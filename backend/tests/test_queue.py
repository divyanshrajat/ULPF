import pytest
import asyncio
from app.core.queue import InMemoryEventQueue

@pytest.mark.asyncio
async def test_in_memory_event_queue():
    queue = InMemoryEventQueue(maxsize=10)
    assert queue.depth() == 0
    
    # Test publish
    await queue.publish({"test": "event1"})
    await queue.publish({"test": "event2"})
    assert queue.depth() == 2
    
    # Test consume
    event1 = await queue.consume()
    assert event1 == {"test": "event1"}
    
    # Test depth before ack
    assert queue.depth() == 1
    
    # Test ack
    queue.ack(event1)
    
    event2 = await queue.consume()
    assert event2 == {"test": "event2"}
    
    # Test reject
    queue.reject(event2)
    
    assert queue.depth() == 0
