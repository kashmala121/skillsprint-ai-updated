from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from datetime import datetime
from typing import Optional

from ..database import documents_col, chunks_col, adversarial_flags_col, audit_log_col
from ..auth import require_roles
from ..models.schemas import new_id
from ..pipeline.document_processing import (
    validate_file, compute_hash, parse_document, chunk_sections, DocumentValidationError
)
from ..security.prompt_injection import scan_chunks

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    doc_type: str = Form("Other"),
    department: str = Form("General"),
    version: str = Form("1.0"),
    effective_date: Optional[str] = Form(None),
    precedence_category: str = Form("Latest Approved Policy"),
    supersedes_document_id: Optional[str] = Form(None),
    user=Depends(require_roles("admin", "training_manager")),
):
    content = await file.read()
    try:
        validate_file(file.filename, content)
    except DocumentValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    file_hash = compute_hash(content)
    duplicate = await documents_col.find_one({"file_hash": file_hash})
    if duplicate:
        raise HTTPException(status_code=409, detail=f"Duplicate document already uploaded: {duplicate['document_id']}")

    document_id = new_id("DOC")

    # If this supersedes an existing document, mark the old one obsolete (Step 8: version control)
    if supersedes_document_id:
        await documents_col.update_one(
            {"document_id": supersedes_document_id}, {"$set": {"status": "obsolete"}}
        )

    try:
        sections = parse_document(file.filename, content)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse document: {e}")

    doc_record = {
        "document_id": document_id,
        "title": title,
        "filename": file.filename,
        "doc_type": doc_type,
        "department": department,
        "version": version,
        "effective_date": effective_date,
        "precedence_category": precedence_category,
        "supersedes_document_id": supersedes_document_id,
        "file_hash": file_hash,
        "status": "active",
        "uploaded_by": user["username"],
        "uploaded_at": datetime.utcnow().isoformat(),
    }
    await documents_col.insert_one(doc_record)

    chunks = chunk_sections(document_id, title, version, effective_date or "", sections)
    if chunks:
        await chunks_col.insert_many(chunks)

    # Step 42/43 - scan for prompt injection / adversarial content
    flags = scan_chunks(chunks)
    if flags:
        for f in flags:
            f["document_id"] = document_id
            f["flagged_at"] = datetime.utcnow().isoformat()
        await adversarial_flags_col.insert_many(flags)

    await audit_log_col.insert_one({
        "action": "document_upload", "document_id": document_id,
        "user": user["username"], "timestamp": datetime.utcnow().isoformat(),
        "chunk_count": len(chunks), "adversarial_flags": len(flags),
    })

    doc_record.pop("_id", None)
    return {
        "document": doc_record,
        "chunk_count": len(chunks),
        "adversarial_flags_found": len(flags),
        "adversarial_flags": flags,
    }


@router.get("/")
async def list_documents(user=Depends(require_roles("admin", "training_manager", "reviewer"))):
    docs = await documents_col.find({}, {"_id": 0}).to_list(length=1000)
    return docs


@router.get("/{document_id}/chunks")
async def get_document_chunks(document_id: str, user=Depends(require_roles("admin", "training_manager", "reviewer"))):
    chunks = await chunks_col.find({"document_id": document_id}, {"_id": 0}).to_list(length=5000)
    return chunks


@router.get("/adversarial-flags")
async def list_adversarial_flags(user=Depends(require_roles("admin", "training_manager", "reviewer"))):
    flags = await adversarial_flags_col.find({}, {"_id": 0}).to_list(length=1000)
    return flags


@router.delete("/{document_id}")
async def delete_document(document_id: str, user=Depends(require_roles("admin"))):
    await documents_col.delete_one({"document_id": document_id})
    await chunks_col.delete_many({"document_id": document_id})
    return {"message": f"Document {document_id} and its chunks deleted"}
