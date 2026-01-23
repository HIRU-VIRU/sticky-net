"""Main honeypot agent implementation using Gemini 3 Pro."""

import os
import random
import time
import uuid
from dataclasses import dataclass

import structlog
from google import genai
from google.genai import types

from config.settings import get_settings
from src.api.schemas import ConversationMessage, Message, Metadata, SenderType
from src.detection.detector import DetectionResult
from src.agents.prompts import (
    HONEYPOT_SYSTEM_PROMPT,
    EXTRACTION_QUESTIONS,
    format_scam_indicators,
)
from src.agents.persona import PersonaManager, Persona
from src.agents.policy import EngagementPolicy, EngagementMode, EngagementState

# Safety settings for Gemini to allow scam roleplay (for honeypot context)
# Using BLOCK_NONE for Gemini 3 Preview models which have stricter default filters
HONEYPOT_SAFETY_SETTINGS = [
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
]

logger = structlog.get_logger()


@dataclass
class EngagementResult:
    """Result of agent engagement."""

    response: str
    duration_seconds: int
    notes: str
    conversation_id: str
    turn_number: int
    engagement_mode: EngagementMode
    should_continue: bool
    exit_reason: str | None = None


class HoneypotAgent:
    """
    AI agent that engages scammers while maintaining a believable human persona.

    Uses Google Gemini 3 Pro with fallback to Gemini 2.5 Pro for sophisticated,
    natural conversation generation.
    """

    def __init__(self) -> None:
        """Initialize the honeypot agent."""
        self.settings = get_settings()
        self.logger = logger.bind(component="HoneypotAgent")
        self.persona_manager = PersonaManager()
        self.policy = EngagementPolicy()
        
        # Set credentials path in environment if configured
        if self.settings.google_application_credentials:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.settings.google_application_credentials
        
        # Initialize Gemini client with Vertex AI credentials from settings
        self.client = genai.Client(
            vertexai=self.settings.google_genai_use_vertexai,
            project=self.settings.google_cloud_project,
            location=self.settings.google_cloud_location,
        )
        
        # Primary model (Gemini 3 Pro) and fallback (Gemini 2.5 Pro)
        self.model = self.settings.pro_model  # gemini-3-pro-preview
        self.fallback_model = self.settings.fallback_pro_model  # gemini-2.5-pro
        self._last_model_used: str | None = None  # Track which model was used

    async def engage(
        self,
        message: Message,
        history: list[ConversationMessage],
        metadata: Metadata,
        detection: DetectionResult,
        conversation_id: str | None = None,
    ) -> EngagementResult:
        """
        Engage with the scammer and generate a response.

        Args:
            message: The current scammer message
            history: Previous conversation messages
            metadata: Message metadata
            detection: Scam detection result
            conversation_id: Optional existing conversation ID

        Returns:
            EngagementResult with the agent's response
        """
        start_time = time.time()

        # Generate or use existing conversation ID
        conv_id = conversation_id or str(uuid.uuid4())

        self.logger.info(
            "Engaging with scammer",
            conversation_id=conv_id,
            history_length=len(history),
            confidence=detection.confidence,
        )

        # Determine engagement mode
        engagement_mode = self.policy.get_engagement_mode(detection.confidence)

        # Get/update persona state
        persona = self.persona_manager.update_persona(
            conv_id,
            scam_intensity=detection.confidence,
        )

        # Build conversation prompt for Gemini
        prompt = self._build_prompt(
            message=message,
            history=history,
            detection=detection,
            persona=persona,
        )

        # Generate response using Gemini 3 Pro
        try:
            response = await self._generate_response(prompt, persona)
        except Exception as e:
            self.logger.error("Failed to generate response", error=str(e))
            response = self._get_fallback_response(detection)

        # Calculate duration
        duration = int(time.time() - start_time)

        # Check if engagement should continue
        state = EngagementState(
            mode=engagement_mode,
            turn_count=persona.engagement_turn,
            duration_seconds=duration,
            intelligence_complete=False,  # Set by intelligence extractor
            scammer_suspicious=False,  # Detect from response patterns
            turns_since_new_info=0,  # Track over time
        )
        should_continue = self.policy.should_continue(state)
        exit_reason = self.policy.get_exit_reason(state) if not should_continue else None

        # Generate notes
        notes = self._generate_notes(detection, persona, engagement_mode)

        return EngagementResult(
            response=response,
            duration_seconds=duration,
            notes=notes,
            conversation_id=conv_id,
            turn_number=persona.engagement_turn,
            engagement_mode=engagement_mode,
            should_continue=should_continue,
            exit_reason=exit_reason,
        )

    def _build_prompt(
        self,
        message: Message,
        history: list[ConversationMessage],
        detection: DetectionResult,
        persona: Persona,
    ) -> str:
        """Build conversation prompt for Gemini."""
        # Format scam indicators
        scam_indicators = [m.description for m in detection.matched_patterns[:5]]
        indicators_text = format_scam_indicators(scam_indicators) if scam_indicators else "General suspicious behavior"

        # Format conversation history
        history_text = ""
        for msg in history[-10:]:  # Last 10 messages for context
            sender = "SCAMMER" if msg.sender == SenderType.SCAMMER else "YOU"
            history_text += f"[{sender}]: {msg.text}\n"

        prompt = f"""CONVERSATION HISTORY:
{history_text if history_text else "No previous messages"}

SCAMMER'S NEW MESSAGE:
"{message.text}"

YOUR TASK:
Generate a response as the naive, trusting victim. Your emotional state is: {persona.emotional_state.value}
This is turn {persona.engagement_turn} of the conversation.

Remember:
- Stay in character as a confused, worried person
- Ask questions that extract intelligence (bank accounts, UPI IDs, links)
- Keep responses short (1-3 sentences)
- Show willingness to comply but need guidance

DETECTED SCAM INDICATORS: {indicators_text}

Generate your response:"""

        return prompt

    async def _generate_response(
        self,
        prompt: str,
        persona: Persona,
    ) -> str:
        """Generate response using Gemini Pro with fallback to Gemini 2.5."""
        # Format system instruction with persona context
        system_instruction = HONEYPOT_SYSTEM_PROMPT.format(
            emotional_state=persona.emotional_state.value,
            turn_number=persona.engagement_turn,
            scam_indicators="See conversation context",
        )
        
        # Try primary model (Gemini 3 Pro) first, then fallback (Gemini 2.5 Pro)
        models_to_try = [self.model, self.fallback_model]
        response_text = None
        
        for model_name in models_to_try:
            try:
                self.logger.debug(f"Trying model: {model_name}")
                
                # Gemini 3 Pro needs higher max_output_tokens because its
                # internal "thinking" consumes output tokens. 256 is too small
                # and causes MAX_TOKENS finish reason with empty text.
                if "gemini-3" in model_name:
                    max_tokens = 2048  # Gemini 3 needs more for thinking
                    thinking_config = types.ThinkingConfig(
                        thinking_level=types.ThinkingLevel.HIGH
                    )
                else:
                    max_tokens = 512   # Gemini 2.5 is more efficient
                    thinking_config = None
                
                # Build config with model-specific settings
                config = types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    thinking_config=thinking_config,
                    temperature=self.settings.llm_temperature,
                    max_output_tokens=max_tokens,
                    safety_settings=HONEYPOT_SAFETY_SETTINGS,
                )
                
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config,
                )
                
                response_text = response.text
                
                # Check if we got a valid response
                if response_text and len(response_text.strip()) > 0:
                    self._last_model_used = model_name
                    self.logger.info(
                        "Response generated successfully",
                        model=model_name,
                        response_length=len(response_text)
                    )
                    break
                else:
                    self.logger.warning(
                        "Empty response from model, trying fallback",
                        model=model_name
                    )
                    
            except Exception as e:
                self.logger.warning(
                    "Model failed, trying fallback",
                    model=model_name,
                    error=str(e)
                )
                continue
        
        # Handle None response - use fallback response
        if not response_text:
            self._last_model_used = "fallback"
            return self._get_fallback_response(None)

        # Add emotional modifier if appropriate
        if persona.engagement_turn > 0:
            modifier = persona.get_emotional_modifier()
            if modifier and not response_text.startswith(modifier):
                response_text = modifier + response_text

        # Potentially add extraction question
        if persona.should_ask_extraction_question():
            question = random.choice(EXTRACTION_QUESTIONS)
            if not any(q in response_text.lower() for q in ["account", "upi", "link", "number"]):
                response_text = response_text.rstrip(".")
                response_text += f" {question}"
                persona.record_extraction()

        return response_text

    def _get_fallback_response(self, detection: DetectionResult) -> str:
        """Get a fallback response if LLM fails."""
        fallback_responses = [
            "I'm sorry, I'm a bit confused. Can you explain that again?",
            "My phone is acting up. What do I need to do exactly?",
            "I didn't understand. Can you tell me step by step?",
            "Okay, but what should I do first? I'm worried.",
        ]
        return random.choice(fallback_responses)

    def _generate_notes(
        self, 
        detection: DetectionResult, 
        persona: Persona,
        mode: EngagementMode,
    ) -> str:
        """Generate agent notes summarizing the engagement."""
        notes_parts = []

        # Engagement mode
        notes_parts.append(f"Mode: {mode.value}")

        # Scam tactics detected
        categories_used = list(set(m.category.value for m in detection.matched_patterns))
        if categories_used:
            notes_parts.append(f"Tactics: {', '.join(categories_used)}")

        # Confidence
        notes_parts.append(f"Confidence: {detection.confidence:.0%}")

        # Engagement progress
        notes_parts.append(f"Turn: {persona.engagement_turn}")

        # Emotional state
        notes_parts.append(f"Persona: {persona.emotional_state.value}")

        return " | ".join(notes_parts)

    def end_conversation(self, conversation_id: str) -> None:
        """Clean up persona when conversation ends."""
        self.persona_manager.clear_persona(conversation_id)


# Singleton instance for reuse
_agent_instance: HoneypotAgent | None = None


def get_agent() -> HoneypotAgent:
    """Get or create the honeypot agent instance."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = HoneypotAgent()
    return _agent_instance
