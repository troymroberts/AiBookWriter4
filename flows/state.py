"""
BookState - Pydantic model for tracking state across the book generation process.

This model is used by BookWriterFlow to maintain state between phases and enable
features like review gates, convergence detection, and checkpoint/resume.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum


class WorkflowPhase(str, Enum):
    """Current phase of book generation workflow"""
    FOUNDATION = "foundation"
    WORLD_BUILDING = "world_building"
    STRUCTURE = "structure"
    WRITING = "writing"
    EDITORIAL = "editorial"
    FINAL_REVIEW = "final_review"
    COMPLETE = "complete"


class ReviewGateStatus(str, Enum):
    """Status of review gates"""
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ChapterStatus(str, Enum):
    """Status of individual chapters"""
    NOT_STARTED = "not_started"
    OUTLINING = "outlining"
    WRITING = "writing"
    EDITORIAL = "editorial"
    COMPLETE = "complete"


class CharacterProfile(BaseModel):
    """Character data stored in state"""
    name: str
    role: str = ""  # protagonist, antagonist, supporting, minor
    description: str = ""
    backstory: str = ""
    voice_profile: str = ""  # Writing style description
    relationships: Dict[str, str] = Field(default_factory=dict)
    arc: str = ""
    first_appearance: Optional[int] = None  # Chapter number


class LocationProfile(BaseModel):
    """Location data stored in state"""
    name: str
    description: str = ""
    sensory_details: Dict[str, str] = Field(default_factory=dict)  # sight, sound, smell, etc.
    significance: str = ""
    first_appearance: Optional[int] = None


class LoreEntry(BaseModel):
    """Lore/world-building entry"""
    fact_id: str
    content: str
    category: str = ""  # history, magic, culture, technology, etc.
    established_in: Optional[str] = None  # scene_id
    version: str = "main"
    supersedes: Optional[str] = None  # Previous fact_id if retconned


class SceneOutline(BaseModel):
    """Scene-level outline data"""
    scene_id: str
    chapter: int
    scene_number: int
    pov_character: str = ""
    location: str = ""
    characters_present: List[str] = Field(default_factory=list)
    time_of_day: str = ""
    emotional_beat: str = ""
    summary: str = ""
    word_target: int = 1500


class ChapterData(BaseModel):
    """Chapter-level data"""
    chapter_number: int
    title: str = ""
    scenes: List[SceneOutline] = Field(default_factory=list)
    content: str = ""  # Final prose
    status: ChapterStatus = ChapterStatus.NOT_STARTED
    word_count: int = 0
    editorial_iterations: int = 0
    convergence_score: float = 1.0


class BookState(BaseModel):
    """
    Complete state for book generation workflow.

    This model tracks everything needed to:
    - Resume from any checkpoint
    - Enable review gates
    - Detect editorial convergence
    - Maintain canon consistency
    """

    # === Project Configuration ===
    project_name: str = "Untitled Novel"
    genre: str = "literary_fiction"
    premise: str = ""
    target_chapters: int = 25
    target_words_per_chapter: int = 3000
    project_type: str = "STANDARD"  # STANDARD, LIGHT_NOVEL, LITERARY, FANTASY, EPIC_FANTASY

    # === LLM Configuration ===
    llm_base_url: Optional[str] = "http://localhost:11434"  # None for cloud providers like OpenRouter
    llm_model: str = "ollama/llama3.2"

    # === Phase Tracking ===
    current_phase: WorkflowPhase = WorkflowPhase.FOUNDATION
    current_chapter: int = 0
    chapters_completed: int = 0

    # === Foundation Phase Outputs ===
    story_arc: str = ""
    themes: List[str] = Field(default_factory=list)
    tone: str = ""
    narrative_style: str = "third_person"

    # === World Building Outputs ===
    characters: List[CharacterProfile] = Field(default_factory=list)
    locations: List[LocationProfile] = Field(default_factory=list)
    lore: List[LoreEntry] = Field(default_factory=list)

    # === Structure Phase Outputs ===
    plot_outline: str = ""
    chapter_outlines: List[str] = Field(default_factory=list)
    timeline: List[Dict[str, Any]] = Field(default_factory=list)

    # === Writing Phase Data ===
    chapters: List[ChapterData] = Field(default_factory=list)

    # === Editorial Metrics ===
    total_editorial_iterations: int = 0
    max_editorial_iterations: int = 5
    convergence_threshold: float = 0.05  # < 5% changes = converged

    # === Review Gates ===
    review_gates_enabled: bool = True
    review_gate_phases: List[str] = Field(
        default_factory=lambda: ["structure", "chapter"]
    )
    current_review_status: ReviewGateStatus = ReviewGateStatus.NOT_REQUIRED
    user_feedback: str = ""

    # === Progress Tracking ===
    started_at: Optional[str] = None
    last_updated: Optional[str] = None
    total_words_written: int = 0

    # === Error Handling ===
    last_error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 10

    def get_progress_percentage(self) -> float:
        """Calculate overall progress as percentage"""
        phase_weights = {
            WorkflowPhase.FOUNDATION: 0.05,
            WorkflowPhase.WORLD_BUILDING: 0.15,
            WorkflowPhase.STRUCTURE: 0.10,
            WorkflowPhase.WRITING: 0.60,
            WorkflowPhase.EDITORIAL: 0.05,
            WorkflowPhase.FINAL_REVIEW: 0.05,
            WorkflowPhase.COMPLETE: 1.0
        }

        if self.current_phase == WorkflowPhase.COMPLETE:
            return 100.0

        # Calculate base progress from completed phases
        base_progress = 0.0
        phases = list(WorkflowPhase)
        current_idx = phases.index(self.current_phase)

        for i, phase in enumerate(phases):
            if i < current_idx:
                base_progress += phase_weights.get(phase, 0)

        # Add progress within writing phase
        if self.current_phase == WorkflowPhase.WRITING and self.target_chapters > 0:
            writing_progress = self.chapters_completed / self.target_chapters
            base_progress += phase_weights[WorkflowPhase.WRITING] * writing_progress

        return round(base_progress * 100, 1)

    def get_character_by_name(self, name: str) -> Optional[CharacterProfile]:
        """Find character by name (case-insensitive)"""
        for char in self.characters:
            if char.name.lower() == name.lower():
                return char
        return None

    def get_location_by_name(self, name: str) -> Optional[LocationProfile]:
        """Find location by name (case-insensitive)"""
        for loc in self.locations:
            if loc.name.lower() == name.lower():
                return loc
        return None

    def add_lore_entry(self, content: str, category: str, scene_id: str = None) -> LoreEntry:
        """Add a new lore entry with auto-generated ID"""
        entry = LoreEntry(
            fact_id=f"lore_{len(self.lore) + 1}",
            content=content,
            category=category,
            established_in=scene_id
        )
        self.lore.append(entry)
        return entry

    def should_trigger_review_gate(self) -> bool:
        """Check if current state should trigger a review gate"""
        if not self.review_gates_enabled:
            return False

        phase_name = self.current_phase.value

        # Check phase-based gates
        if phase_name in self.review_gate_phases:
            return True

        # Check chapter-based gates
        if "chapter" in self.review_gate_phases and self.current_phase == WorkflowPhase.WRITING:
            # Could add logic for every N chapters, etc.
            return True

        return False
