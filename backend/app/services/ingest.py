import hashlib
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source import Source
from app.services.parsers.registry import get_parser
from app.agents.extraction_agent import run_extraction
from app.services.graph_persist import persist_extraction

logger = logging.getLogger(__name__)


async def process_source(source_id: int, db: AsyncSession) -> None:
    """Parse a source, extract text, then run knowledge graph extraction."""
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        return

    parser = get_parser(source.file_type, source.source_type)
    if not parser:
        source.status = "unsupported"
        await db.commit()
        return

    # Step 1: Parse text
    source.status = "parsing"
    await db.commit()

    try:
        text = await parser.parse(file_path=source.file_path, url=source.url)
        source.content_text = text
        source.content_hash = hashlib.sha256(text.encode()).hexdigest()
    except Exception as e:
        logger.error("Failed to parse source %d: %s", source_id, e)
        source.status = "failed"
        await db.commit()
        return

    # Step 2: Run knowledge graph extraction (LangGraph agent)
    source.status = "extracting"
    await db.commit()

    if not source.content_text or not source.content_hash:
        source.status = "parsed"
        await db.commit()
        return

    try:
        extraction_result = await run_extraction(
            source_id=source.id,
            source_type=source.source_type,
            content_text=source.content_text,
            content_hash=source.content_hash,
        )

        if extraction_result.get("error"):
            logger.warning(
                "Extraction had error for source %d: %s",
                source_id, extraction_result["error"],
            )
            # Still mark as parsed so user can see text was extracted
            source.status = "parsed"
            await db.commit()
            return

        # Step 3: Persist to database
        try:
            counts = await persist_extraction(
                nodes=extraction_result["nodes"],
                edges=extraction_result["edges"],
                hyperedges=extraction_result["hyperedges"],
                db=db,
            )
            logger.info("Source %d processed: %s", source_id, counts)
        except Exception as e:
            logger.error("Failed to persist extraction for source %d: %s", source_id, e)
            source.status = "parsed"  # Text was extracted, but graph persist failed
            await db.commit()
            return

    except Exception as e:
        logger.error("Knowledge extraction failed for source %d: %s", source_id, e)
        source.status = "failed"
        await db.commit()
        return

    # Final: mark as fully processed
    source.status = "parsed"
    await db.commit()
