import asyncio
import hashlib
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db, async_session
from app.models.source import Source
from app.schemas.source import SourceOut, LinkCreate
from app.services.ingest import process_source

router = APIRouter(prefix="/api/sources", tags=["sources"])


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}


@router.get("", response_model=list[SourceOut])
async def list_sources(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Source).order_by(Source.created_at.desc()))
    return result.scalars().all()


@router.post("/upload", response_model=SourceOut)
async def upload_file(
    bg: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: {ext}")

    content = await file.read()
    if len(content) > settings.max_upload_size:
        raise HTTPException(400, "File too large")

    content_hash = _sha256(content)
    save_path = settings.upload_dir / f"{content_hash}.{ext}"
    save_path.write_bytes(content)

    source = Source(
        name=file.filename or "unknown",
        source_type="document",
        file_type=ext,
        file_size=len(content),
        file_path=str(save_path),
        content_hash=content_hash,
        status="uploaded",
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)

    async def _bg_parse(sid: int):
        async with async_session() as session:
            await process_source(sid, session)

    bg.add_task(_bg_parse, source.id)
    return source


@router.post("/link", response_model=SourceOut)
async def add_link(
    bg: BackgroundTasks,
    body: LinkCreate,
    db: AsyncSession = Depends(get_db),
):
    source = Source(
        name=body.name,
        source_type="link",
        file_type="url",
        url=body.url,
        status="uploaded",
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)

    async def _bg_parse(sid: int):
        async with async_session() as session:
            await process_source(sid, session)

    bg.add_task(_bg_parse, source.id)
    return source


@router.get("/{source_id}/content")
async def get_source_content(source_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(404, "Source not found")
    return {"name": source.name, "content_text": source.content_text}


@router.delete("/{source_id}")
async def delete_source(source_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(404, "Source not found")

    # Delete file if exists
    if source.file_path:
        p = Path(source.file_path)
        if p.exists():
            p.unlink()

    await db.delete(source)
    await db.commit()
    return {"ok": True}
