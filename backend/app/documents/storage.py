import os
import re
import uuid
from abc import ABC, abstractmethod
from typing import Tuple

class StorageProvider(ABC):
    @abstractmethod
    def save_file(self, user_id: str, filename: str, content: bytes) -> Tuple[str, str]:
        """Saves content and returns (safe_stored_filename, absolute_storage_path)"""
        pass

    @abstractmethod
    def read_file(self, storage_path: str) -> bytes:
        """Reads file content from storage path"""
        pass

    @abstractmethod
    def delete_file(self, storage_path: str) -> bool:
        """Deletes file from storage path"""
        pass

class LocalStorageProvider(StorageProvider):
    def __init__(self, base_dir: str = "./storage"):
        self.base_dir = os.path.abspath(base_dir)

    def _sanitize_filename(self, filename: str) -> str:
        # Strip directory traversal characters and unsafe symbols
        clean_name = os.path.basename(filename)
        clean_name = re.sub(r"[^\w\-.]", "_", clean_name)
        if not clean_name or clean_name.startswith("."):
            clean_name = f"document_{uuid.uuid4().hex[:8]}"
        return clean_name

    def save_file(self, user_id: str, filename: str, content: bytes) -> Tuple[str, str]:
        # Path traversal protection: ensure user_dir stays strictly inside base_dir
        clean_user_id = re.sub(r"[^\w\-]", "", user_id)
        user_doc_dir = os.path.abspath(os.path.join(self.base_dir, "users", clean_user_id, "documents"))
        
        # Verify user_doc_dir starts with self.base_dir
        if not user_doc_dir.startswith(self.base_dir):
            raise ValueError("Invalid storage directory path traversal attempt.")
        
        os.makedirs(user_doc_dir, exist_ok=True)

        clean_filename = self._sanitize_filename(filename)
        safe_stored_filename = f"{uuid.uuid4().hex[:8]}_{clean_filename}"
        storage_path = os.path.join(user_doc_dir, safe_stored_filename)

        with open(storage_path, "wb") as f:
            f.write(content)

        return safe_stored_filename, storage_path

    def read_file(self, storage_path: str) -> bytes:
        if not os.path.exists(storage_path):
            raise FileNotFoundError(f"Storage file not found: {storage_path}")
        with open(storage_path, "rb") as f:
            return f.read()

    def delete_file(self, storage_path: str) -> bool:
        if os.path.exists(storage_path):
            try:
                os.remove(storage_path)
                return True
            except Exception:
                return False
        return False

class SupabaseStorageProvider(StorageProvider):
    """
    Cloud storage provider using Supabase Storage REST API.
    Falls back to local storage if offline or network is unavailable.
    """
    def __init__(self, supabase_url: str, service_role_key: str, bucket_name: str = "study-materials"):
        self.supabase_url = supabase_url.rstrip("/")
        self.service_role_key = service_role_key
        self.bucket_name = bucket_name
        self.local_fallback = LocalStorageProvider()

    def _get_headers(self, content_type: str = "application/octet-stream") -> dict:
        return {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}",
            "Content-Type": content_type,
        }

    def save_file(self, user_id: str, filename: str, content: bytes) -> Tuple[str, str]:
        import urllib.request
        clean_user = re.sub(r"[^\w\-]", "", user_id)
        clean_name = re.sub(r"[^\w\-.]", "_", os.path.basename(filename))
        object_key = f"{clean_user}/{uuid.uuid4().hex[:8]}_{clean_name}"
        
        # Also persist locally for offline resilience and fast access
        local_name, local_path = self.local_fallback.save_file(user_id, filename, content)

        if not self.supabase_url or not self.service_role_key:
            return local_name, local_path

        try:
            url = f"{self.supabase_url}/storage/v1/object/{self.bucket_name}/{object_key}"
            headers = self._get_headers()
            req = urllib.request.Request(url, data=content, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status in (200, 201):
                    # Return cloud object reference key
                    return f"supabase://{self.bucket_name}/{object_key}", local_path
        except Exception:
            # Resilient fallback to local storage
            pass
        return local_name, local_path

    def read_file(self, storage_path: str) -> bytes:
        import urllib.request
        # Check local path first for zero-latency retrieval
        if os.path.exists(storage_path):
            return self.local_fallback.read_file(storage_path)

        if storage_path.startswith("supabase://"):
            parts = storage_path.replace("supabase://", "").split("/", 1)
            if len(parts) == 2:
                bucket, obj_key = parts
                try:
                    url = f"{self.supabase_url}/storage/v1/object/{bucket}/{obj_key}"
                    req = urllib.request.Request(url, headers=self._get_headers())
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        if resp.status == 200:
                            return resp.read()
                except Exception:
                    pass

        return self.local_fallback.read_file(storage_path)

    def delete_file(self, storage_path: str) -> bool:
        import urllib.request
        import json
        local_deleted = self.local_fallback.delete_file(storage_path)

        if storage_path.startswith("supabase://"):
            parts = storage_path.replace("supabase://", "").split("/", 1)
            if len(parts) == 2:
                bucket, obj_key = parts
                try:
                    url = f"{self.supabase_url}/storage/v1/object/{bucket}"
                    headers = self._get_headers("application/json")
                    payload = json.dumps({"prefixes": [obj_key]}).encode("utf-8")
                    req = urllib.request.Request(url, data=payload, headers=headers, method="DELETE")
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        return resp.status == 200
                except Exception:
                    pass

        return local_deleted

def get_storage_provider() -> StorageProvider:
    from app.core.config import settings
    if settings.STORAGE_TYPE == "supabase" and settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
        return SupabaseStorageProvider(
            supabase_url=settings.SUPABASE_URL,
            service_role_key=settings.SUPABASE_SERVICE_ROLE_KEY,
            bucket_name=settings.SUPABASE_BUCKET,
        )
    return LocalStorageProvider()

# Global storage instance
storage_service = get_storage_provider()
