"""
BookWriterFlow - Main orchestrator for book generation using CrewAI Flows.

This implements the Supervisor pattern from SPEC.md using CrewAI's Flow architecture
with @start, @listen, and @router decorators for state-based workflow control.

Features:
- Phase-based workflow (Foundation → World Building → Structure → Writing → Editorial)
- Editorial loop with convergence detection
- HITL (Human-in-the-loop) review gates
- Streaming support for real-time UI updates
- Memory/RAG integration via CrewAI
"""

import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
import difflib

import litellm
from crewai.flow.flow import Flow, start, listen, router, or_
from crewai import Agent, Crew, Task, Process, LLM

# Note: IPv4 fix is applied in flows/__init__.py via ipv4_fix module

from .state import (
    BookState,
    WorkflowPhase,
    ReviewGateStatus,
    ChapterData,
    ChapterStatus,
    CharacterProfile,
    LocationProfile,
    SceneOutline
)


class BookWriterFlow(Flow[BookState]):
    """
    Main flow orchestrator for novel generation.

    Workflow:
    1. Foundation Phase: Story arc, themes, tone
    2. World Building Phase: Characters, locations, lore (parallel)
    3. Structure Phase: Plot outline, chapter breakdown, timeline
    4. Writing Phase: Scene-by-scene generation with editorial loop
    5. Final Review: Manuscript consistency check

    Each phase can have review gates for user approval.

    Usage:
        flow = BookWriterFlow()
        result = flow.kickoff(inputs={
            'project_name': 'My Novel',
            'genre': 'fantasy_scifi',
            'premise': 'A young mage discovers...',
            'target_chapters': 10,
            ...
        })
    """

    # Enable streaming for real-time UI updates
    stream = True

    def __init__(self, initial_state: BookState = None, **kwargs):
        super().__init__(**kwargs)
        self._llm = None
        self._agents_cache = {}
        self._initial_state = initial_state

        # Warmup httpx client for cloud providers (fixes connection issues)
        if initial_state and initial_state.llm_model.startswith("openrouter/"):
            self._warmup_http_client(initial_state.llm_model)

    def _warmup_http_client(self, model: str):
        """
        Initialize httpx client with correct network settings.

        This makes a minimal LiteLLM call to ensure the httpx client is
        created after our IPv4 fix is applied. Without this warmup,
        CrewAI might initialize httpx before the fix takes effect.
        """
        import os
        if not os.environ.get("OPENROUTER_API_KEY"):
            return  # Skip if no API key set

        try:
            litellm.completion(
                model=model,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=1,
            )
        except Exception:
            pass  # Ignore errors, this is just a warmup

    def _get_llm(self) -> LLM:
        """Get or create LLM instance"""
        if self._llm is None:
            # Calculate tokens needed for target chapter length
            # Rough estimate: 1 token ≈ 0.75 words, so 4000 words ≈ 5333 tokens
            # Add buffer for prompt + response
            target_tokens = max(8000, self.state.target_words_per_chapter * 2)

            # Configure provider-specific parameters
            if self.state.llm_model.startswith("ollama/"):
                # Ollama: set num_predict and context window via LiteLLM config
                litellm.OllamaConfig(
                    num_predict=target_tokens,
                    num_ctx=40000,  # Model supports 40k context
                )
            elif self.state.llm_model.startswith("openrouter/"):
                # OpenRouter: higher token limits available (MiMo-V2 supports 65K output)
                target_tokens = max(16000, self.state.target_words_per_chapter * 3)

            # Build LLM kwargs (only include base_url if set)
            llm_kwargs = {
                "model": self.state.llm_model,
                "temperature": 0.7,
                "max_tokens": target_tokens,
                "num_retries": 3,  # Retry on transient failures
                "timeout": 120.0,  # 2 minute timeout per request
            }
            if self.state.llm_base_url:
                llm_kwargs["base_url"] = self.state.llm_base_url

            self._llm = LLM(**llm_kwargs)
        return self._llm

    def _should_use_memory(self) -> bool:
        """
        Determine if CrewAI memory should be enabled.

        Memory/RAG requires embeddings. By default CrewAI uses OpenAI embeddings,
        which requires OPENAI_API_KEY. For cloud providers like OpenRouter that
        don't provide embeddings, we disable memory to avoid errors.

        Returns:
            True if memory should be enabled, False otherwise
        """
        # Local providers (Ollama) can use local embeddings
        if self.state.llm_model.startswith("ollama/"):
            return True

        # Cloud providers without embedding support
        if self.state.llm_model.startswith("openrouter/"):
            return False

        # Default: disable to be safe
        return False

    def _get_agent(self, agent_type: str) -> Agent:
        """Get or create agent by type (cached)"""
        if agent_type not in self._agents_cache:
            # Import from agents_extended
            from agents_extended import ALL_AGENTS
            if agent_type in ALL_AGENTS:
                creator_func = ALL_AGENTS[agent_type]
                self._agents_cache[agent_type] = creator_func(
                    llm=self._get_llm(),
                    genre_config=self._load_genre_config()
                )
            else:
                raise ValueError(f"Unknown agent type: {agent_type}")
        return self._agents_cache[agent_type]

    def _load_genre_config(self) -> Dict[str, Any]:
        """Load genre configuration"""
        try:
            from agents import load_genre_config
            return load_genre_config(self.state.genre)
        except Exception:
            return {}

    # =========================================================================
    # PHASE 1: FOUNDATION
    # =========================================================================

    @start()
    def foundation_phase(self):
        """
        Foundation Phase: Create story arc, themes, and overall direction.

        Input: premise, genre, target_chapters
        Output: story_arc, themes, tone, narrative_style
        """
        # Copy initial state values if provided
        if self._initial_state:
            for field in self._initial_state.model_fields:
                if hasattr(self._initial_state, field):
                    value = getattr(self._initial_state, field)
                    if value is not None and value != getattr(BookState(), field, None):
                        setattr(self.state, field, value)

        self.state.current_phase = WorkflowPhase.FOUNDATION
        self.state.started_at = datetime.now().isoformat()
        self.state.last_updated = datetime.now().isoformat()

        # Create story architect agent and task
        story_architect = self._get_agent("story_architect")

        story_task = Task(
            description=f"""
            Create a comprehensive story arc for a {self.state.genre} novel.

            PREMISE: {self.state.premise}

            TARGET LENGTH: {self.state.target_chapters} chapters

            Create:
            1. A compelling overall story arc with beginning, middle, and end
            2. Core themes to explore throughout the narrative
            3. The emotional tone and atmosphere
            4. Recommended narrative style (POV, tense)

            Be detailed and specific. This will guide all subsequent writing.
            """,
            expected_output="""
            A structured story foundation including:
            - Complete story arc outline
            - List of 3-5 core themes
            - Tone description
            - Narrative style recommendation
            """,
            agent=story_architect
        )

        # Create and run foundation crew
        foundation_crew = Crew(
            agents=[story_architect],
            tasks=[story_task],
            process=Process.sequential,
            memory=self._should_use_memory(),
            verbose=True
        )

        result = foundation_crew.kickoff()

        # Parse and store results
        self.state.story_arc = result.raw
        self.state.last_updated = datetime.now().isoformat()

        return {
            "phase": "foundation",
            "story_arc": self.state.story_arc,
            "status": "complete"
        }

    # =========================================================================
    # PHASE 2: WORLD BUILDING
    # =========================================================================

    @listen(foundation_phase)
    def world_building_phase(self, foundation_result):
        """
        World Building Phase: Create characters, locations, and lore.

        These can run in parallel for efficiency.
        """
        self.state.current_phase = WorkflowPhase.WORLD_BUILDING
        self.state.last_updated = datetime.now().isoformat()

        # Get agents
        character_designer = self._get_agent("character_designer")
        location_designer = self._get_agent("location_designer")

        # Character creation task
        character_task = Task(
            description=f"""
            Create detailed character profiles for a {self.state.genre} novel.

            STORY ARC:
            {self.state.story_arc}

            Create profiles for:
            - Protagonist(s)
            - Antagonist(s)
            - Key supporting characters

            For each character include:
            - Name and role
            - Physical description
            - Personality and voice (how they speak)
            - Backstory
            - Character arc
            - Key relationships
            """,
            expected_output="Detailed character profiles with voice guides",
            agent=character_designer
        )

        # Location creation task
        location_task = Task(
            description=f"""
            Create detailed location profiles for a {self.state.genre} novel.

            STORY ARC:
            {self.state.story_arc}

            For each significant location include:
            - Name and type
            - Visual description
            - Sensory details (sounds, smells, textures)
            - Atmosphere and mood
            - Narrative significance
            """,
            expected_output="Detailed location profiles with sensory details",
            agent=location_designer
        )

        # Run crews (could be parallel with asyncio)
        character_crew = Crew(
            agents=[character_designer],
            tasks=[character_task],
            process=Process.sequential,
            memory=self._should_use_memory(),
            verbose=True
        )

        location_crew = Crew(
            agents=[location_designer],
            tasks=[location_task],
            process=Process.sequential,
            memory=self._should_use_memory(),
            verbose=True
        )

        # Sequential for now (can parallelize with asyncio)
        char_result = character_crew.kickoff()
        loc_result = location_crew.kickoff()

        # Store results (parsing would happen here in production)
        self.state.last_updated = datetime.now().isoformat()

        return {
            "phase": "world_building",
            "characters": char_result.raw,
            "locations": loc_result.raw,
            "status": "complete"
        }

    # =========================================================================
    # PHASE 3: STRUCTURE
    # =========================================================================

    @listen(world_building_phase)
    def structure_phase(self, world_result):
        """
        Structure Phase: Create plot outline, chapter breakdown, and timeline.
        """
        self.state.current_phase = WorkflowPhase.STRUCTURE
        self.state.last_updated = datetime.now().isoformat()

        plot_architect = self._get_agent("plot_architect")

        structure_task = Task(
            description=f"""
            Create a detailed plot structure for a {self.state.target_chapters}-chapter
            {self.state.genre} novel.

            STORY ARC:
            {self.state.story_arc}

            CHARACTERS:
            {world_result.get('characters', 'See above')}

            LOCATIONS:
            {world_result.get('locations', 'See above')}

            Create:
            1. Overall plot outline with major beats
            2. Chapter-by-chapter breakdown with:
               - Chapter title/number
               - Key scenes
               - POV character
               - Main conflict/tension
               - Word count target
            3. Timeline of events
            """,
            expected_output="""
            Complete plot structure including:
            - Plot outline with story beats
            - Chapter breakdown for all {num} chapters
            - Chronological timeline
            """.format(num=self.state.target_chapters),
            agent=plot_architect
        )

        structure_crew = Crew(
            agents=[plot_architect],
            tasks=[structure_task],
            process=Process.sequential,
            memory=self._should_use_memory(),
            verbose=True
        )

        result = structure_crew.kickoff()

        self.state.plot_outline = result.raw
        self.state.last_updated = datetime.now().isoformat()

        return {
            "phase": "structure",
            "plot_outline": self.state.plot_outline,
            "status": "complete"
        }

    # =========================================================================
    # REVIEW GATE ROUTER
    # =========================================================================

    @router(structure_phase)
    def check_structure_review(self):
        """Router: Check if structure needs user approval before writing"""
        if self.state.should_trigger_review_gate():
            self.state.current_review_status = ReviewGateStatus.PENDING
            return "await_review"
        return "begin_writing"

    @listen("await_review")
    def await_user_review(self):
        """
        Pause for user review (HITL).

        In Streamlit, this triggers a review UI.
        In API mode, this could trigger a webhook.
        """
        self.state.last_updated = datetime.now().isoformat()

        return {
            "phase": "review_gate",
            "status": "awaiting_approval",
            "content_to_review": {
                "story_arc": self.state.story_arc,
                "plot_outline": self.state.plot_outline
            },
            "message": "Awaiting user approval before proceeding to writing phase."
        }

    def resume_after_review(self, approved: bool, feedback: str = ""):
        """
        Resume workflow after user review.

        Call this method from the UI when user approves/rejects.
        """
        self.state.user_feedback = feedback
        self.state.last_updated = datetime.now().isoformat()

        if approved:
            self.state.current_review_status = ReviewGateStatus.APPROVED
            return self.writing_phase()
        else:
            self.state.current_review_status = ReviewGateStatus.REJECTED
            # Re-run structure phase with feedback
            return self.structure_phase({
                "feedback": feedback,
                "revision_requested": True
            })

    # =========================================================================
    # PHASE 4: WRITING
    # =========================================================================

    @listen("begin_writing")
    def writing_phase(self):
        """
        Writing Phase: Generate chapters with editorial loop.

        For each chapter:
        1. Generate initial draft
        2. Editorial loop until convergence
        3. Move to next chapter
        """
        self.state.current_phase = WorkflowPhase.WRITING
        self.state.last_updated = datetime.now().isoformat()

        # Initialize chapter data if not exists
        if not self.state.chapters:
            self.state.chapters = [
                ChapterData(chapter_number=i + 1)
                for i in range(self.state.target_chapters)
            ]

        # Find next chapter to write
        for chapter in self.state.chapters:
            if chapter.status == ChapterStatus.NOT_STARTED:
                self.state.current_chapter = chapter.chapter_number
                return self._write_chapter(chapter)

        # All chapters complete
        return self.final_review_phase()

    def _write_chapter(self, chapter: ChapterData):
        """Write a single chapter with editorial loop"""
        chapter.status = ChapterStatus.WRITING

        scene_writer = self._get_agent("scene_writer")

        writing_task = Task(
            description=f"""
            Write Chapter {chapter.chapter_number} of the novel.

            STORY ARC:
            {self.state.story_arc}

            PLOT OUTLINE:
            {self.state.plot_outline}

            CRITICAL REQUIREMENT - WORD COUNT:
            You MUST write AT LEAST {self.state.target_words_per_chapter} words for this chapter.
            This is a MINIMUM requirement. Do not stop writing until you have reached this target.
            Count your words as you write. A typical page is ~250 words.
            {self.state.target_words_per_chapter} words = approximately {self.state.target_words_per_chapter // 250} pages.

            Write engaging, publication-quality prose that:
            - Advances the plot according to the outline
            - Maintains character voice consistency
            - Uses vivid sensory details and rich descriptions
            - Shows rather than tells through action and dialogue
            - Includes multiple scenes with smooth transitions
            - Develops subplots and character relationships
            - Ends with forward momentum

            DO NOT summarize. DO NOT abbreviate. Write the FULL chapter with all scenes fully developed.
            """,
            expected_output=f"A complete, fully-written chapter of AT LEAST {self.state.target_words_per_chapter} words. Not an outline, not a summary - full prose narrative.",
            agent=scene_writer
        )

        writing_crew = Crew(
            agents=[scene_writer],
            tasks=[writing_task],
            process=Process.sequential,
            memory=self._should_use_memory(),
            verbose=True
        )

        result = writing_crew.kickoff()

        # Clean up agent output artifacts
        content = result.raw
        # Remove CrewAI internal prompts that may leak through
        cleanup_patterns = [
            "Thought: I now can give a great answer",
            "Your final answer must be the great and the most complete as possible, it must be outcome described.",
            "Final Answer:",
        ]
        for pattern in cleanup_patterns:
            content = content.replace(pattern, "").strip()

        chapter.content = content
        chapter.word_count = len(content.split())
        chapter.status = ChapterStatus.EDITORIAL

        self.state.last_updated = datetime.now().isoformat()

        return {
            "phase": "writing",
            "chapter": chapter.chapter_number,
            "content": chapter.content,
            "word_count": chapter.word_count,
            "status": "draft_complete"
        }

    # =========================================================================
    # EDITORIAL LOOP
    # =========================================================================

    @router(writing_phase)
    def check_editorial_needed(self):
        """Router: Determine if editorial loop is needed"""
        current_chapter = self.state.chapters[self.state.current_chapter - 1]

        if current_chapter.status == ChapterStatus.EDITORIAL:
            return "editorial_loop"

        return "next_chapter"

    @listen("editorial_loop")
    def editorial_refinement(self):
        """
        Editorial Loop: Critic → Reviser → Continuity check.

        Continues until convergence (< 5% changes) or max iterations.
        """
        self.state.current_phase = WorkflowPhase.EDITORIAL
        chapter = self.state.chapters[self.state.current_chapter - 1]

        previous_content = chapter.content

        # Get editorial agents
        continuity_editor = self._get_agent("continuity_editor")
        style_editor = self._get_agent("style_editor")

        # Critique task
        critique_task = Task(
            description=f"""
            Review Chapter {chapter.chapter_number} for quality and consistency.

            CHAPTER CONTENT:
            {chapter.content}

            STORY ARC:
            {self.state.story_arc}

            Provide holistic feedback on:
            - Pacing and tension
            - Character voice consistency
            - Plot coherence
            - Prose quality
            - Areas for improvement

            Focus on big-picture issues, not line edits.
            """,
            expected_output="Constructive critique with specific improvement suggestions",
            agent=continuity_editor
        )

        # Revision task
        revision_task = Task(
            description=f"""
            Revise Chapter {chapter.chapter_number} based on editorial feedback.

            ORIGINAL CHAPTER:
            {chapter.content}

            Implement the suggested improvements while:
            - Maintaining the author's voice
            - Preserving plot points
            - Keeping the target word count
            """,
            expected_output="Revised chapter incorporating feedback",
            agent=style_editor,
            context=[critique_task]
        )

        editorial_crew = Crew(
            agents=[continuity_editor, style_editor],
            tasks=[critique_task, revision_task],
            process=Process.sequential,
            memory=self._should_use_memory(),
            verbose=True
        )

        result = editorial_crew.kickoff()

        # Update chapter (with cleanup)
        content = result.raw
        cleanup_patterns = [
            "Thought: I now can give a great answer",
            "Your final answer must be the great and the most complete as possible, it must be outcome described.",
            "Final Answer:",
        ]
        for pattern in cleanup_patterns:
            content = content.replace(pattern, "").strip()
        chapter.content = content
        chapter.editorial_iterations += 1
        self.state.total_editorial_iterations += 1

        # Calculate convergence
        chapter.convergence_score = self._calculate_convergence(
            previous_content,
            chapter.content
        )

        self.state.last_updated = datetime.now().isoformat()

        return {
            "phase": "editorial",
            "chapter": chapter.chapter_number,
            "iteration": chapter.editorial_iterations,
            "convergence_score": chapter.convergence_score,
            "status": "revision_complete"
        }

    @router(editorial_refinement)
    def check_convergence(self):
        """Router: Check if chapter has converged or needs more iterations"""
        chapter = self.state.chapters[self.state.current_chapter - 1]

        # Converged if changes < threshold
        if chapter.convergence_score < self.state.convergence_threshold:
            chapter.status = ChapterStatus.COMPLETE
            self.state.chapters_completed += 1
            self.state.total_words_written += chapter.word_count
            return "next_chapter"

        # Max iterations reached
        if chapter.editorial_iterations >= self.state.max_editorial_iterations:
            chapter.status = ChapterStatus.COMPLETE
            self.state.chapters_completed += 1
            self.state.total_words_written += chapter.word_count
            return "next_chapter"

        # Continue editorial loop
        return "editorial_loop"

    @listen("next_chapter")
    def proceed_to_next_chapter(self):
        """Move to next chapter or finish"""
        self.state.current_phase = WorkflowPhase.WRITING
        self.state.last_updated = datetime.now().isoformat()

        # Check if more chapters to write
        remaining = [c for c in self.state.chapters if c.status != ChapterStatus.COMPLETE]

        if remaining:
            next_chapter = remaining[0]
            self.state.current_chapter = next_chapter.chapter_number
            return self._write_chapter(next_chapter)

        # All chapters complete
        return self.final_review_phase()

    # =========================================================================
    # PHASE 5: FINAL REVIEW
    # =========================================================================

    @listen(or_("next_chapter", "writing_phase"))
    def final_review_phase(self):
        """
        Final Review Phase: Full manuscript consistency check.
        """
        # Only run if all chapters are complete
        if self.state.chapters_completed < self.state.target_chapters:
            return None

        self.state.current_phase = WorkflowPhase.FINAL_REVIEW
        self.state.last_updated = datetime.now().isoformat()

        # Combine all chapters
        full_manuscript = "\n\n".join([
            f"# Chapter {c.chapter_number}\n\n{c.content}"
            for c in self.state.chapters
        ])

        # Final consistency check could go here
        # For now, mark complete

        self.state.current_phase = WorkflowPhase.COMPLETE
        self.state.last_updated = datetime.now().isoformat()

        return {
            "phase": "complete",
            "total_chapters": self.state.chapters_completed,
            "total_words": self.state.total_words_written,
            "status": "complete"
        }

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def _calculate_convergence(self, previous: str, current: str) -> float:
        """
        Calculate word-level edit distance as percentage.

        Returns value between 0 and 1, where:
        - 0 = identical (fully converged)
        - 1 = completely different
        """
        prev_words = previous.split()
        curr_words = current.split()

        matcher = difflib.SequenceMatcher(None, prev_words, curr_words)
        similarity = matcher.ratio()

        # Return change percentage (1 - similarity)
        return 1.0 - similarity

    def get_status(self) -> Dict[str, Any]:
        """Get current workflow status for UI"""
        return {
            "phase": self.state.current_phase.value,
            "progress": self.state.get_progress_percentage(),
            "current_chapter": self.state.current_chapter,
            "chapters_completed": self.state.chapters_completed,
            "total_chapters": self.state.target_chapters,
            "total_words": self.state.total_words_written,
            "review_status": self.state.current_review_status.value,
            "last_updated": self.state.last_updated
        }

    def export_manuscript(self) -> str:
        """Export complete manuscript as markdown"""
        lines = [
            f"# {self.state.project_name}",
            f"\n*Genre: {self.state.genre}*",
            f"\n*Total Words: {self.state.total_words_written:,}*",
            "\n---\n"
        ]

        for chapter in self.state.chapters:
            if chapter.content:
                lines.append(f"\n## Chapter {chapter.chapter_number}")
                if chapter.title:
                    lines.append(f"### {chapter.title}")
                lines.append(f"\n{chapter.content}\n")

        return "\n".join(lines)
