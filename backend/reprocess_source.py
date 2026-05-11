"""Manually reprocess a source."""
import asyncio
import sys
from sqlalchemy import select
from app.database import async_session
from app.models.source import Source
from app.services.ingest import process_source


async def reprocess_source(source_id: int):
    """Reprocess a specific source."""
    async with async_session() as db:
        # Check if source exists
        result = await db.execute(select(Source).where(Source.id == source_id))
        source = result.scalar_one_or_none()
        
        if not source:
            print(f"❌ Source {source_id} not found!")
            return
        
        print(f"📄 Source: {source.name}")
        print(f"   Current status: {source.status}")
        print(f"   Type: {source.source_type}/{source.file_type}")
        print(f"   Text length: {len(source.content_text) if source.content_text else 0}")
        
        # Reset status
        source.status = "uploaded"
        await db.commit()
        print(f"\n🔄 Reprocessing source {source_id}...")
        
        try:
            await process_source(source_id, db)
            print(f"✅ Processing completed!")
            
            # Check final status
            await db.refresh(source)
            print(f"   Final status: {source.status}")
        except Exception as e:
            print(f"❌ Processing failed: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python reprocess_source.py <source_id>")
        print("\nExample: python reprocess_source.py 4")
        sys.exit(1)
    
    source_id = int(sys.argv[1])
    asyncio.run(reprocess_source(source_id))
