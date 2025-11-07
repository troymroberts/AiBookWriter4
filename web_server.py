"""
AI Book Writer - Web Server
FastAPI-based web interface with real-time agent progress and LLM streaming.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sse_starlette.sse import EventSourceResponse
import yaml
import os
import glob

from rag import VectorStoreManager, sync_file_to_rag, AutoSyncYw7File
from config.llm_config import get_llm_config

# Import agents
from agents.story_planner import StoryPlanner, StoryPlannerConfig
from agents.character_creator import CharacterCreator, CharacterCreatorConfig
from agents.setting_builder import SettingBuilder, SettingBuilderConfig
from agents.outline_creator import OutlineCreator, OutlineCreatorConfig
from agents.writer import Writer, WriterConfig
from agents.editor import Editor, EditorConfig

# Import CrewAI components
from crewai import Crew, Task, Process

# Import yWriter7 components
from ywriter7.yw.yw7_file import Yw7File
from ywriter7.model.novel import Novel
from ywriter7.model.chapter import Chapter
from ywriter7.model.scene import Scene
from ywriter7.model.character import Character
from ywriter7.model.location import Location
from ywriter7.model.id_generator import create_id

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="AI Book Writer Studio")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="web/static"), name="static")
templates = Jinja2Templates(directory="web/templates")

# Global state for workflow progress
workflow_state = {
    "status": "idle",  # idle, running, completed, error
    "current_agent": None,
    "progress": 0,
    "output": [],
    "rag_stats": {}
}

# Load configuration
with open("config.yaml") as f:
    config = yaml.safe_load(f)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main dashboard page."""
    # Get RAG stats
    try:
        vector_store = VectorStoreManager()
        rag_stats = {
            "characters": len(vector_store.get_or_create_collection("characters").get()["ids"]),
            "locations": len(vector_store.get_or_create_collection("locations").get()["ids"]),
            "plot_events": len(vector_store.get_or_create_collection("plot_events").get()["ids"]),
        }
    except:
        rag_stats = {"characters": 0, "locations": 0, "plot_events": 0}

    # Get agent configurations
    agents_config = config.get("agents", {})

    return templates.TemplateResponse("index.html", {
        "request": request,
        "rag_stats": rag_stats,
        "agents_config": agents_config,
        "workflow_state": workflow_state
    })


@app.get("/api/config")
async def get_config():
    """Get current configuration."""
    return {
        "agents": config.get("agents", {}),
        "rag": config.get("rag", {}),
        "project": {
            "genre": config.get("genre", "literary_fiction"),
            "num_chapters": config.get("num_chapters", 12)
        }
    }


@app.post("/api/config/agent/{agent_name}")
async def update_agent_config(agent_name: str, updates: Dict[str, Any]):
    """Update agent configuration."""
    if agent_name not in config.get("agents", {}):
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")

    # Update config
    for key, value in updates.items():
        config["agents"][agent_name][key] = value

    # Save to file
    with open("config.yaml", "w") as f:
        yaml.dump(config, f)

    return {"status": "success", "agent": agent_name, "updates": updates}


@app.get("/api/rag/stats")
async def get_rag_stats():
    """Get RAG knowledge base statistics."""
    try:
        vector_store = VectorStoreManager()
        collections = ["characters", "locations", "items", "plot_events", "relationships", "lore"]

        stats = {}
        for collection_name in collections:
            try:
                collection = vector_store.get_or_create_collection(collection_name)
                items = collection.get()
                stats[collection_name] = {
                    "count": len(items["ids"]),
                    "items": [
                        {
                            "id": id,
                            "name": metadata.get("name", "Unknown"),
                            "type": metadata.get("type", collection_name)
                        }
                        for id, metadata in zip(items["ids"][:10], items["metadatas"][:10])
                    ] if items["ids"] else []
                }
            except:
                stats[collection_name] = {"count": 0, "items": []}

        return stats
    except Exception as e:
        logger.error(f"Error getting RAG stats: {e}")
        return {"error": str(e)}


