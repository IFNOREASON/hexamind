"""Quick check database connection."""
import asyncio
from sqlalchemy import text
from app.database import engine


async def test():
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("✓ Database connection OK!")
            
            result = await conn.execute(text("""
                SELECT id, name, status, LENGTH(content_text) as text_len
                FROM sources
                ORDER BY id DESC
                LIMIT 10
            """))
            rows = result.fetchall()
            
            print(f"\nFound {len(rows)} sources:")
            print(f"{'ID':<5} {'Status':<15} {'Text Len':<10} Name")
            print("-" * 60)
            for row in rows:
                print(f"{row[0]:<5} {row[2]:<15} {row[3]:<10} {row[1]}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test())
