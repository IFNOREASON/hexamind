"""Fix stuck sources - simple SQL approach."""
import psycopg2
import sys

# Database connection string from .env
DB_CONFIG = {
    "dbname": "hexamind",  # Database name from .env
    "user": "postgres",
    "password": "123456",
    "host": "localhost",
    "port": "5432"
}


def fix_stuck():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Find stuck sources
        cur.execute("""
            SELECT id, name, status, LENGTH(content_text) as text_len
            FROM sources
            WHERE status IN ('extracting', 'parsing')
            ORDER BY id DESC
        """)
        stuck = cur.fetchall()
        
        if not stuck:
            print("✓ No stuck sources found!")
            cur.close()
            conn.close()
            return
        
        print(f"Found {len(stuck)} stuck source(s):\n")
        for s in stuck:
            print(f"  ID: {s[0]}")
            print(f"  Name: {s[1]}")
            print(f"  Status: {s[2]}")
            print(f"  Text length: {s[3]}")
            print()
        
        # Reset to uploaded
        for s in stuck:
            cur.execute("""
                UPDATE sources
                SET status = 'uploaded'
                WHERE id = %s
            """, (s[0],))
            print(f"✓ Reset source {s[0]} to 'uploaded'")
        
        conn.commit()
        print(f"\n✓ All {len(stuck)} stuck source(s) have been reset!")
        print("\nYou can now re-upload or the system will retry on next restart.")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    fix_stuck()
