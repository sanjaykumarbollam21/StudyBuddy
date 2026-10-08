from app.documents.extractors.base import BaseExtractor, ExtractedDocument, ExtractedPage, ExtractedSection
from app.documents.extractors.pdf_extractor import PDFExtractor
from app.documents.extractors.docx_extractor import DOCXExtractor
from app.documents.extractors.txt_extractor import TXTExtractor
from app.documents.extractors.markdown_extractor import MarkdownExtractor

SUPPORTED_EXTENSIONS = {"pdf", "docx", "txt", "md", "markdown"}
FUTURE_EXTENSIONS = {"ppt", "pptx", "csv", "png", "jpg", "jpeg", "webp"}

def get_extractor(file_extension: str) -> BaseExtractor:
    ext = file_extension.lower().lstrip(".")
    if ext == "pdf":
        return PDFExtractor()
    elif ext in ["docx", "doc"]:
        return DOCXExtractor()
    elif ext == "txt":
        return TXTExtractor()
    elif ext in ["md", "markdown"]:
        return MarkdownExtractor()
    elif ext in FUTURE_EXTENSIONS:
        raise NotImplementedError("This file type will be supported in a future version.")
    else:
        raise ValueError(f"Unsupported file format: .{ext}. Supported formats are PDF, DOCX, TXT, and Markdown.")

__all__ = [
    "BaseExtractor",
    "ExtractedDocument",
    "ExtractedPage",
    "ExtractedSection",
    "PDFExtractor",
    "DOCXExtractor",
    "TXTExtractor",
    "MarkdownExtractor",
    "get_extractor",
    "SUPPORTED_EXTENSIONS",
    "FUTURE_EXTENSIONS",
]
