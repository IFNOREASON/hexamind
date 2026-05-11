"""Check source processing status."""
import asyncio
from sqlalchemy import text
from app.database import engine


async def check_sources():
    """Check all sources and their status."""
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT id, name, status, source_type, file_type, 
                   LENGTH(content_text) as text_length,
                   created_at
            FROM sources
            ORDER BY created_at DESC
        """))
        rows = result.fetchall()
        
        print(f"\n{'ID':<5} {'Status':<15} {'Type':<10} {'Text Len':<10} {'Name'}")
        print("-" * 100)
        for row in rows:
            print(f"{row[0]:<5} {row[2]:<15} {row[3]:<10} {row[5]:<10} {row[1]}")
        
        # Check for stuck sources
        stuck = [r for r in rows if r[2] in ['extracting', 'parsing']]
        if stuck:
            print(f"\n⚠️  Found {len(stuck)} stuck source(s):")
            for s in stuck:
                print(f"   - Source ID {s[0]}: status='{s[2]}', name='{s[1]}'")
        
        print()


if __name__ == "__main__":
    asyncio.run(check_sources())
