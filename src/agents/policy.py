"""Engagement policy for routing and exit conditions."""

from dataclasses import dataclass
from enum import Enum

from config.settings import get_settings


class EngagementMode(str, Enum):
    """Engagement intensity modes."""
    
    NONE = "none"           # Not engaging (monitoring only)
    CAUTIOUS = "cautious"   # Low confidence scam, limited turns
    AGGRESSIVE = "aggressive"  # High confidence scam, full engagement


@dataclass
class EngagementState:
    """Current state of an engagement."""
    
    mode: EngagementMode
    turn_count: int
    duration_seconds: int
    intelligence_complete: bool
    scammer_suspicious: bool
    turns_since_new_info: int


class EngagementPolicy:
    """
    Determines engagement routing and exit conditions.
    
    Routes scams to appropriate engagement intensity based on confidence,
    and determines when to exit an engagement.
    """
    
    def __init__(self) -> None:
        """Initialize with settings."""
        settings = get_settings()
        
        # Confidence thresholds
        self.cautious_threshold = settings.cautious_confidence_threshold  # 0.60
        self.aggressive_threshold = settings.aggressive_confidence_threshold  # 0.85
        
        # Turn limits
        self.max_turns_cautious = settings.max_engagement_turns_cautious  # 10
        self.max_turns_aggressive = settings.max_engagement_turns_aggressive  # 25
        
        # Time limit
        self.max_duration_seconds = settings.max_engagement_duration_seconds  # 600
        
        # Stale detection
        self.stale_turn_threshold = 5  # Exit if no new info in 5 turns
    
    def get_engagement_mode(self, confidence: float) -> EngagementMode:
        """Determine engagement mode based on confidence."""
        if confidence >= self.aggressive_threshold:
            return EngagementMode.AGGRESSIVE
        elif confidence >= self.cautious_threshold:
            return EngagementMode.CAUTIOUS
        return EngagementMode.NONE
    
    def should_continue(self, state: EngagementState) -> bool:
        """Determine if engagement should continue."""
        # Get max turns for current mode
        max_turns = (
            self.max_turns_aggressive 
            if state.mode == EngagementMode.AGGRESSIVE 
            else self.max_turns_cautious
        )
        
        # Check all exit conditions
        if state.turn_count >= max_turns:
            return False
        if state.duration_seconds >= self.max_duration_seconds:
            return False
        if state.intelligence_complete:
            return False
        if state.scammer_suspicious:
            return False
        if state.turns_since_new_info >= self.stale_turn_threshold:
            return False
        
        return True
    
    def get_exit_reason(self, state: EngagementState) -> str | None:
        """Get the reason for exiting engagement, if any."""
        max_turns = (
            self.max_turns_aggressive 
            if state.mode == EngagementMode.AGGRESSIVE 
            else self.max_turns_cautious
        )
        
        if state.turn_count >= max_turns:
            return f"Max turns reached ({max_turns})"
        if state.duration_seconds >= self.max_duration_seconds:
            return f"Max duration exceeded ({self.max_duration_seconds}s)"
        if state.intelligence_complete:
            return "Intelligence extraction complete"
        if state.scammer_suspicious:
            return "Scammer became suspicious"
        if state.turns_since_new_info >= self.stale_turn_threshold:
            return f"No new information in {self.stale_turn_threshold} turns"
        
        return None
