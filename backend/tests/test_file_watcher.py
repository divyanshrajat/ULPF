import pytest
import os
import json
import asyncio
from app.services.ingestion.file_watcher import process_file

class MockDB:
    def close(self):
        pass

class MockProcessIngestion:
    def __init__(self):
        self.calls = []
    
    async def __call__(self, db, source_id, payload, transport, peer):
        self.calls.append(payload)

@pytest.fixture
def mock_gateway(monkeypatch):
    mock = MockProcessIngestion()
    monkeypatch.setattr("app.services.ingestion.file_watcher.process_ingestion", mock)
    monkeypatch.setattr("app.services.ingestion.file_watcher.SessionLocal", lambda: MockDB())
    return mock

@pytest.mark.asyncio
async def test_process_file_drop(tmp_path, mock_gateway):
    file_path = tmp_path / "test_drop.log"
    file_path.write_bytes(b"line1\nline2\n")
    
    await process_file(str(file_path), "SRC1", "drop", str(tmp_path), {})
    
    assert not file_path.exists()
    assert len(mock_gateway.calls) == 2
    assert mock_gateway.calls[0] == b"line1"
    assert mock_gateway.calls[1] == b"line2"

@pytest.mark.asyncio
async def test_process_file_grow(tmp_path, mock_gateway):
    file_path = tmp_path / "test_grow.log"
    file_path.write_bytes(b"line1\nline2\n")
    
    offsets = {}
    await process_file(str(file_path), "SRC1", "grow", str(tmp_path), offsets)
    
    assert file_path.exists()
    assert len(mock_gateway.calls) == 2
    assert offsets[str(file_path)] == 12 # "line1\nline2\n" length
    
    # Append to file
    with open(file_path, "ab") as f:
        f.write(b"line3\n")
        
    await process_file(str(file_path), "SRC1", "grow", str(tmp_path), offsets)
    assert len(mock_gateway.calls) == 3
    assert mock_gateway.calls[2] == b"line3"

@pytest.mark.asyncio
async def test_process_file_partial_line(tmp_path, mock_gateway):
    file_path = tmp_path / "test_partial.log"
    file_path.write_bytes(b"line1\nparti")
    
    offsets = {}
    await process_file(str(file_path), "SRC1", "grow", str(tmp_path), offsets)
    
    assert len(mock_gateway.calls) == 1
    assert mock_gateway.calls[0] == b"line1"
    
    # Complete the line
    with open(file_path, "ab") as f:
        f.write(b"al\n")
        
    await process_file(str(file_path), "SRC1", "grow", str(tmp_path), offsets)
    assert len(mock_gateway.calls) == 2
    assert mock_gateway.calls[1] == b"partial"
