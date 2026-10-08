import re
import unicodedata

class TextCleaner:
    @staticmethod
    def clean(text: str) -> str:
        if not text:
            return ""

        # 1. Normalize Unicode characters (NFKC)
        cleaned = unicodedata.normalize("NFKC", text)

        # 2. Normalize carriage returns
        cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")

        # 3. Fix hyphenated line breaks (e.g. "concur- \nrency" -> "concurrency")
        cleaned = re.sub(r"(\b\w+)-\s*\n\s*(\w+\b)", r"\1\2", cleaned)

        # 4. Collapse runs of horizontal whitespace (spaces, tabs) to a single space
        lines = cleaned.splitlines()
        normalized_lines = []
        for line in lines:
            line = re.sub(r"[ \t]+", " ", line).strip()
            normalized_lines.append(line)

        # 5. Remove repeated blank lines (keep maximum 2 newlines between paragraphs)
        rejoined = "\n".join(normalized_lines)
        cleaned = re.sub(r"\n{3,}", "\n\n", rejoined)

        # 6. Filter out recurring page footers like "Page 1 of 12"
        cleaned = re.sub(r"(?i)\bpage\s+\d+\s+of\s+\d+\b", "", cleaned)

        return cleaned.strip()
