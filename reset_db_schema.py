from database import engine
from sqlalchemy import text

print("[DB] Dropping old tables to recreate with new 3-role schema...")
try:
    with engine.connect() as con:
        con.execute(text("DROP TABLE IF EXISTS reports;"))
        con.execute(text("DROP TABLE IF EXISTS users;"))
        con.commit()
    print("[DB] Successfully dropped old tables!")
except Exception as e:
    print(f"[DB Error] Failed to drop tables: {e}")
