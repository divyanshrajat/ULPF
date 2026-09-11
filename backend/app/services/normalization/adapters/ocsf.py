from typing import Any

def to_ocsf(event_dict: dict[str, Any]) -> dict[str, Any]:
    """Adapts internal canonical format to OCSF"""
    ocsf = {
        "metadata": {
            "version": "1.1.0",
            "uid": event_dict.get("event_id"),
        },
        "time": event_dict.get("event_time"),
        "observables": []
    }
    
    source = event_dict.get("source", {})
    if "ip" in source:
        ocsf["src_endpoint"] = {"ip": source["ip"]}
        
    network = event_dict.get("network", {})
    if "port" in network:
        if "src_endpoint" not in ocsf:
            ocsf["src_endpoint"] = {}
        ocsf["src_endpoint"]["port"] = network["port"]
        
    security = event_dict.get("security", {})
    if "action" in security:
        ocsf["action"] = security["action"]
        
    if "user" in source:
        ocsf["user"] = {"name": source["user"]}
        
    ocsf["unmapped"] = event_dict.get("unmapped_fields", {})
    ocsf["raw_data"] = event_dict.get("raw_reference", {})
    
    return ocsf
