from pydantic import BaseModel, Field
from typing import List, Optional

class StrategyJSON(BaseModel):
    objective: str = Field(description="The overarching goal (e.g., 'resolve_conflict')")
    current_state: str = Field(description="Brief description of current emotional state")
    desired_next_state: str = Field(description="The emotional state to shift to next")
    approach: str = Field(description="The tactical approach (e.g., 'de_escalation')")
    tone: str = Field(description="The tone of the message (e.g., 'casual', 'empathetic')")
    directness: float = Field(ge=0, le=1, description="Directness from 0 to 1")
    intensity: float = Field(ge=0, le=1, description="Intensity from 0 to 1")
    avoid: List[str] = Field(description="Topics or phrasing to explicitly avoid")

class CriticResultJSON(BaseModel):
    passed: bool = Field(description="Whether the draft passed critique")
    scores: dict[str, int] = Field(description="Scores out of 10 for relevance, consistency, tone, directness")
    issues: List[str] = Field(description="Specific issues found with the draft, if any")
    revision_instructions: List[str] = Field(description="Instructions for the generator to fix the draft")

class DraftCandidate(BaseModel):
    content: str
    strategy: StrategyJSON
    critic_feedback: Optional[CriticResultJSON] = None
    iteration: int = 1
