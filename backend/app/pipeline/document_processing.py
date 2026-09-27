"""
Document Upload -> Validation -> Parsing -> Chunking pipeline.
Supports PDF and DOCX (mandatory per SRS). TXT/Markdown supported as a bonus.
Every chunk retains: document_id, chunk_id, section, heading, source location,
version, effective_date -> required for source traceability (SRS Steps 5-8).
"""
import hashlib
import re
from datetime import datetime
from typing import List, Dict

import pdfplumber
from docx import Document as DocxDocument

from ..models.schemas import new_id

MAX_FILE_SIZE_MB = 20
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


class DocumentValidationError(Exception):
    pass


def validate_file(filename: str, content: bytes) -> None:
    """Step 5: Document Validation - file type, size, empty document."""
    ext = "." + filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise DocumentValidationError(f"Unsupported file type: {ext}")
    if len(content) == 0:
        raise DocumentValidationError("Uploaded document is empty.")
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise DocumentValidationError(f"File exceeds max size of {MAX_FILE_SIZE_MB}MB.")


def compute_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def extract_pdf(content: bytes) -> List[Dict]:
    """Returns list of {page, heading, text}."""
    import io
    sections = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            if not text.strip():
                continue
            # naive heading detection: short line in Title Case / ALL CAPS at start of block
            lines = [l for l in text.split("\n") if l.strip()]
            heading = lines[0][:80] if lines else f"Page {page_num}"
            sections.append({"page": page_num, "heading": heading, "text": text})
    return sections


def extract_docx(content: bytes) -> List[Dict]:
    """Returns list of {paragraph_ref, heading, text} split by Heading styles."""
    import io
    doc = DocxDocument(io.BytesIO(content))
    sections = []
    current_heading = "Introduction"
    current_text = []
    para_index = 0
    for para in doc.paragraphs:
        para_index += 1
        style = (para.style.name or "").lower()
        if para.text.strip() == "":
            continue
        if style.startswith("heading") or style.startswith("title"):
            if current_text:
                sections.append({
                    "paragraph_ref": f"para-{para_index}",
                    "heading": current_heading,
                    "text": "\n".join(current_text),
                })
            current_heading = para.text.strip()
            current_text = []
        else:
            current_text.append(para.text.strip())
    if current_text:
        sections.append({
            "paragraph_ref": f"para-{para_index}",
            "heading": current_heading,
            "text": "\n".join(current_text),
        })
    if not sections:
        # fallback: whole doc as one section
        full_text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        sections.append({"paragraph_ref": "para-1", "heading": "Document", "text": full_text})
    return sections


def extract_plain_text(content: bytes) -> List[Dict]:
    text = content.decode("utf-8", errors="ignore")
    blocks = re.split(r"\n\s*\n", text)
    sections = []
    for i, block in enumerate(blocks, start=1):
        if block.strip():
            heading_line = block.strip().split("\n")[0][:80]
            sections.append({"paragraph_ref": f"block-{i}", "heading": heading_line, "text": block.strip()})
    return sections


def parse_document(filename: str, content: bytes) -> List[Dict]:
    """Step 6: Document Parsing - dispatches by extension."""
    ext = "." + filename.lower().rsplit(".", 1)[-1]
    if ext == ".pdf":
        return extract_pdf(content)
    elif ext == ".docx":
        return extract_docx(content)
    elif ext in (".txt", ".md"):
        return extract_plain_text(content)
    raise DocumentValidationError(f"No parser available for {ext}")


CHUNK_TARGET_CHARS = 1200


def chunk_sections(document_id: str, doc_title: str, version: str,
                    effective_date: str, sections: List[Dict]) -> List[Dict]:
    """
    Step 7: Content Chunking - splits large sections into manageable chunks
    while retaining document_id, chunk_id, section, heading and source location
    (page number for PDF, paragraph reference for DOCX) for traceability.
    """
    chunks = []
    for sec in sections:
        text = sec["text"]
        heading = sec.get("heading", "General")
        location = sec.get("page", sec.get("paragraph_ref", "N/A"))
        location_label = f"page-{location}" if "page" in sec else str(location)

        # split long section text into sub-chunks of ~CHUNK_TARGET_CHARS
        paragraphs = text.split("\n")
        buffer = ""
        part = 1
        for p in paragraphs:
            if len(buffer) + len(p) > CHUNK_TARGET_CHARS and buffer:
                chunks.append(_build_chunk(document_id, doc_title, version, effective_date,
                                            heading, location_label, part, buffer.strip()))
                part += 1
                buffer = ""
            buffer += p + "\n"
        if buffer.strip():
            chunks.append(_build_chunk(document_id, doc_title, version, effective_date,
                                        heading, location_label, part, buffer.strip()))
    return chunks


def _build_chunk(document_id, doc_title, version, effective_date, heading, location_label, part, text):
    return {
        "chunk_id": new_id("CHK"),
        "document_id": document_id,
        "document_title": doc_title,
        "version": version,
        "effective_date": effective_date,
        "section_id": f"{heading[:30]}-{part}",
        "heading": heading,
        "source_location": location_label,
        "text": text,
        "char_count": len(text),
        "created_at": datetime.utcnow().isoformat(),
    }
