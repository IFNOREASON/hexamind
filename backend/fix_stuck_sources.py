"""Fix stuck sources by resetting their status."""
import asyncio
from sqlalchemy import text
from app.database import engine


async def fix_stuck_sources():
    """Reset stuck sources to 'uploaded' so they can be reprocessed."""
    async with engine.connect() as conn:
        # Find stuck sources
        result = await conn.execute(text("""
            SELECT id, name, status, source_type, file_type
            FROM sources
            WHERE status IN ('extracting', 'parsing')
            ORDER BY created_at DESC
        """))
        stuck = result.fetchall()
        
        if not stuck:
            print("✓ No stuck sources found!")
            return
        
        print(f"Found {len(stuck)} stuck source(s):")
        for s in stuck:
            print(f"  - ID {s[0]}: {s[1]} (status: {s[2]})")
        
        # Reset to uploaded status
        for s in stuck:
            await conn.execute(text("""
                UPDATE sources
                SET status = 'uploaded'
                WHERE id = :source_id
            """), {"source_id": s[0]})
            print(f"  ✓ Reset source {s[0]} to 'uploaded'")
        
        await conn.commit()
        print("\n✓ All stuck sources have been reset!")
        print("  You may need to restart the extraction process.")


if __name__ == "__main__":
    asyncio.run(fix_stuck_sources())
