from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class ExtractedPage:
    page_number: int
    text: str

@dataclass
class ExtractedSection:
    title: str
    level: int = 1
    content: str = ""
    page_number: Optional[int] = None
    character_start: int = 0
    character_end: int = 0

@dataclass
class ExtractedDocument:
    text: str
    pages: List[ExtractedPage] = field(default_factory=list)
    sections: List[ExtractedSection] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    needs_ocr: bool = False
    page_count: int = 1

class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, content: bytes, filename: str = "") -> ExtractedDocument:
        """Extract structured document representation from raw file bytes."""
        pass
