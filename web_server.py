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
            - yWriter7-compatible character data

            Use semantic search to ensure characters are unique.""",
            agent=character_creator,
            expected_output="Detailed character profiles ready for yWriter7"
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

        workflow_state["output"].append({
            "type": "llm_output",
            "message": f"[Character Creator] Generated characters: {str(char_result)[:150]}...",
            "timestamp": datetime.now().isoformat()
        })

        workflow_state["output"].append({
            "type": "complete",
            "agent": "character_creator",
            "message": "✓ Characters created",
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
            - yWriter7-compatible location data""",
            agent=setting_builder,
            expected_output="Rich location descriptions ready for yWriter7"
        )

        setting_crew = Crew(
            agents=[setting_builder],
            tasks=[setting_task],
            process=Process.sequential,
            verbose=True
        )

        setting_result = setting_crew.kickoff()

        workflow_state["output"].append({
            "type": "complete",
            "agent": "setting_builder",
            "message": "✓ Settings created",
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

        # Create chapters in yWriter7
        with AutoSyncYw7File(project_path) as yw7:
            for i in range(num_chapters):
                ch_id = create_id(yw7.novel.chapters)
                chapter = Chapter()
                chapter.title = f"Chapter {i+1}"
                chapter.desc = f"Chapter {i+1} outline from story planning"
                chapter.chLevel = 0
                chapter.chType = 0
                chapter.srtScenes = []
                yw7.novel.chapters[ch_id] = chapter
                yw7.novel.srtChapters.append(ch_id)

        workflow_state["output"].append({
            "type": "complete",
            "agent": "outline_creator",
            "message": f"✓ Created {num_chapters} chapter outlines",
            "timestamp": datetime.now().isoformat()
        })

        # ============================================================
        # FINAL: Complete
        # ============================================================
        workflow_state["status"] = "completed"
        workflow_state["progress"] = 100
        workflow_state["output"].append({
            "type": "success",
            "message": f"✓ Project '{project_name}' created successfully!\nFile: {project_path}",
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
