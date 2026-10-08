import re
from typing import List
from app.documents.extractors.base import BaseExtractor, ExtractedDocument, ExtractedPage, ExtractedSection

class MarkdownExtractor(BaseExtractor):
    def extract(self, content: bytes, filename: str = "") -> ExtractedDocument:
        try:
            raw_text = content.decode("utf-8")
        except UnicodeDecodeError:
            raw_text = content.decode("latin-1", errors="ignore")

        normalized_text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
        lines = normalized_text.splitlines()

        sections: List[ExtractedSection] = []
        char_cursor = 0

        # Detect markdown headings
        for line in lines:
            heading_match = re.match(r"^(#{1,6})\s+(.*)$", line.strip())
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                sections.append(
                    ExtractedSection(
                        title=title,
                        level=level,
                        character_start=char_cursor,
                    )
                )
            char_cursor += len(line) + 1

        full_text = normalized_text.strip()
        estimated_pages = max(1, len(full_text) // 1500 + (1 if len(full_text) % 1500 else 0))

        pages = [
            ExtractedPage(page_number=i + 1, text=full_text[i * 1500 : (i + 1) * 1500])
            for i in range(estimated_pages)
        ]

        return ExtractedDocument(
            text=full_text,
            pages=pages,
            sections=sections,
            metadata={"headings_count": len(sections), "extractor": "markdown"},
            needs_ocr=False,
            page_count=estimated_pages,
        )
