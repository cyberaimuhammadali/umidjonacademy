import logging
from typing import Any

import aiosqlite


logger = logging.getLogger(__name__)


class Database:
    def __init__(self, path: str) -> None:
        self.path = path

    async def _execute(self, query: str, params: tuple[Any, ...] = ()) -> None:
        try:
            async with aiosqlite.connect(self.path) as db:
                await db.execute(query, params)
                await db.commit()
        except Exception:
            logger.exception("Database execute failed: %s", query)
            raise

    async def _fetchone(self, query: str, params: tuple[Any, ...] = ()) -> aiosqlite.Row | None:
        try:
            async with aiosqlite.connect(self.path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(query, params) as cursor:
                    return await cursor.fetchone()
        except Exception:
            logger.exception("Database fetchone failed: %s", query)
            raise

    async def _fetchall(self, query: str, params: tuple[Any, ...] = ()) -> list[aiosqlite.Row]:
        try:
            async with aiosqlite.connect(self.path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(query, params) as cursor:
                    rows = await cursor.fetchall()
                    return list(rows)
        except Exception:
            logger.exception("Database fetchall failed: %s", query)
            raise

    async def init(self) -> None:
        schema = """
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id BIGINT UNIQUE,
            language TEXT DEFAULT 'uz',
            level TEXT,
            current_subject TEXT,
            current_lesson INTEGER DEFAULT 1,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT,
            level TEXT,
            lesson_number INTEGER,
            video_file_id TEXT UNIQUE,
            title TEXT,
            added_by_admin INTEGER,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS quiz (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_id INTEGER REFERENCES lessons(id) ON DELETE CASCADE,
            question_text TEXT,
            option_a TEXT,
            option_b TEXT,
            option_c TEXT,
            option_d TEXT,
            correct_option TEXT
        );

        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            lesson_id INTEGER,
            score INTEGER,
            passed BOOLEAN,
            attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
        CREATE INDEX IF NOT EXISTS idx_lessons_subject_level_number
            ON lessons(subject, level, lesson_number);
        """
        try:
            async with aiosqlite.connect(self.path) as db:
                await db.executescript(schema)
                await db.commit()
        except Exception:
            logger.exception("Database initialization failed")
            raise

    async def get_user_by_telegram_id(self, telegram_id: int) -> dict[str, Any] | None:
        row = await self._fetchone(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,),
        )
        return dict(row) if row else None

    async def create_user(self, telegram_id: int, language: str | None = None) -> None:
        await self._execute(
            """
            INSERT OR IGNORE INTO users(telegram_id, language)
            VALUES(?, COALESCE(?, 'uz'))
            """,
            (telegram_id, language),
        )

    async def update_user_language(self, telegram_id: int, language: str) -> None:
        await self._execute(
            "UPDATE users SET language = ? WHERE telegram_id = ?",
            (language, telegram_id),
        )

    async def update_user_level(self, telegram_id: int, level: str) -> None:
        await self._execute(
            "UPDATE users SET level = ?, current_lesson = 1 WHERE telegram_id = ?",
            (level, telegram_id),
        )

    async def update_user_subject(self, telegram_id: int, subject: str) -> None:
        await self._execute(
            "UPDATE users SET current_subject = ?, current_lesson = 1 WHERE telegram_id = ?",
            (subject, telegram_id),
        )

    async def get_current_lesson(self, subject: str, level: str, lesson_number: int) -> dict[str, Any] | None:
        row = await self._fetchone(
            """
            SELECT * FROM lessons
            WHERE subject = ? AND level = ? AND lesson_number = ?
            """,
            (subject, level, lesson_number),
        )
        return dict(row) if row else None

    async def add_lesson(
        self,
        subject: str,
        level: str,
        lesson_number: int,
        video_file_id: str,
        title: str,
        added_by_admin: int,
    ) -> int:
        try:
            async with aiosqlite.connect(self.path) as db:
                cursor = await db.execute(
                    """
                    INSERT INTO lessons(subject, level, lesson_number, video_file_id, title, added_by_admin)
                    VALUES(?, ?, ?, ?, ?, ?)
                    """,
                    (subject, level, lesson_number, video_file_id, title, added_by_admin),
                )
                await db.commit()
                return int(cursor.lastrowid)
        except Exception:
            logger.exception("Failed to add lesson")
            raise

    async def get_lesson_by_id(self, lesson_id: int) -> dict[str, Any] | None:
        row = await self._fetchone("SELECT * FROM lessons WHERE id = ?", (lesson_id,))
        return dict(row) if row else None

    async def save_quiz_questions(self, lesson_id: int, questions: list[dict[str, Any]]) -> int:
        try:
            async with aiosqlite.connect(self.path) as db:
                await db.execute("DELETE FROM quiz WHERE lesson_id = ?", (lesson_id,))
                for q in questions:
                    await db.execute(
                        """
                        INSERT INTO quiz(
                            lesson_id, question_text, option_a, option_b, option_c, option_d, correct_option
                        )
                        VALUES(?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            lesson_id,
                            q["question_text"],
                            q["option_a"],
                            q["option_b"],
                            q["option_c"],
                            q["option_d"],
                            q["correct_option"].lower(),
                        ),
                    )
                await db.commit()
                return len(questions)
        except Exception:
            logger.exception("Failed to save quiz questions for lesson %s", lesson_id)
            raise

    async def get_quiz_by_lesson(self, lesson_id: int) -> list[dict[str, Any]]:
        rows = await self._fetchall(
            "SELECT * FROM quiz WHERE lesson_id = ? ORDER BY id ASC",
            (lesson_id,),
        )
        return [dict(row) for row in rows]

    async def record_quiz_result(self, user_id: int, lesson_id: int, score: int, passed: bool) -> None:
        await self._execute(
            """
            INSERT INTO quiz_results(user_id, lesson_id, score, passed)
            VALUES(?, ?, ?, ?)
            """,
            (user_id, lesson_id, score, int(passed)),
        )

    async def increment_user_lesson(self, telegram_id: int) -> None:
        await self._execute(
            """
            UPDATE users
            SET current_lesson = current_lesson + 1
            WHERE telegram_id = ?
            """,
            (telegram_id,),
        )

    async def users_count(self) -> int:
        row = await self._fetchone("SELECT COUNT(*) as cnt FROM users")
        return int(row["cnt"]) if row else 0

    async def popular_subjects(self, limit: int = 5) -> list[tuple[str, int]]:
        rows = await self._fetchall(
            """
            SELECT current_subject as subject, COUNT(*) as cnt
            FROM users
            WHERE current_subject IS NOT NULL AND current_subject != ''
            GROUP BY current_subject
            ORDER BY cnt DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [(str(row["subject"]), int(row["cnt"])) for row in rows]

    async def all_user_telegram_ids(self) -> list[int]:
        rows = await self._fetchall("SELECT telegram_id FROM users")
        return [int(row["telegram_id"]) for row in rows]
