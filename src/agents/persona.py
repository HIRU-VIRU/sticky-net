"""Human persona management for the honeypot agent."""

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PersonaTrait(str, Enum):
    """Persona personality traits."""

    TRUSTING = "trusting"
    WORRIED = "worried"
    CONFUSED = "confused"
    COOPERATIVE = "cooperative"
    TECH_NAIVE = "tech_naive"


class EmotionalState(str, Enum):
    """Current emotional state of the persona."""

    CALM = "calm"
    ANXIOUS = "anxious"
    PANICKED = "panicked"
    RELIEVED = "relieved"
    SUSPICIOUS = "suspicious"  # Use sparingly, only late in conversation


@dataclass
class Persona:
    """Represents the honeypot's human persona."""

    traits: list[PersonaTrait] = field(default_factory=lambda: [
        PersonaTrait.TRUSTING,
        PersonaTrait.WORRIED,
        PersonaTrait.TECH_NAIVE,
    ])
    emotional_state: EmotionalState = EmotionalState.CALM
    engagement_turn: int = 0
    extracted_info_count: int = 0

    # Conversation memory
    claimed_issues: list[str] = field(default_factory=list)
    mentioned_details: dict[str, Any] = field(default_factory=dict)

    def update_emotional_state(self, scam_intensity: float) -> None:
        """Update emotional state based on scam intensity."""
        if scam_intensity > 0.8:
            self.emotional_state = EmotionalState.PANICKED
        elif scam_intensity > 0.5:
            self.emotional_state = EmotionalState.ANXIOUS
        else:
            self.emotional_state = EmotionalState.CALM

    def get_emotional_modifier(self) -> str:
        """Get text modifier based on emotional state."""
        modifiers = {
            EmotionalState.CALM: "",
            EmotionalState.ANXIOUS: "I'm getting worried... ",
            EmotionalState.PANICKED: "Oh god, please help! ",
            EmotionalState.RELIEVED: "Thank goodness... ",
            EmotionalState.SUSPICIOUS: "Hmm, ",
        }
        return modifiers.get(self.emotional_state, "")

    def should_ask_extraction_question(self) -> bool:
        """Determine if it's a good time to ask for intelligence."""
        # More likely to ask after building rapport (turn 2+)
        # Less likely if we've already extracted a lot
        base_probability = 0.4
        turn_bonus = min(0.3, self.engagement_turn * 0.1)
        extraction_penalty = self.extracted_info_count * 0.15

        probability = base_probability + turn_bonus - extraction_penalty
        return random.random() < probability

    def record_extraction(self) -> None:
        """Record that we extracted some intelligence."""
        self.extracted_info_count += 1

    def increment_turn(self) -> None:
        """Increment the engagement turn counter."""
        self.engagement_turn += 1


class PersonaManager:
    """Manages persona state across conversation turns."""

    def __init__(self) -> None:
        """Initialize persona manager."""
        self.personas: dict[str, Persona] = {}

    def get_or_create_persona(self, conversation_id: str) -> Persona:
        """Get existing persona or create new one for a conversation."""
        if conversation_id not in self.personas:
            self.personas[conversation_id] = Persona()
        return self.personas[conversation_id]

    def update_persona(
        self,
        conversation_id: str,
        scam_intensity: float,
        extracted_something: bool = False,
    ) -> Persona:
        """Update persona state after a turn."""
        persona = self.get_or_create_persona(conversation_id)
        persona.increment_turn()
        persona.update_emotional_state(scam_intensity)
        if extracted_something:
            persona.record_extraction()
        return persona

    def get_persona_context(self, conversation_id: str) -> dict[str, Any]:
        """Get persona context for prompt injection."""
        persona = self.get_or_create_persona(conversation_id)
        return {
            "emotional_state": persona.emotional_state.value,
            "engagement_turn": persona.engagement_turn,
            "emotional_modifier": persona.get_emotional_modifier(),
            "should_extract": persona.should_ask_extraction_question(),
        }

    def clear_persona(self, conversation_id: str) -> None:
        """Clear persona for a completed conversation."""
        self.personas.pop(conversation_id, None)
