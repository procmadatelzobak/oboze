"""Game engine for Ó bože."""
from app.models import Entity, Command, EngineCommands, ActionType


class EngineError(Exception):
    """Error in game engine."""
    pass


def validate_commands(commands: EngineCommands, entities: list[Entity], map_size: int = 100, max_steps: int = 200) -> list[str]:
    """
    Validate commands against game rules.
    Returns list of error messages (empty if valid).
    """
    errors = []
    entity_ids = {e.id for e in entities}
    
    for cmd in commands.commands:
        # Check entity exists
        if cmd.entityId not in entity_ids:
            errors.append(f"Entity '{cmd.entityId}' does not exist")
            continue
        
        # Validate move command
        if cmd.action == ActionType.MOVE:
            if cmd.steps > max_steps:
                errors.append(f"Entity '{cmd.entityId}': steps ({cmd.steps}) exceeds max ({max_steps})")
            if cmd.speed < 0 or cmd.speed > 10:
                errors.append(f"Entity '{cmd.entityId}': invalid speed ({cmd.speed})")
            if cmd.direction is None:
                errors.append(f"Entity '{cmd.entityId}': move action requires direction")
        
        # Validate wait command
        if cmd.action == ActionType.WAIT:
            if cmd.steps < 0 or cmd.steps > max_steps:
                errors.append(f"Entity '{cmd.entityId}': wait steps ({cmd.steps}) out of range")
        
        # Validate disappear command
        if cmd.action == ActionType.DISAPPEAR:
            if cmd.delay < 0 or cmd.delay > max_steps * 2:
                errors.append(f"Entity '{cmd.entityId}': invalid delay ({cmd.delay})")
    
    return errors


def compute_final_positions(commands: EngineCommands, entities: list[Entity], map_size: int = 100) -> dict:
    """
    Compute final positions after all commands execute.
    Returns dict with entity_id -> final_position or None if disappeared.
    """
    positions = {e.id: {"x": e.position.x, "y": e.position.y, "alive": True} for e in entities}
    
    for cmd in commands.commands:
        if cmd.entityId not in positions:
            continue
            
        if cmd.action == ActionType.DISAPPEAR:
            positions[cmd.entityId]["alive"] = False
            
        elif cmd.action == ActionType.MOVE and cmd.direction:
            # Compute final position after movement
            pos = positions[cmd.entityId]
            dx = cmd.direction.x * cmd.steps * cmd.speed
            dy = cmd.direction.y * cmd.steps * cmd.speed
            pos["x"] += dx
            pos["y"] += dy
            
            # Check if entity left the map
            if pos["x"] < 0 or pos["x"] > map_size or pos["y"] < 0 or pos["y"] > map_size:
                positions[cmd.entityId]["alive"] = False
    
    return positions


def prepare_animation_data(commands: EngineCommands, entities: list[Entity]) -> dict:
    """
    Prepare animation data for frontend.
    Returns data structure that frontend can use to animate entities.
    """
    # Initial state
    entity_states = {}
    for e in entities:
        entity_states[e.id] = {
            "id": e.id,
            "name": e.name,
            "x": e.position.x,
            "y": e.position.y,
            "radius": e.radius,
            "listensToPlayer": e.listensToPlayer,
            "alive": e.alive
        }
    
    # Commands in order
    animation_commands = []
    for cmd in commands.commands:
        animation_commands.append({
            "entityId": cmd.entityId,
            "action": cmd.action.value,
            "direction": {"x": cmd.direction.x, "y": cmd.direction.y} if cmd.direction else None,
            "steps": cmd.steps,
            "speed": cmd.speed,
            "delay": cmd.delay
        })
    
    return {
        "entities": entity_states,
        "commands": animation_commands
    }
