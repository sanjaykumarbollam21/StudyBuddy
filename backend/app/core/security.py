from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional
import bcrypt
from jose import jwt
from app.core.config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against the stored bcrypt hash."""
    try:
        plain_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(plain_bytes, hash_bytes)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    """Generate bcrypt hash for a plain password."""
    plain_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain_bytes, salt).decode("utf-8")

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "iat": datetime.now(timezone.utc)
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except Exception:
        return None


# --- Production Security Hardening (Phase 10) ---

import os
import re
import time
from collections import defaultdict

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


def validate_safe_filename(filename: str) -> str:
    """
    Sanitizes filename and prevents directory traversal attacks.
    Removes path separators and .. sequences.
    """
    clean_name = os.path.basename(filename)
    clean_name = re.sub(r"[^\w\s\.-]", "", clean_name).strip()
    if not clean_name or clean_name in (".", ".."):
        raise ValueError("Invalid filename detected.")
    return clean_name


def validate_file_upload(
    filename: str,
    file_bytes: bytes,
    allowed_extensions: Optional[set] = None,
    max_size: int = MAX_FILE_SIZE,
) -> bool:
    """
    Validates file upload against size limits, path traversal, and allowed extensions.
    """
    if len(file_bytes) > max_size:
        raise ValueError(f"File size exceeds maximum limit of {max_size // (1024 * 1024)}MB.")

    safe_name = validate_safe_filename(filename)
    ext = os.path.splitext(safe_name)[1].lower()

    allowed = allowed_extensions or ALLOWED_EXTENSIONS
    if ext not in allowed:
        raise ValueError(f"Disallowed file extension '{ext}'. Allowed: {', '.join(sorted(allowed))}")

    return True


class InMemoryRateLimiter:
    """
    Lightweight sliding-window rate limiter for sensitive API routes.
    """

    def __init__(self, requests_per_minute: int = 60):
        self.limit = requests_per_minute
        self.window_seconds = 60.0
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, client_key: str) -> bool:
        now = time.time()
        cutoff = now - self.window_seconds
        # Clean older entries
        timestamps = [t for t in self._requests[client_key] if t > cutoff]
        if len(timestamps) >= self.limit:
            self._requests[client_key] = timestamps
            return False
        timestamps.append(now)
        self._requests[client_key] = timestamps
        return True


rate_limiter = InMemoryRateLimiter(requests_per_minute=120)

