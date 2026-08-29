import asyncio
import os
import aiofiles
from watchfiles import awatch
from app.services.ingestion.gateway import process_ingestion
from app.core.database import SessionLocal
import logging

logger = logging.getLogger(__name__)

async def process_file(file_path: str, source_id: str):
    db = SessionLocal()
    try:
        async with aiofiles.open(file_path, mode='rb') as f:
            content = await f.read()
            # For MVP, assuming one line = one event if it's text, or raw json array
            # We'll just read line by line
            lines = content.splitlines()
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
        # Optionally delete or move file after processing
        os.remove(file_path)
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}")
    finally:
        db.close()

async def watch_directory(directory: str, source_id: str):
    logger.info(f"Starting directory watch on {directory} for source {source_id}")
    os.makedirs(directory, exist_ok=True)
    
    # Process existing files first
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            await process_file(file_path, source_id)
            
    # Watch for new files
    async for changes in awatch(directory):
        for change, path in changes:
            if change.name == "added" or change.name == "modified":
                # Basic debounce: await a bit before reading to ensure write is done
                await asyncio.sleep(0.5) 
                await process_file(path, source_id)
