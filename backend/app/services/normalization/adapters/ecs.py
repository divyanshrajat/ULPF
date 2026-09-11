from typing import Any

def to_ecs(event_dict: dict[str, Any]) -> dict[str, Any]:
    """Adapts internal canonical format to ECS"""
    ecs = {
        "ecs": {"version": "8.11.0"},
        "event": {
            "id": event_dict.get("event_id"),
            "created": event_dict.get("event_time"),
        }
    }
    
    source = event_dict.get("source", {})
    if "ip" in source:
        ecs.setdefault("source", {})["ip"] = source["ip"]
    if "user" in source:
        ecs.setdefault("user", {})["name"] = source["user"]
        
    network = event_dict.get("network", {})
    if "port" in network:
        ecs.setdefault("source", {})["port"] = network["port"]
        
    security = event_dict.get("security", {})
    if "action" in security:
        ecs["event"]["action"] = security["action"]
        
    ecs["_unmapped"] = event_dict.get("unmapped_fields", {})
    ecs["_raw_reference"] = event_dict.get("raw_reference", {})
    
    return ecs
