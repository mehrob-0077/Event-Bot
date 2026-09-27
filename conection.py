import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()
ps = os.getenv("PASSWORD_DB")

async def connection():
    try:
        conn = await asyncpg.connect(
            port=5432,
            host="localhost",
            user="postgres",
            database="exam-3_bot",
            password=ps
        )
        print("Connection Successful")
        return conn

    except Exception as error:
        print(f"Connection Error: {error}")

async def create_table():
    conn = await connection()
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                events_id SERIAL PRIMARY KEY,
                title VARCHAR(100) NOT NULL,
                capacity INT NOT NULL CHECK(capacity >= 0),
                event_date TIMESTAMP
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                registrations_id SERIAL PRIMARY KEY,
                telegram_id  BIGINT NOT NULL,
                event_id INT REFERENCES events(events_id),
                status VARCHAR(20) NOT NULL,
                registered_at TIMESTAMP DEFAULT NOW()
            );
        """)
        print("Tables Created!")

    except Exception as error:
        print(f"Create table error: {error}")

    finally:
        await conn.close()
        print("Connection OK")