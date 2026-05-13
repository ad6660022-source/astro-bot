import os
import aiosqlite
from datetime import datetime, timezone

DB_PATH = os.getenv("DB_PATH", "astro.db")


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                full_name   TEXT,
                zodiac_sign TEXT,
                birth_date  TEXT,
                sub_end     TIMESTAMP,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        for col in ("birth_date", "last_free_tarot"):
            try:
                await db.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
            except Exception:
                pass
        try:
            await db.execute("ALTER TABLE users ADD COLUMN readings_count INTEGER DEFAULT 0")
        except Exception:
            pass
        await db.execute("""
            CREATE TABLE IF NOT EXISTS horoscopes (
                date        TEXT,
                zodiac_sign TEXT,
                text        TEXT,
                PRIMARY KEY (date, zodiac_sign)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS daily_tarot (
                user_id  INTEGER,
                date     TEXT,
                text     TEXT,
                PRIMARY KEY (user_id, date)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_messages (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER,
                message     TEXT,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS token_usage (
                month          TEXT PRIMARY KEY,
                input_tokens   INTEGER DEFAULT 0,
                output_tokens  INTEGER DEFAULT 0,
                requests       INTEGER DEFAULT 0,
                free_input     INTEGER DEFAULT 0,
                free_output    INTEGER DEFAULT 0,
                free_requests  INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS support_tickets (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER,
                username   TEXT,
                full_name  TEXT,
                message    TEXT,
                answered   INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def get_user(user_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
    return dict(row) if row else None


async def create_user(user_id: int, username: str, full_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?, ?, ?)",
            (user_id, username, full_name)
        )
        await db.commit()


async def set_zodiac(user_id: int, zodiac_sign: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET zodiac_sign = ? WHERE user_id = ?",
            (zodiac_sign, user_id)
        )
        await db.commit()


async def get_free_tarot_used(user_id: int, date: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT last_free_tarot FROM users WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
    return bool(row and row[0] == date)


async def increment_readings(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET readings_count = readings_count + 1 WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()


async def mark_free_tarot_used(user_id: int, date: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET last_free_tarot = ? WHERE user_id = ?",
            (date, user_id)
        )
        await db.commit()


async def set_birth_date(user_id: int, birth_date: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET birth_date = ? WHERE user_id = ?",
            (birth_date, user_id)
        )
        await db.commit()


async def set_subscription(user_id: int, end_date: datetime):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET sub_end = ? WHERE user_id = ?",
            (end_date.isoformat(), user_id)
        )
        await db.commit()


async def get_horoscope(date: str, zodiac_sign: str) -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT text FROM horoscopes WHERE date = ? AND zodiac_sign = ?",
            (date, zodiac_sign)
        ) as cur:
            row = await cur.fetchone()
    return row[0] if row else None


async def save_horoscope(date: str, zodiac_sign: str, text: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO horoscopes (date, zodiac_sign, text) VALUES (?, ?, ?)",
            (date, zodiac_sign, text)
        )
        await db.commit()


async def get_daily_tarot(user_id: int, date: str) -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT text FROM daily_tarot WHERE user_id = ? AND date = ?",
            (user_id, date)
        ) as cur:
            row = await cur.fetchone()
    return row[0] if row else None


async def save_daily_tarot(user_id: int, date: str, text: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO daily_tarot (user_id, date, text) VALUES (?, ?, ?)",
            (user_id, date, text)
        )
        await db.commit()


async def add_user_message(user_id: int, message: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO user_messages (user_id, message) VALUES (?, ?)",
            (user_id, message)
        )
        await db.execute("""
            DELETE FROM user_messages WHERE user_id = ? AND id NOT IN (
                SELECT id FROM user_messages WHERE user_id = ? ORDER BY id DESC LIMIT 10
            )
        """, (user_id, user_id))
        await db.commit()


async def get_user_messages(user_id: int, limit: int = 5) -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT message FROM user_messages WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        ) as cur:
            rows = await cur.fetchall()
    return [r[0] for r in reversed(rows)]


async def add_token_usage(input_tokens: int, output_tokens: int, is_free: bool = False):
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO token_usage (month, input_tokens, output_tokens, requests,
                                        free_input, free_output, free_requests)
               VALUES (?, ?, ?, 1, ?, ?, ?)
               ON CONFLICT(month) DO UPDATE SET
                 input_tokens  = input_tokens  + excluded.input_tokens,
                 output_tokens = output_tokens + excluded.output_tokens,
                 requests      = requests      + 1,
                 free_input    = free_input    + excluded.free_input,
                 free_output   = free_output   + excluded.free_output,
                 free_requests = free_requests + excluded.free_requests""",
            (month, input_tokens, output_tokens,
             input_tokens if is_free else 0,
             output_tokens if is_free else 0,
             1 if is_free else 0)
        )
        await db.commit()


async def get_token_usage(month: str | None = None) -> dict:
    if month is None:
        month = datetime.now(timezone.utc).strftime("%Y-%m")
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT input_tokens, output_tokens, requests, free_input, free_output, free_requests FROM token_usage WHERE month = ?",
            (month,)
        ) as cur:
            row = await cur.fetchone()
    if not row:
        return {"input_tokens": 0, "output_tokens": 0, "requests": 0,
                "free_input": 0, "free_output": 0, "free_requests": 0, "month": month}
    return {"input_tokens": row[0], "output_tokens": row[1], "requests": row[2],
            "free_input": row[3], "free_output": row[4], "free_requests": row[5], "month": month}


async def get_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            total = (await cur.fetchone())[0]
        now = datetime.now(timezone.utc).isoformat()
        async with db.execute(
            "SELECT COUNT(*) FROM users WHERE sub_end > ?", (now,)
        ) as cur:
            active_subs = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM horoscopes") as cur:
            horoscopes_generated = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM daily_tarot") as cur:
            daily_tarots = (await cur.fetchone())[0]
    return {
        "total": total,
        "active_subs": active_subs,
        "horoscopes": horoscopes_generated,
        "daily_tarots": daily_tarots,
    }


async def get_all_user_ids() -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cur:
            rows = await cur.fetchall()
    return [r[0] for r in rows]


async def add_support_ticket(user_id: int, username: str, full_name: str, message: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO support_tickets (user_id, username, full_name, message) VALUES (?, ?, ?, ?)",
            (user_id, username, full_name, message)
        )
        await db.commit()
        return cursor.lastrowid


async def get_open_tickets(limit: int = 10) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM support_tickets WHERE answered = 0 ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ) as cur:
            rows = await cur.fetchall()
    return [dict(r) for r in rows]


async def get_closed_tickets(limit: int = 10) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM support_tickets WHERE answered = 1 ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ) as cur:
            rows = await cur.fetchall()
    return [dict(r) for r in rows]


async def get_ticket(ticket_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM support_tickets WHERE id = ?", (ticket_id,)) as cur:
            row = await cur.fetchone()
    return dict(row) if row else None


async def mark_ticket_answered(ticket_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE support_tickets SET answered = 1 WHERE id = ?", (ticket_id,))
        await db.commit()
