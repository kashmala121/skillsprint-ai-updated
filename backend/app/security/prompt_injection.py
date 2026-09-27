"""
Step 42/43/48 (Competition Integrity #5) - Prompt Injection Defense.

Uploaded documents are always treated as DATA, never as instructions.
This module scans chunk text for adversarial patterns before it is ever
placed into a GenAI prompt, and wraps all source content in explicit
data-delimiters inside the prompt itself as a second layer of defense.
"""
import re
from typing import List, Dict

INJECTION_PATTERNS = [
    r"ignore (all|any|previous|prior) instructions",
    r"disregard (all|any|previous|prior) (instructions|rules)",
    r"you are now",
    r"system prompt",
    r"act as (an? )?(admin|administrator|root|system)",
    r"approve (this|the) (employee|request|user)",
    r"grant (access|admin|approval)",
    r"reveal (the|your) (prompt|instructions|system)",
    r"override (the )?(application|system|validation) (rules?|logic)",
    r"do not (validate|verify|check)",
    r"bypass (validation|verification|security)",
    r"<\s*system\s*>",
    r"\[\s*admin\s*\]",
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def scan_text_for_injection(text: str) -> List[str]:
    """Returns list of matched suspicious phrases (evidence), empty if clean."""
    hits = []
    for pattern in COMPILED_PATTERNS:
        m = pattern.search(text)
        if m:
            hits.append(m.group(0))
    return hits


def scan_chunks(chunks: List[Dict]) -> List[Dict]:
    """
    Scans a list of document chunks. Returns adversarial flag records for any
    chunk containing suspicious embedded instructions. Does NOT remove the
    chunk (content is still valid company data) - it only flags it so that
    it is never treated as an instruction and so reviewers are alerted.
    """
    flags = []
    for chunk in chunks:
        hits = scan_text_for_injection(chunk["text"])
        if hits:
            flags.append({
                "chunk_id": chunk["chunk_id"],
                "document_id": chunk["document_id"],
                "matched_phrases": hits,
                "severity": "high" if len(hits) > 1 else "medium",
            })
    return flags


def sanitize_for_prompt(text: str) -> str:
    """
    Wraps content in explicit data delimiters and strips characters commonly
    used to break out of a prompt's data section. This does not delete
    legitimate company content - it neutralizes it as inert data.
    """
    safe_text = text.replace("```", "'''")
    return f"<<<COMPANY_DOCUMENT_DATA_START>>>\n{safe_text}\n<<<COMPANY_DOCUMENT_DATA_END>>>"
