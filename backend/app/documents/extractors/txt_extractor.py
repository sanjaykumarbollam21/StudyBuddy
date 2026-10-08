from typing import List
from app.documents.extractors.base import BaseExtractor, ExtractedDocument, ExtractedPage, ExtractedSection

class TXTExtractor(BaseExtractor):
    def extract(self, content: bytes, filename: str = "") -> ExtractedDocument:
        # Decode utf-8 with fallback
        try:
            raw_text = content.decode("utf-8")
        except UnicodeDecodeError:
            raw_text = content.decode("latin-1", errors="ignore")

        # Normalize line endings
        normalized_text = raw_text.replace("\r\n", "\n").replace("\r", "\n")

        # Clean paragraphs
        paragraphs = [p.strip() for p in normalized_text.split("\n\n") if p.strip()]
        full_text = "\n\n".join(paragraphs)

        estimated_pages = max(1, len(full_text) // 1500 + (1 if len(full_text) % 1500 else 0))
        pages: List[ExtractedPage] = []
        for i in range(estimated_pages):
            pages.append(
                ExtractedPage(page_number=i + 1, text=full_text[i * 1500 : (i + 1) * 1500])
            )

        # Basic section detection from lines that look like headers
        sections: List[ExtractedSection] = []
        for p in paragraphs:
            if len(p) < 60 and (p.isupper() or p.startswith("Chapter ") or p.startswith("Section ")):
                sections.append(ExtractedSection(title=p, level=1))

        return ExtractedDocument(
            text=full_text,
            pages=pages,
            sections=sections,
            metadata={"paragraph_count": len(paragraphs), "extractor": "txt"},
            needs_ocr=False,
            page_count=estimated_pages,
        )
