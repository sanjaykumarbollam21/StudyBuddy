import re
from typing import List
from app.documents.extractors.base import ExtractedSection

class SectionDetector:
    @staticmethod
    def detect_sections(text: str) -> List[ExtractedSection]:
        if not text:
            return []

        sections: List[ExtractedSection] = []
        lines = text.splitlines()
        char_cursor = 0

        for line in lines:
            line_str = line.strip()
            # 1. Markdown headings (# Chapter 1, ## Section)
            md_match = re.match(r"^(#{1,4})\s+(.+)$", line_str)
            if md_match:
                sections.append(
                    ExtractedSection(
                        title=md_match.group(2).strip(),
                        level=len(md_match.group(1)),
                        character_start=char_cursor,
                    )
                )
            # 2. Numbered headings (e.g. "1. Introduction", "Chapter 2: Process Scheduling", "Unit 3")
            elif re.match(r"^(Chapter|Unit|Section|Part)\s+\d+[:\s\-]*(.+)?$", line_str, re.IGNORECASE):
                sections.append(
                    ExtractedSection(
                        title=line_str,
                        level=1,
                        character_start=char_cursor,
                    )
                )
            elif re.match(r"^\d+\.\d*\s+([A-Z][\w\s]{3,50})$", line_str):
                sections.append(
                    ExtractedSection(
                        title=line_str,
                        level=2,
                        character_start=char_cursor,
                    )
                )

            char_cursor += len(line) + 1

        # Populate character_end for each section
        for i in range(len(sections)):
            if i < len(sections) - 1:
                sections[i].character_end = sections[i + 1].character_start
            else:
                sections[i].character_end = len(text)

        return sections