@app.get("/api/rag/search")
async def search_rag(query: str, collection: str = "all", limit: int = 10):
    """Search RAG knowledge base."""
    try:
        vector_store = VectorStoreManager()

        if collection == "all":
            collections = ["characters", "locations", "plot_events"]
        else:
            collections = [collection]

        results = []
        for coll_name in collections:
            search_results = vector_store.semantic_search(coll_name, query, n_results=limit)
            for i, (doc_id, doc, metadata, distance) in enumerate(zip(
                search_results["ids"],
                search_results["documents"],
                search_results["metadatas"],
                search_results["distances"]
            )):
                results.append({
                    "collection": coll_name,
                    "id": doc_id,
                    "name": metadata.get("name", "Unknown"),
                    "similarity": round((1 - distance) * 100, 1),
                    "preview": doc[:200]
                })

        # Sort by similarity
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return {"results": results[:limit]}

    except Exception as e:
        logger.error(f"Error searching RAG: {e}")
        return {"error": str(e), "results": []}


@app.get("/api/projects")
async def list_projects():
    """List all yWriter7 projects in the output directory."""
    try:
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        projects = []
        for yw7_file in glob.glob(str(output_dir / "*.yw7")):
            file_path = Path(yw7_file)
            stat = file_path.stat()
            projects.append({
                "name": file_path.stem,
                "filename": file_path.name,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "download_url": f"/api/projects/download/{file_path.name}"
            })

        # Sort by modification time (newest first)
        projects.sort(key=lambda x: x["modified"], reverse=True)

        return {"projects": projects}

    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        return {"error": str(e), "projects": []}


@app.get("/api/projects/download/{filename}")
async def download_project(filename: str):
    """Download a yWriter7 project file."""
    try:
        # Security: prevent directory traversal
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")

        file_path = Path("output") / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Project not found")

        if not file_path.suffix == ".yw7":
            raise HTTPException(status_code=400, detail="Invalid file type")

        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type="application/xml"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/projects/{filename}")
async def delete_project(filename: str):
    """Delete a yWriter7 project file."""
    try:
        # Security: prevent directory traversal
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")

        file_path = Path("output") / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Project not found")

        if not file_path.suffix == ".yw7":
            raise HTTPException(status_code=400, detail="Invalid file type")

        # Also delete backup file if exists
        backup_path = Path(str(file_path) + ".bak")
        if backup_path.exists():
            backup_path.unlink()

        file_path.unlink()

        return {"status": "success", "message": f"Deleted {filename}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/workflow/status")
async def get_workflow_status():
    """Get current workflow status."""
    return workflow_state


@app.post("/api/workflow/start")
async def start_workflow(request: Request):
    """Start the book writing workflow."""
    global workflow_state

    body = await request.json()
    project_config = body.get("project", {})

    # Reset state
    workflow_state = {
        "status": "running",
        "current_agent": "story_planner",
        "progress": 0,
        "output": [],
        "rag_stats": {},
        "project": project_config
    }

    # Start workflow in background
    asyncio.create_task(run_workflow(project_config))

    return {"status": "started", "state": workflow_state}


@app.get("/api/workflow/stream")
async def stream_workflow():
    """Stream workflow progress via Server-Sent Events."""
    async def event_generator():
        last_output_len = 0

        while True:
            # Check if there are new outputs
            current_output_len = len(workflow_state["output"])

            if current_output_len > last_output_len:
                # Send new outputs
                new_outputs = workflow_state["output"][last_output_len:]
                for output in new_outputs:
                    yield {
                        "event": output.get("type", "message"),
                        "data": json.dumps(output)
                    }
                last_output_len = current_output_len

            # Send status update
            yield {
                "event": "status",
                "data": json.dumps({
                    "status": workflow_state["status"],
                    "current_agent": workflow_state["current_agent"],
                    "progress": workflow_state["progress"]
                })
            }

            # If workflow complete, send final event and close
            if workflow_state["status"] in ["completed", "error"]:
                yield {
                    "event": "complete",
                    "data": json.dumps(workflow_state)
                }
                break

            await asyncio.sleep(0.5)  # Update every 500ms

    return EventSourceResponse(event_generator())


