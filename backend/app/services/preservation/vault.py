import os
import hashlib
import aiofiles
from datetime import datetime
from app.core.config import settings

class RawEventVault:
    def __init__(self):
        self.vault_dir = settings.VAULT_DIR
        os.makedirs(self.vault_dir, exist_ok=True)
        
    def _get_storage_path(self, source_id: str, received_at: datetime, trace_id: str) -> str:
        date_str = received_at.strftime("%Y-%m-%d")
        dir_path = os.path.join(self.vault_dir, source_id, date_str)
        os.makedirs(dir_path, exist_ok=True)
        return os.path.join(dir_path, f"{trace_id}.raw")

    async def write_event(self, trace_id: str, source_id: str, payload: bytes, received_at: datetime) -> tuple[str, str]:
        """
        Writes the raw event to the vault.
        Returns (digest, storage_uri).
        """
        digest = hashlib.sha256(payload).hexdigest()
        digest_str = f"sha256:{digest}"
        
        file_path = self._get_storage_path(source_id, received_at, trace_id)
        
        # Write-once append-only
        if os.path.exists(file_path):
            raise FileExistsError(f"Raw event {trace_id} already exists in vault.")
            
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(payload)
            
        uri = f"vault://{source_id}/{received_at.strftime('%Y-%m-%d')}/{trace_id}.raw"
        return digest_str, uri
        
    async def read_event(self, source_id: str, received_at: datetime, trace_id: str) -> bytes:
        file_path = self._get_storage_path(source_id, received_at, trace_id)
        async with aiofiles.open(file_path, "rb") as f:
            return await f.read()

    def verify_digest(self, payload: bytes, expected_digest: str) -> bool:
        digest = hashlib.sha256(payload).hexdigest()
        return expected_digest == f"sha256:{digest}"

vault = RawEventVault()
