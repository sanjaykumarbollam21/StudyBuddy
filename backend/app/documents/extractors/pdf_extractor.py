import io
import re
from typing import List
import pypdf
from app.documents.extractors.base import BaseExtractor, ExtractedDocument, ExtractedPage, ExtractedSection

class PDFExtractor(BaseExtractor):
    def extract(self, content: bytes, filename: str = "") -> ExtractedDocument:
        try:
            reader = pypdf.PdfReader(io.BytesIO(content))
        except Exception as e:
            raise ValueError(f"Corrupted or invalid PDF file: {str(e)}")

        pages: List[ExtractedPage] = []
        full_text_parts: List[str] = []
        sections: List[ExtractedSection] = []
        char_cursor = 0

        total_pages = len(reader.pages)
        if total_pages == 0:
            return ExtractedDocument(text="", page_count=0, needs_ocr=True)

        total_extracted_chars = 0

        for page_idx, page in enumerate(reader.pages):
            page_num = page_idx + 1
            raw_page_text = page.extract_text() or ""
            clean_page_text = raw_page_text.strip()
            total_extracted_chars += len(clean_page_text)

            pages.append(ExtractedPage(page_number=page_num, text=clean_page_text))

            # Detect headings on page (e.g., lines starting with capital letters or Chapter/Section)
            lines = clean_page_text.splitlines()
            for line in lines:
                stripped_line = line.strip()
                if (
                    re.match(r"^(Chapter|Section|Unit|Part)\s+\d+", stripped_line, re.IGNORECASE)
                    or (len(stripped_line) < 60 and stripped_line.isupper() and len(stripped_line) > 4)
                ):
                    sections.append(
                        ExtractedSection(
                            title=stripped_line,
                            level=1 if "chapter" in stripped_line.lower() or "unit" in stripped_line.lower() else 2,
                            page_number=page_num,
                            character_start=char_cursor,
                        )
                    )

            if clean_page_text:
                full_text_parts.append(f"--- Page {page_num} ---\n{clean_page_text}")
                char_cursor += len(clean_page_text) + 20

        # Check if PDF contains practically no extractable text (scanned document)
        needs_ocr = total_extracted_chars < 20

        joined_text = "\n\n".join(full_text_parts)
        if needs_ocr and not joined_text:
            joined_text = "[Scanned document detected. This document contains images with no selectable text and requires OCR in future version.]"

        return ExtractedDocument(
            text=joined_text,
            pages=pages,
            sections=sections,
            metadata={"total_pages": total_pages, "extractor": "pypdf"},
            needs_ocr=needs_ocr,
            page_count=max(1, total_pages),
        )
