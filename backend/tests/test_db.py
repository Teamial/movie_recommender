# test_db_connection.py
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

# Try to connect
try:
    engine = create_engine(os.getenv("DATABASE_URL"))
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        print("✅ Database connected successfully!")
        print(f"PostgreSQL version: {result.fetchone()[0]}")
except Exception as e:
    print(f"❌ Connection failed: {e}")