async def run_workflow(project_config: Dict[str, Any]):
    """Run the complete book writing workflow with real CrewAI agents."""
    global workflow_state

    try:
        # Get project details
        project_name = project_config.get("name", "My Novel")
        genre = config.get("genre", "literary_fiction")
        num_chapters = config.get("num_chapters", 12)

        # Create yWriter7 project
        project_path = f"output/{project_name.replace(' ', '_').lower()}.yw7"
        Path(project_path).parent.mkdir(exist_ok=True)

        # Initialize project
        workflow_state["output"].append({
            "type": "info",
            "message": f"Creating project: {project_name}",
            "timestamp": datetime.now().isoformat()
        })

        yw7_file = Yw7File(project_path)
        yw7_file.novel = Novel()
        yw7_file.novel.title = project_name
        yw7_file.novel.authorName = "AI Book Writer"
        yw7_file.novel.desc = f"A {genre} novel created with AI Book Writer Studio"
        yw7_file.write()

        # ============================================================
        # STEP 1: Story Planning
        # ============================================================
        workflow_state["current_agent"] = "story_planner"
        workflow_state["progress"] = 10
        workflow_state["output"].append({
            "type": "progress",
            "agent": "story_planner",
            "message": "📖 Starting Story Planner...",
            "timestamp": datetime.now().isoformat()
        })

        # Initialize Story Planner
        planner_config = StoryPlannerConfig(
            temperature=config.get("agents", {}).get("story_planner", {}).get("temperature", 0.7),
            max_tokens=config.get("agents", {}).get("story_planner", {}).get("max_tokens", 12288),
        )
        story_planner = StoryPlanner(config=planner_config)

        # Create story planning task
        story_task = Task(
            description=f"""Create a compelling story arc for a {genre} novel with {num_chapters} chapters.
            Include:
            - Overall story premise and themes
            - Character arcs (protagonist, antagonist, supporting characters)
            - Three-act structure with key plot points
            - Chapter-by-chapter story progression
            - Thematic elements and narrative goals

            Project: {project_name}""",
            agent=story_planner,
            expected_output="Comprehensive story arc with plot structure and character arcs"
        )

        # Add LLM output notification
        workflow_state["output"].append({
            "type": "llm_output",
            "message": f"[Story Planner] Analyzing {genre} structure for {num_chapters} chapters...",
            "timestamp": datetime.now().isoformat()
        })

        # Execute planning
        story_crew = Crew(
            agents=[story_planner],
            tasks=[story_task],
            process=Process.sequential,
            verbose=True
        )

        workflow_state["output"].append({
            "type": "llm_output",
            "message": "[Story Planner] Generating story arc...",
            "timestamp": datetime.now().isoformat()
        })

        story_result = story_crew.kickoff()
        story_arc = str(story_result)

        # Stream partial result
        workflow_state["output"].append({
            "type": "llm_output",
            "message": f"[Story Planner] Result preview: {story_arc[:200]}...",
            "timestamp": datetime.now().isoformat()
        })

        workflow_state["output"].append({
            "type": "complete",
            "agent": "story_planner",
            "message": f"✓ Story arc created ({len(story_arc)} chars)",
            "timestamp": datetime.now().isoformat()
        })

        # Save to yWriter7 project notes
        with AutoSyncYw7File(project_path) as yw7:
            yw7.novel.desc = story_arc[:500]  # Save summary in description

        # ============================================================
        # STEP 2: Character Creation
        # ============================================================
        workflow_state["current_agent"] = "character_creator"
        workflow_state["progress"] = 30
        workflow_state["output"].append({
            "type": "progress",
            "agent": "character_creator",
            "message": "👥 Starting Character Creator...",
            "timestamp": datetime.now().isoformat()
        })

        char_config = CharacterCreatorConfig(
            temperature=config.get("agents", {}).get("character_creator", {}).get("temperature", 0.7),
            max_tokens=config.get("agents", {}).get("character_creator", {}).get("max_tokens", 6144),
        )
        character_creator = CharacterCreator(config=char_config)

        workflow_state["output"].append({
            "type": "llm_output",
            "message": "[Character Creator] Analyzing story for character requirements...",
            "timestamp": datetime.now().isoformat()
        })

        char_task = Task(
            description=f"""Based on the story arc, create detailed character profiles:

            Story Context:
            {story_arc[:1000]}

            Create 3-5 main characters with:
            - Full names and physical descriptions
            - Backstories and motivations
            - Character arcs and development
            - Relationships with other characters
            - Nicknames or alternate names (AKA)
            - Story goals (what they want to achieve)
            - Whether they are major or minor characters
            - yWriter7-compatible character data

            Use semantic search to ensure characters are unique.

            Format as structured data:
            CHARACTER: [name]
            FULLNAME: [full name]
            AKA: [nicknames, alternate names]
            DESC: [brief description]
            BIO: [detailed biography, background, personality]
            NOTES: [character development notes, arc notes]
            GOALS: [what the character wants to achieve in the story]
            MAJOR: [YES or NO - is this a major character?]
            ---
            (repeat for each character)""",
            agent=character_creator,
            expected_output="Detailed character profiles with bio, notes, goals, aka, and major/minor designation"
        )

        char_crew = Crew(
            agents=[character_creator],
            tasks=[char_task],
            process=Process.sequential,
            verbose=True
        )

        workflow_state["output"].append({
            "type": "llm_output",
            "message": "[Character Creator] Creating character profiles with RAG verification...",
            "timestamp": datetime.now().isoformat()
        })

        char_result = char_crew.kickoff()
        char_text = str(char_result)

        # Parse and create characters with full yWriter7 structure
        with AutoSyncYw7File(project_path) as yw7:
            current_char_data = {}
            lines = char_text.split('\n')

            for line in lines:
                line = line.strip()

                if line.startswith('CHARACTER:'):
                    # Save previous character if exists
                    if current_char_data.get('name'):
                        char_id = create_id(yw7.novel.characters)
                        character = Character()
                        character.title = current_char_data.get('name', 'Unnamed')
                        character.fullName = current_char_data.get('fullname', character.title)
                        character.aka = current_char_data.get('aka', '')
                        character.desc = current_char_data.get('desc', '')
                        character.bio = current_char_data.get('bio', '')
                        character.notes = current_char_data.get('notes', '')
                        character.goals = current_char_data.get('goals', '')
                        character.isMajor = True if current_char_data.get('major', 'YES') == 'YES' else False

                        yw7.novel.characters[char_id] = character
                        yw7.novel.srtCharacters.append(char_id)

                    # Start new character
                    current_char_data = {'name': line.replace('CHARACTER:', '').strip()}

                elif line.startswith('FULLNAME:'):
                    current_char_data['fullname'] = line.replace('FULLNAME:', '').strip()
                elif line.startswith('AKA:'):
                    current_char_data['aka'] = line.replace('AKA:', '').strip()
                elif line.startswith('DESC:'):
                    current_char_data['desc'] = line.replace('DESC:', '').strip()
                elif line.startswith('BIO:'):
                    current_char_data['bio'] = line.replace('BIO:', '').strip()
                elif line.startswith('NOTES:'):
                    current_char_data['notes'] = line.replace('NOTES:', '').strip()
                elif line.startswith('GOALS:'):
                    current_char_data['goals'] = line.replace('GOALS:', '').strip()
                elif line.startswith('MAJOR:'):
                    current_char_data['major'] = line.replace('MAJOR:', '').strip()

            # Save last character
            if current_char_data.get('name'):
                char_id = create_id(yw7.novel.characters)
                character = Character()
                character.title = current_char_data.get('name', 'Unnamed')
                character.fullName = current_char_data.get('fullname', character.title)
                character.aka = current_char_data.get('aka', '')
                character.desc = current_char_data.get('desc', '')
                character.bio = current_char_data.get('bio', '')
                character.notes = current_char_data.get('notes', '')
                character.goals = current_char_data.get('goals', '')
                character.isMajor = True if current_char_data.get('major', 'YES') == 'YES' else False

                yw7.novel.characters[char_id] = character
                yw7.novel.srtCharacters.append(char_id)

        workflow_state["output"].append({
            "type": "llm_output",
            "message": f"[Character Creator] Created {len(yw7.novel.characters)} characters with full profiles",
            "timestamp": datetime.now().isoformat()
        })

        workflow_state["output"].append({
            "type": "complete",
            "agent": "character_creator",
            "message": "✓ Characters created with bio, notes, goals, aka",
            "timestamp": datetime.now().isoformat()
        })

        # ============================================================
        # STEP 3: Setting & Location Building
        # ============================================================
        workflow_state["current_agent"] = "setting_builder"
        workflow_state["progress"] = 50
        workflow_state["output"].append({
            "type": "progress",
            "agent": "setting_builder",
            "message": "🌍 Starting Setting Builder...",
            "timestamp": datetime.now().isoformat()
        })

        setting_config = SettingBuilderConfig(
            temperature=config.get("agents", {}).get("setting_builder", {}).get("temperature", 0.7),
            max_tokens=config.get("agents", {}).get("setting_builder", {}).get("max_tokens", 8192),
        )
        setting_builder = SettingBuilder(config=setting_config)

        setting_task = Task(
            description=f"""Create detailed settings and locations for the story:

            Story Context:
            {story_arc[:1000]}

            Create 3-5 key locations with:
            - Vivid descriptions
            - Atmosphere and mood
            - Significance to the story
            - Alternate names (AKA) - nicknames, colloquial names, or historical names
            - yWriter7-compatible location data

            Format as structured data:
            LOCATION: [name]
            AKA: [alternate names, nicknames]
            DESC: [vivid description with atmosphere and mood]
            ---
            (repeat for each location)""",
            agent=setting_builder,
            expected_output="Rich location descriptions with alternate names ready for yWriter7"
        )

        setting_crew = Crew(
            agents=[setting_builder],
            tasks=[setting_task],
            process=Process.sequential,
            verbose=True
        )

        setting_result = setting_crew.kickoff()
        location_text = str(setting_result)

        # Parse and create locations with full yWriter7 structure
        with AutoSyncYw7File(project_path) as yw7:
            current_loc_data = {}
            lines = location_text.split('\n')

            for line in lines:
                line = line.strip()

                if line.startswith('LOCATION:'):
                    # Save previous location if exists
                    if current_loc_data.get('name'):
                        loc_id = create_id(yw7.novel.locations)
                        location = Location()
                        location.title = current_loc_data.get('name', 'Unnamed Location')
                        location.aka = current_loc_data.get('aka', '')
                        location.desc = current_loc_data.get('desc', '')

                        yw7.novel.locations[loc_id] = location
                        yw7.novel.srtLocations.append(loc_id)

                    # Start new location
                    current_loc_data = {'name': line.replace('LOCATION:', '').strip()}

                elif line.startswith('AKA:'):
                    current_loc_data['aka'] = line.replace('AKA:', '').strip()
                elif line.startswith('DESC:'):
                    # DESC might span multiple lines, so accumulate
                    if 'desc' not in current_loc_data:
                        current_loc_data['desc'] = line.replace('DESC:', '').strip()
                    else:
                        current_loc_data['desc'] += ' ' + line

            # Save last location
            if current_loc_data.get('name'):
                loc_id = create_id(yw7.novel.locations)
                location = Location()
                location.title = current_loc_data.get('name', 'Unnamed Location')
                location.aka = current_loc_data.get('aka', '')
                location.desc = current_loc_data.get('desc', '')

                yw7.novel.locations[loc_id] = location
                yw7.novel.srtLocations.append(loc_id)

        workflow_state["output"].append({
            "type": "complete",
            "agent": "setting_builder",
            "message": "✓ Settings created with alternate names",
            "timestamp": datetime.now().isoformat()
        })

        # ============================================================
        # STEP 4: Chapter Outlining
        # ============================================================
        workflow_state["current_agent"] = "outline_creator"
        workflow_state["progress"] = 70
        workflow_state["output"].append({
            "type": "progress",
            "agent": "outline_creator",
            "message": "📝 Creating chapter outlines...",
            "timestamp": datetime.now().isoformat()
        })

        outline_config = OutlineCreatorConfig(
            temperature=config.get("agents", {}).get("outline_creator", {}).get("temperature", 0.7),
            max_tokens=config.get("agents", {}).get("outline_creator", {}).get("max_tokens", 12288),
        )
        outline_creator = OutlineCreator(config=outline_config)

        outline_task = Task(
            description=f"""Create detailed chapter-by-chapter outlines with scene breakdowns:

            Story Arc:
            {story_arc}

            For each of {num_chapters} chapters:
            - Chapter title and summary
            - Scene breakdowns with:
              * Scene goals (what needs to be accomplished)
              * Scene conflict (obstacles and tension)
              * Scene outcome (how it ends and connects to next scene)
            - POV character
            - Key events and character development

            Format for yWriter7 integration.""",
            agent=outline_creator,
            expected_output="Comprehensive chapter outlines with scene goals/conflicts/outcomes"
        )

        outline_crew = Crew(
            agents=[outline_creator],
            tasks=[outline_task],
            process=Process.sequential,
            verbose=True
        )

        outline_result = outline_crew.kickoff()

        # Parse outline to extract chapter and scene structure
        outline_text = str(outline_result)

        workflow_state["output"].append({
            "type": "complete",
            "agent": "outline_creator",
            "message": f"✓ Created {num_chapters} chapter outlines",
            "timestamp": datetime.now().isoformat()
        })

        # ============================================================
        # STEP 5: Scene Structure Creation
        # ============================================================
        workflow_state["current_agent"] = "scene_builder"
        workflow_state["progress"] = 75
        workflow_state["output"].append({
            "type": "progress",
            "agent": "scene_builder",
            "message": "🎬 Creating scene structure with goals/conflicts/outcomes...",
            "timestamp": datetime.now().isoformat()
        })

        # Use outline creator to generate structured scene data
        scene_structure_task = Task(
            description=f"""Parse the chapter outlines and create detailed scene structure.

            Chapter Outlines:
            {outline_text}

            For each chapter, extract:
            1. Chapter title and description (summary of all scenes in the chapter)
            2. For each scene in the chapter:
               - Scene title
               - Scene goal (what the character wants to accomplish)
               - Scene conflict (obstacles, tension, opposition)
               - Scene outcome (how it resolves and connects to next scene)
               - Is it an ACTION scene or REACTION scene? (Action = pursuit of goal, Reaction = processing consequences)
               - Scene mode (Dramatic action / Dialogue / Description / Exposition)
               - POV character
               - Key location

            Format as structured data that can be parsed:
            CHAPTER: [number] - [title]
            CHAPTER_DESC: [summary of all scenes]
            SCENE: [title]
            GOAL: [specific goal]
            CONFLICT: [specific conflict]
            OUTCOME: [specific outcome]
            TYPE: [ACTION or REACTION]
            MODE: [narrative mode]
            POV: [character name]
            LOCATION: [location name]
            ---
            (repeat for each scene)""",
            agent=outline_creator,
            expected_output="Structured scene data with goals, conflicts, outcomes for all scenes"
        )

        scene_crew = Crew(
            agents=[outline_creator],
            tasks=[scene_structure_task],
            process=Process.sequential,
            verbose=True
        )

        scene_structure_result = scene_crew.kickoff()
        scene_data_text = str(scene_structure_result)

        # Parse and create chapters/scenes with full yWriter7 structure
        with AutoSyncYw7File(project_path) as yw7:
            current_chapter = None
            current_chapter_id = None
            current_scene_data = {}

            # Simple parser for structured scene data
            lines = scene_data_text.split('\n')
            for line in lines:
                line = line.strip()

                if line.startswith('CHAPTER:'):
                    # Save previous chapter if exists
                    if current_chapter_id and current_chapter:
                        yw7.novel.chapters[current_chapter_id] = current_chapter
                        yw7.novel.srtChapters.append(current_chapter_id)

                    # Create new chapter
                    current_chapter_id = create_id(yw7.novel.chapters)
                    current_chapter = Chapter()
                    chapter_title = line.replace('CHAPTER:', '').strip()
                    current_chapter.title = chapter_title
                    current_chapter.chLevel = 0
                    current_chapter.chType = 0
                    current_chapter.srtScenes = []

                elif line.startswith('CHAPTER_DESC:'):
                    if current_chapter:
                        current_chapter.desc = line.replace('CHAPTER_DESC:', '').strip()

                elif line.startswith('SCENE:'):
                    # Save previous scene if exists
                    if current_scene_data.get('title') and current_chapter:
                        scene_id = create_id(yw7.novel.scenes)
                        scene = Scene()
                        scene.title = current_scene_data.get('title', 'Untitled Scene')
                        scene.desc = f"{current_scene_data.get('goal', '')} - {current_scene_data.get('conflict', '')}"

                        # Populate goal/conflict/outcome (Dwight Swain structure)
                        scene.goal = current_scene_data.get('goal', '')
                        scene.conflict = current_scene_data.get('conflict', '')
                        scene.outcome = current_scene_data.get('outcome', '')

                        # Set scene type (Action vs Reaction)
                        scene_type = current_scene_data.get('type', 'ACTION')
                        scene.isReactionScene = True if scene_type == 'REACTION' else False

                        # Set narrative mode
                        scene.scnMode = current_scene_data.get('mode', 'Dramatic action')

                        # Add storyline tracking
                        scene.scnArcs = 'Main Plot'

                        # Add placeholder for content (Writer agent will fill this)
                        scene.sceneContent = f"[Scene to be written: {scene.title}]"

                        # Notes field for scene planning
                        scene.notes = f"POV: {current_scene_data.get('pov', 'Unknown')}\nLocation: {current_scene_data.get('location', 'Unknown')}"

                        # Tags for organization
                        scene.tags = current_scene_data.get('type', 'ACTION').lower()

                        yw7.novel.scenes[scene_id] = scene
                        current_chapter.srtScenes.append(scene_id)

                    # Start new scene
                    current_scene_data = {'title': line.replace('SCENE:', '').strip()}

                elif line.startswith('GOAL:'):
                    current_scene_data['goal'] = line.replace('GOAL:', '').strip()
                elif line.startswith('CONFLICT:'):
                    current_scene_data['conflict'] = line.replace('CONFLICT:', '').strip()
                elif line.startswith('OUTCOME:'):
                    current_scene_data['outcome'] = line.replace('OUTCOME:', '').strip()
                elif line.startswith('TYPE:'):
                    current_scene_data['type'] = line.replace('TYPE:', '').strip()
                elif line.startswith('MODE:'):
                    current_scene_data['mode'] = line.replace('MODE:', '').strip()
                elif line.startswith('POV:'):
                    current_scene_data['pov'] = line.replace('POV:', '').strip()
                elif line.startswith('LOCATION:'):
                    current_scene_data['location'] = line.replace('LOCATION:', '').strip()

            # Save last scene and chapter
            if current_scene_data.get('title') and current_chapter:
                scene_id = create_id(yw7.novel.scenes)
                scene = Scene()
                scene.title = current_scene_data.get('title', 'Untitled Scene')
                scene.desc = f"{current_scene_data.get('goal', '')} - {current_scene_data.get('conflict', '')}"
                scene.goal = current_scene_data.get('goal', '')
                scene.conflict = current_scene_data.get('conflict', '')
                scene.outcome = current_scene_data.get('outcome', '')
                scene.isReactionScene = True if current_scene_data.get('type') == 'REACTION' else False
                scene.scnMode = current_scene_data.get('mode', 'Dramatic action')
                scene.scnArcs = 'Main Plot'
                scene.sceneContent = f"[Scene to be written: {scene.title}]"
                scene.notes = f"POV: {current_scene_data.get('pov', 'Unknown')}\nLocation: {current_scene_data.get('location', 'Unknown')}"
                scene.tags = current_scene_data.get('type', 'ACTION').lower()
                yw7.novel.scenes[scene_id] = scene
                current_chapter.srtScenes.append(scene_id)

            if current_chapter_id and current_chapter:
                yw7.novel.chapters[current_chapter_id] = current_chapter
                yw7.novel.srtChapters.append(current_chapter_id)

        workflow_state["output"].append({
            "type": "complete",
            "agent": "scene_builder",
            "message": f"✓ Scene structure created with goals/conflicts/outcomes",
            "timestamp": datetime.now().isoformat()
        })

        # ============================================================
        # STEP 6: Prose Writing
        # ============================================================
        workflow_state["current_agent"] = "writer"
        workflow_state["progress"] = 85
        workflow_state["output"].append({
            "type": "progress",
            "agent": "writer",
            "message": "✍️ Writing scene prose...",
            "timestamp": datetime.now().isoformat()
        })

        # Initialize Writer agent
        writer_config = WriterConfig(
            temperature=config.get("agents", {}).get("writer", {}).get("temperature", 0.8),
            max_tokens=config.get("agents", {}).get("writer", {}).get("max_tokens", 16384),
        )
        writer = Writer(config=writer_config)

        # Write prose for each scene (first 3 scenes for now to avoid long execution)
        with AutoSyncYw7File(project_path) as yw7:
            scenes_written = 0
            max_scenes_to_write = 3  # Limit for testing

            for ch_id in yw7.novel.srtChapters[:2]:  # First 2 chapters
                chapter = yw7.novel.chapters[ch_id]

                for scene_id in chapter.srtScenes:
                    if scenes_written >= max_scenes_to_write:
                        break

                    scene = yw7.novel.scenes[scene_id]

                    workflow_state["output"].append({
                        "type": "llm_output",
                        "message": f"[Writer] Writing: {scene.title}",
                        "timestamp": datetime.now().isoformat()
                    })

                    # Create writing task
                    write_task = Task(
                        description=f"""Write compelling prose for this scene:

                        Title: {scene.title}
                        Goal: {scene.goal}
                        Conflict: {scene.conflict}
                        Outcome: {scene.outcome}
                        Type: {'REACTION' if scene.isReactionScene else 'ACTION'} scene
                        Mode: {scene.scnMode}
                        POV: {scene.notes}

                        Story Context:
                        {story_arc[:500]}

                        Write 800-1200 words of engaging prose that:
                        - Shows the character pursuing their goal
                        - Dramatizes the conflict with tension
                        - Reaches the specified outcome
                        - Uses vivid sensory details
                        - Includes compelling dialogue
                        - Maintains consistent character voice

                        Use RAG tools to verify character and location details.""",
                        agent=writer,
                        expected_output="800-1200 words of polished prose"
                    )

                    write_crew = Crew(
                        agents=[writer],
                        tasks=[write_task],
                        process=Process.sequential,
                        verbose=True
                    )

                    prose_result = write_crew.kickoff()
                    scene.sceneContent = str(prose_result)
                    scenes_written += 1

                    workflow_state["output"].append({
                        "type": "llm_output",
                        "message": f"[Writer] ✓ Completed: {scene.title} ({len(str(prose_result))} chars)",
                        "timestamp": datetime.now().isoformat()
                    })

        workflow_state["output"].append({
            "type": "complete",
            "agent": "writer",
            "message": f"✓ Wrote prose for {scenes_written} scenes",
            "timestamp": datetime.now().isoformat()
        })

        # ============================================================
        # STEP 7: Editorial Refinement
        # ============================================================
        workflow_state["current_agent"] = "editor"
        workflow_state["progress"] = 95
        workflow_state["output"].append({
            "type": "progress",
            "agent": "editor",
            "message": "📝 Refining prose...",
            "timestamp": datetime.now().isoformat()
        })

        # Initialize Editor agent
        editor_config = EditorConfig(
            temperature=config.get("agents", {}).get("editor", {}).get("temperature", 0.5),
            max_tokens=config.get("agents", {}).get("editor", {}).get("max_tokens", 8192),
        )
        editor = Editor(config=editor_config)

        # Edit the written scenes
        with AutoSyncYw7File(project_path) as yw7:
            scenes_edited = 0

            for ch_id in yw7.novel.srtChapters[:2]:
                chapter = yw7.novel.chapters[ch_id]

                for scene_id in chapter.srtScenes:
                    if scenes_edited >= max_scenes_to_write:
                        break

                    scene = yw7.novel.scenes[scene_id]

                    # Skip placeholder scenes
                    if scene.sceneContent.startswith('[Scene to be written'):
                        continue

                    workflow_state["output"].append({
                        "type": "llm_output",
                        "message": f"[Editor] Refining: {scene.title}",
                        "timestamp": datetime.now().isoformat()
                    })

                    edit_task = Task(
                        description=f"""Review and refine this scene:

                        Title: {scene.title}
                        Current Draft:
                        {scene.sceneContent}

                        Improve:
                        - Clarity and flow
                        - Dialogue naturalness
                        - Pacing and tension
                        - Sensory details
                        - Grammar and style

                        Maintain the core story beats and character voice.""",
                        agent=editor,
                        expected_output="Refined, polished prose"
                    )

                    edit_crew = Crew(
                        agents=[editor],
                        tasks=[edit_task],
                        process=Process.sequential,
                        verbose=True
                    )

                    edited_result = edit_crew.kickoff()
                    scene.sceneContent = str(edited_result)
                    scenes_edited += 1

        workflow_state["output"].append({
            "type": "complete",
            "agent": "editor",
            "message": f"✓ Refined {scenes_edited} scenes",
            "timestamp": datetime.now().isoformat()
        })

        # ============================================================
        # FINAL: Complete
        # ============================================================
        workflow_state["status"] = "completed"
        workflow_state["progress"] = 100
        workflow_state["output"].append({
            "type": "success",
            "message": f"✓ Project '{project_name}' created successfully!\nFile: {project_path}\nScenes written: {scenes_written}",
            "timestamp": datetime.now().isoformat()
        })

        # Sync to RAG
        sync_stats = sync_file_to_rag(project_path)
        workflow_state["rag_stats"] = sync_stats

        logger.info(f"Workflow completed: {project_path}")

    except Exception as e:
        logger.error(f"Workflow error: {e}", exc_info=True)
        workflow_state["status"] = "error"
        workflow_state["output"].append({
            "type": "error",
            "message": f"Error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
