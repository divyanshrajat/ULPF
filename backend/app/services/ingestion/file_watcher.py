import asyncio
import json
import logging
import os

import aiofiles
from watchfiles import Change, awatch

from app.core.database import SessionLocal
from app.services.ingestion.gateway import process_ingestion

logger = logging.getLogger(__name__)

OFFSETS_FILE = "watcher_offsets.json"

def load_offsets(directory: str) -> dict:
    path = os.path.join(directory, OFFSETS_FILE)
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_offsets(directory: str, offsets: dict):
    path = os.path.join(directory, OFFSETS_FILE)
    try:
        with open(path, "w") as f:
            json.dump(offsets, f)
    except Exception as e:
        logger.error(f"Failed to save offsets: {e}")

async def process_file(file_path: str, source_id: str, mode: str, directory: str, offsets: dict):
    db = SessionLocal()
    try:
        file_size = os.path.getsize(file_path)
        offset = offsets.get(file_path, 0) if mode == "grow" else 0
        
        if mode == "grow" and file_size < offset:
            # File was truncated/rotated
            offset = 0

        async with aiofiles.open(file_path, mode='rb') as f:
            if offset > 0:
                await f.seek(offset)
            
            content = await f.read()
            if not content:
                return

            # Handle partial lines by finding the last newline
            last_newline = content.rfind(b'\n')
            if last_newline == -1:
                # No complete line found, don't update offset and wait for more data
                return
                
            valid_content = content[:last_newline + 1]
            new_offset = offset + len(valid_content)
            
            lines = valid_content.splitlines()
            for line in lines:
                if not line.strip():
                    continue
                await process_ingestion(
                    db=db,
                    source_id=source_id,
                    payload=line,
                    transport="file",
                    peer="localhost"
                )
            
            if mode == "grow":
                offsets[file_path] = new_offset
                save_offsets(directory, offsets)
        
        if mode == "drop" and new_offset == file_size:
            os.remove(file_path)

    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}")
    finally:
        db.close()

async def watch_directory(directory: str, source_id: str, mode: str = "drop"):
    logger.info(f"Starting directory watch on {directory} for source {source_id} (mode={mode})")
    os.makedirs(directory, exist_ok=True)
    
    offsets = load_offsets(directory) if mode == "grow" else {}
    
    # Process existing files first
    for filename in os.listdir(directory):
        if filename == OFFSETS_FILE:
            continue
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            await process_file(file_path, source_id, mode, directory, offsets)
            
    # Watch for new files
    async for changes in awatch(directory):
        for change, path in changes:
            if os.path.basename(path) == OFFSETS_FILE:
                continue
            if change in (Change.added, Change.modified):
                await asyncio.sleep(0.5) 
                await process_file(path, source_id, mode, directory, offsets)
