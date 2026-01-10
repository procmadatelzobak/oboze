"""FastAPI main application for Ó bože."""
import json
import logging
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse

from app.logging_config import logger
from app.config import get_config
from app.models import Scenario, Entity, Position, EntityProperties
from app.agent import get_agent
from app.engine import validate_commands, prepare_animation_data

# Initialize FastAPI
app = FastAPI(title="Ó bože", description="World Simulator Game")

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
STATIC_DIR = PROJECT_ROOT / "static"
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

logger.info("Ó bože server initialized")


def load_scenario(scenario_id: str = "default") -> Scenario:
    """Load a scenario from JSON file."""
    scenario_path = SCENARIOS_DIR / f"{scenario_id}.json"
    
    if scenario_path.exists():
        logger.info(f"Loading scenario from file: {scenario_path}")
        with open(scenario_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return Scenario(**data)
    
    logger.warning(f"Scenario file not found: {scenario_path}, using default")
    # Fallback to default scenario
    return Scenario(
        id="default",
        name="Setkání dvou bytostí",
        description="Stojí naproti sobě dva lidé. Ty jsi bože - bytost A ti naslouchá. Co jí poradíš?",
        entities=[
            Entity(
                id="A",
                name="Poutník",
                position=Position(x=20, y=50),
                radius=5,
                listensToPlayer=True,
                properties=EntityProperties(
                    character="Opatrný člověk hledající cestu",
                    goals="Přežít a najít bezpečí",
                    health=100
                )
            ),
            Entity(
                id="B",
                name="Zloděj",
                position=Position(x=80, y=50),
                radius=5,
                listensToPlayer=False,
                properties=EntityProperties(
                    character="Lstivý zloděj",
                    goals="Okrást A tím, že si získá jeho důvěru",
                    health=100
                )
            )
        ]
    )


def get_scenario_info(scenario_id: str) -> dict:
    """Get scenario metadata without loading full entities."""
    scenario_path = SCENARIOS_DIR / f"{scenario_id}.json"
    if scenario_path.exists():
        with open(scenario_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {
                "id": data.get("id", scenario_id),
                "name": data.get("name", scenario_id),
                "description": data.get("description", "")[:100] + "..."
            }
    return {"id": scenario_id, "name": scenario_id, "description": ""}


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve main page."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return index_path.read_text(encoding="utf-8")
    return HTMLResponse("<h1>Ó bože</h1><p>Static files not found.</p>")


@app.get("/api/scenario/{scenario_id}")
async def get_scenario(scenario_id: str = "default"):
    """Get scenario data."""
    scenario = load_scenario(scenario_id)
    return JSONResponse(scenario.model_dump())


@app.get("/api/scenarios")
async def list_scenarios():
    """List available scenarios with metadata."""
    scenarios = []
    if SCENARIOS_DIR.exists():
        for f in SCENARIOS_DIR.glob("*.json"):
            scenarios.append(get_scenario_info(f.stem))
    if not scenarios:
        scenarios.append({"id": "default", "name": "Výchozí scénář", "description": "Setkání dvou bytostí"})
    return JSONResponse({"scenarios": scenarios})


@app.get("/api/config")
async def get_api_config():
    """Get current configuration (without exposing full API key)."""
    try:
        config = get_config()
        # Mask API key for security (show only last 4 chars)
        api_key = config.get("gemini", {}).get("api_key", "")
        masked_key = "..." + api_key[-4:] if len(api_key) > 4 else "NOT SET"
        
        return JSONResponse({
            "gemini": {
                "api_key_masked": masked_key,
                "api_key_set": len(api_key) > 10,
                "model": config.get("gemini", {}).get("model", "gemini-2.0-flash")
            }
        })
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/config")
async def update_api_config(request_data: dict):
    """Update configuration."""
    from app.config import update_config
    from app.agent import reset_agent
    
    try:
        updates = {}
        
        # Handle API key update
        if "api_key" in request_data and request_data["api_key"]:
            updates["gemini"] = updates.get("gemini", {})
            updates["gemini"]["api_key"] = request_data["api_key"]
        
        # Handle model update
        if "model" in request_data and request_data["model"]:
            updates["gemini"] = updates.get("gemini", {})
            updates["gemini"]["model"] = request_data["model"]
        
        if updates:
            update_config(updates)
            reset_agent()  # Reset agent to use new config
            logger.info(f"Configuration updated: {list(updates.keys())}")
        
        return JSONResponse({"success": True})
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/models")
async def list_models():
    """List available Gemini models."""
    import google.generativeai as genai
    
    try:
        config = get_config()
        api_key = config.get("gemini", {}).get("api_key", "")
        
        if not api_key or len(api_key) < 10:
            return JSONResponse({
                "error": "API key not configured",
                "models": []
            })
        
        genai.configure(api_key=api_key)
        
        models = []
        for model in genai.list_models():
            # Only include models that support generateContent
            if 'generateContent' in model.supported_generation_methods:
                models.append({
                    "name": model.name.replace("models/", ""),
                    "display_name": model.display_name,
                    "description": model.description[:100] if model.description else ""
                })
        
        # Sort by name
        models.sort(key=lambda x: x["name"])
        
        logger.info(f"Found {len(models)} available models")
        return JSONResponse({"models": models})
        
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        return JSONResponse({
            "error": str(e),
            "models": []
        })


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time game communication."""
    await websocket.accept()
    logger.info("WebSocket client connected")
    
    # Load current scenario
    current_scenario = load_scenario("default")
    
    # Send initial scenario
    await websocket.send_json({
        "type": "scenario",
        "data": current_scenario.model_dump()
    })
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            logger.debug(f"Received message: {data}")
            
            if data.get("type") == "user_input":
                user_input = data.get("text", "")
                logger.info(f"User input: {user_input}")
                
                # Notify client we're processing
                await websocket.send_json({
                    "type": "status",
                    "status": "thinking"
                })
                
                # Process with AI agent
                agent = get_agent()
                response = agent.process_input(user_input, current_scenario)
                
                logger.info(f"Agent narrative: {response.narrative[:100]}...")
                logger.debug(f"Agent commands: {response.commands}")
                
                if response.error:
                    logger.error(f"Agent error: {response.error}")
                
                # Validate commands
                config = get_config()
                errors = validate_commands(
                    response.commands,
                    current_scenario.entities,
                    map_size=config.get("game", {}).get("map_size", 100),
                    max_steps=config.get("game", {}).get("max_steps_per_command", 200)
                )
                
                if errors:
                    logger.warning(f"Command validation errors: {errors}")
                    await websocket.send_json({
                        "type": "error",
                        "errors": errors
                    })
                    continue
                
                # Prepare animation data
                animation = prepare_animation_data(response.commands, current_scenario.entities)
                logger.debug(f"Animation data prepared: {len(animation.get('commands', []))} commands")
                
                # Send response with animation data
                await websocket.send_json({
                    "type": "response",
                    "narrative": response.narrative,
                    "animation": animation,
                    "error": response.error
                })
            
            elif data.get("type") == "load_scenario":
                scenario_id = data.get("scenario_id", "default")
                logger.info(f"Loading scenario: {scenario_id}")
                current_scenario = load_scenario(scenario_id)
                await websocket.send_json({
                    "type": "scenario",
                    "data": current_scenario.model_dump()
                })
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.exception(f"WebSocket error: {e}")
        await websocket.send_json({
            "type": "error",
            "errors": [str(e)]
        })
