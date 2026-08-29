CORE_FIELDS = [
    # Metadata
    {"name": "metadata.trace_id", "type": "text", "description": "Unique trace identifier"},
    {"name": "metadata.schema_version", "type": "text", "description": "Schema version string"},
    {"name": "metadata.mapping_version", "type": "numeric", "description": "Mapping version number"},
    {"name": "metadata.product.vendor", "type": "text", "description": "Vendor name"},
    {"name": "metadata.product.name", "type": "text", "description": "Product name"},
    
    # Time
    {"name": "time.event_time_utc", "type": "timestamp", "description": "Event timestamp normalized to UTC ISO-8601"},
    {"name": "time.event_time_original", "type": "text", "description": "Original event timestamp string"},
    {"name": "time.timezone", "type": "text", "description": "Detected timezone"},
    
    # Source
    {"name": "source.ip", "type": "ipv4", "description": "Originating source IP address"},
    {"name": "source.port", "type": "numeric", "description": "Originating source port"},
    {"name": "source.hostname", "type": "hostname", "description": "Originating source hostname"},
    {"name": "source.user", "type": "username", "description": "Originating source username"},
    {"name": "source.mac", "type": "mac", "description": "Originating source MAC address"},
    
    # Destination
    {"name": "destination.ip", "type": "ipv4", "description": "Target destination IP address"},
    {"name": "destination.port", "type": "numeric", "description": "Target destination port"},
    {"name": "destination.hostname", "type": "hostname", "description": "Target destination hostname"},
    
    # Network
    {"name": "network.protocol", "type": "protocol", "description": "Network protocol name"},
    {"name": "network.direction", "type": "text", "description": "Network direction"},
    {"name": "network.bytes", "type": "numeric", "description": "Total network bytes"},
    {"name": "network.packets", "type": "numeric", "description": "Total network packets"},
    
    # Event
    {"name": "event.category", "type": "text", "description": "Event category"},
    {"name": "event.class", "type": "text", "description": "Event class"},
    {"name": "event.action", "type": "action", "description": "Normalized event action"},
    {"name": "event.outcome", "type": "text", "description": "Event outcome"},
    {"name": "event.severity", "type": "severity", "description": "Normalized event severity"},
    
    # Device
    {"name": "device.hostname", "type": "hostname", "description": "Reporting device hostname"},
    {"name": "device.ip", "type": "ipv4", "description": "Reporting device IP address"},
    {"name": "device.type", "type": "text", "description": "Reporting device type"},
    
    # Observer
    {"name": "observer.source_id", "type": "text", "description": "Observer source identity"},
    {"name": "observer.transport", "type": "text", "description": "Observer transport mechanism"},
    {"name": "observer.peer", "type": "text", "description": "Observer remote peer address"},
]

def get_core_field(name: str):
    for f in CORE_FIELDS:
        if f["name"] == name:
            return f
    return None
