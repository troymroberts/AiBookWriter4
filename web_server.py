"""
AI Book Writer - Web Server
FastAPI-based web interface with real-time agent progress and LLM streaming.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sse_starlette.sse import EventSourceResponse
import yaml

from rag import VectorStoreManager, sync_file_to_rag
from config.llm_config import get_llm_config

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
    """Run the complete book writing workflow."""
    global workflow_state

    try:
        # Simulated workflow for now - you'll integrate real agents here
        agents = [
            "story_planner",
            "character_creator",
            "setting_builder",
            "outline_creator",
            "writer",
            "editor"
        ]

        for i, agent_name in enumerate(agents):
            workflow_state["current_agent"] = agent_name
            workflow_state["progress"] = int((i / len(agents)) * 100)

            # Add progress message
            workflow_state["output"].append({
                "type": "progress",
                "agent": agent_name,
                "message": f"Starting {agent_name.replace('_', ' ').title()}...",
                "timestamp": datetime.now().isoformat()
            })

            # Simulate agent work
            await asyncio.sleep(2)

            # Add completion message
            workflow_state["output"].append({
                "type": "complete",
                "agent": agent_name,
                "message": f"{agent_name.replace('_', ' ').title()} completed!",
                "timestamp": datetime.now().isoformat()
            })

        workflow_state["status"] = "completed"
        workflow_state["progress"] = 100

    except Exception as e:
        logger.error(f"Workflow error: {e}", exc_info=True)
        workflow_state["status"] = "error"
        workflow_state["output"].append({
            "type": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
