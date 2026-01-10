"""Data models for Ó bože."""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class Position(BaseModel):
    """2D position on the map."""
    x: float
    y: float


class EntityProperties(BaseModel):
    """Properties of an entity."""
    character: str = ""
    goals: str = ""
    health: int = 100
    appearance: str = ""


class Entity(BaseModel):
    """A being in the game world."""
    id: str
    name: str
    position: Position
    radius: float = 5.0
    listensToPlayer: bool = False
    properties: EntityProperties = Field(default_factory=EntityProperties)
    alive: bool = True


class Scenario(BaseModel):
    """A game scenario."""
    id: str
    name: str
    description: str
    entities: list[Entity]


class ActionType(str, Enum):
    """Types of actions entities can perform."""
    MOVE = "move"
    WAIT = "wait"
    DISAPPEAR = "disappear"


class Direction(BaseModel):
    """Movement direction (normalized)."""
    x: float = 0.0
    y: float = 0.0


class Command(BaseModel):
    """A command for the game engine."""
    entityId: str
    action: ActionType
    direction: Optional[Direction] = None
    steps: int = 0
    speed: float = 1.0
    delay: int = 0  # Delay in steps before executing


class EngineCommands(BaseModel):
    """Batch of commands for the engine."""
    commands: list[Command]


class AgentResponse(BaseModel):
    """Response from the AI agent."""
    narrative: str  # Text for the player
    commands: EngineCommands  # Commands for the engine
    error: Optional[str] = None
