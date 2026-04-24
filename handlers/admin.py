import json
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import Config
from data.texts import t
from database import Database
from handlers.states import AdminStates
from keyboards.admin import admin_menu_keyboard, yes_no_keyboard


logger = logging.getLogger(__name__)
router = Router()


def _is_admin(message_or_callback: Message | CallbackQuery, config: Config) -> bool:
    user = message_or_callback.from_user
    return bool(user and user.id == config.admin_id)


@router.message(Command("admin"))
async def admin_panel(message: Message, config: Config) -> None:
    if not _is_admin(message, config):
        await message.answer(t("en", "admin_only"))
        return
    await message.answer("Admin Panel", reply_markup=admin_menu_keyboard())


@router.callback_query(F.data == "admin:add_lesson")
async def add_lesson_start(callback: CallbackQuery, state: FSMContext, config: Config) -> None:
    if not _is_admin(callback, config):
        await callback.answer(t("en", "admin_only"), show_alert=True)
        return
    await state.set_state(AdminStates.waiting_lesson_video)
    await callback.message.answer(t("en", "send_video"))
    await callback.answer()


@router.message(AdminStates.waiting_lesson_video)
async def add_lesson_video(message: Message, state: FSMContext, config: Config) -> None:
    if not _is_admin(message, config):
        return
    if not message.video:
        await message.answer("Please send a video.")
        return
    await state.update_data(video_file_id=message.video.file_id)
    await state.set_state(AdminStates.waiting_lesson_meta)
    await message.answer(t("en", "send_lesson_meta"))


@router.message(AdminStates.waiting_lesson_meta)
async def add_lesson_meta(message: Message, state: FSMContext, db: Database, config: Config) -> None:
    if not _is_admin(message, config):
        return
    if not message.text:
        await message.answer("Metadata must be text.")
        return
    try:
        parts = [p.strip() for p in message.text.split("|")]
        if len(parts) != 4:
            await message.answer("Invalid format. Use subject|level|lesson_number|title")
            return
        subject, level, lesson_number_raw, title = parts
        lesson_number = int(lesson_number_raw)
        data = await state.get_data()
        video_file_id = str(data["video_file_id"])
        lesson_id = await db.add_lesson(
            subject=subject,
            level=level,
            lesson_number=lesson_number,
            video_file_id=video_file_id,
            title=title,
            added_by_admin=config.admin_id,
        )
        await state.clear()
        await message.answer(t("en", "lesson_saved", lesson_id=lesson_id))
        await message.answer(t("en", "offer_add_quiz"), reply_markup=yes_no_keyboard(f"admin:add_quiz:{lesson_id}"))
    except ValueError:
        await message.answer("lesson_number must be an integer.")
    except Exception:
        logger.exception("Failed to add lesson")
        await message.answer(t("en", "error"))


@router.callback_query(F.data.startswith("admin:add_quiz:"))
async def add_quiz_offer(callback: CallbackQuery, state: FSMContext, config: Config) -> None:
    if not _is_admin(callback, config) or not callback.data:
        return
    parts = callback.data.split(":")
    lesson_id = int(parts[2])
    decision = parts[3]
    if decision == "yes":
        await state.set_state(AdminStates.waiting_quiz_json)
        await state.update_data(quiz_lesson_id=lesson_id)
        await callback.message.answer(t("en", "send_quiz_json"))
    else:
        await callback.message.answer("Done.")
    await callback.answer()


@router.callback_query(F.data == "admin:add_quiz")
async def add_quiz_manual_start(callback: CallbackQuery, state: FSMContext, config: Config) -> None:
    if not _is_admin(callback, config):
        await callback.answer(t("en", "admin_only"), show_alert=True)
        return
    await state.set_state(AdminStates.waiting_quiz_lesson_id)
    await callback.message.answer(t("en", "send_quiz_lesson_id"))
    await callback.answer()


@router.message(AdminStates.waiting_quiz_lesson_id)
async def receive_quiz_lesson_id(message: Message, state: FSMContext, config: Config, db: Database) -> None:
    if not _is_admin(message, config) or not message.text:
        return
    try:
        lesson_id = int(message.text.strip())
        lesson = await db.get_lesson_by_id(lesson_id)
        if not lesson:
            await message.answer("Lesson not found.")
            return
        await state.update_data(quiz_lesson_id=lesson_id)
        await state.set_state(AdminStates.waiting_quiz_json)
        await message.answer(t("en", "send_quiz_json"))
    except ValueError:
        await message.answer("Lesson id must be integer.")


def _validate_quiz_payload(payload: list[dict]) -> list[dict]:
    normalized: list[dict] = []
    required = {
        "question_text",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "correct_option",
    }
    for item in payload:
        if not required.issubset(item.keys()):
            raise ValueError("Invalid question object structure.")
        correct = str(item["correct_option"]).lower()
        if correct not in {"a", "b", "c", "d"}:
            raise ValueError("correct_option must be one of a,b,c,d")
        normalized.append(
            {
                "question_text": str(item["question_text"]),
                "option_a": str(item["option_a"]),
                "option_b": str(item["option_b"]),
                "option_c": str(item["option_c"]),
                "option_d": str(item["option_d"]),
                "correct_option": correct,
            }
        )
    return normalized


@router.message(AdminStates.waiting_quiz_json)
async def receive_quiz_json(message: Message, state: FSMContext, config: Config, db: Database) -> None:
    if not _is_admin(message, config) or not message.text:
        return
    try:
        payload = json.loads(message.text)
        if not isinstance(payload, list):
            await message.answer("JSON must be an array.")
            return
        questions = _validate_quiz_payload(payload)
        data = await state.get_data()
        lesson_id = int(data["quiz_lesson_id"])
        count = await db.save_quiz_questions(lesson_id, questions)
        await state.clear()
        await message.answer(t("en", "quiz_saved", count=count))
    except json.JSONDecodeError:
        await message.answer("Invalid JSON format.")
    except Exception:
        logger.exception("Failed to save quiz JSON")
        await message.answer(t("en", "error"))


@router.callback_query(F.data == "admin:view_stats")
async def view_stats(callback: CallbackQuery, db: Database, config: Config) -> None:
    if not _is_admin(callback, config):
        await callback.answer(t("en", "admin_only"), show_alert=True)
        return
    try:
        users_count = await db.users_count()
        popular = await db.popular_subjects()
        subjects_lines = [f"- {subject}: {count}" for subject, count in popular] or ["- No data"]
        text = t("en", "stats_text", users_count=users_count, subjects="\n".join(subjects_lines))
        await callback.message.answer(text)
        await callback.answer()
    except Exception:
        logger.exception("Failed to view stats")
        await callback.answer("Error.", show_alert=True)


@router.callback_query(F.data == "admin:broadcast")
async def broadcast_start(callback: CallbackQuery, state: FSMContext, config: Config) -> None:
    if not _is_admin(callback, config):
        await callback.answer(t("en", "admin_only"), show_alert=True)
        return
    await state.set_state(AdminStates.waiting_broadcast_text)
    await callback.message.answer(t("en", "send_broadcast_text"))
    await callback.answer()


@router.message(AdminStates.waiting_broadcast_text)
async def broadcast_send(message: Message, state: FSMContext, db: Database, config: Config) -> None:
    if not _is_admin(message, config) or not message.text:
        return
    text = message.text
    sent = 0
    failed = 0
    try:
        user_ids = await db.all_user_telegram_ids()
        for telegram_id in user_ids:
            try:
                await message.bot.send_message(telegram_id, text)
                sent += 1
            except Exception:
                failed += 1
                logger.exception("Broadcast failed for %s", telegram_id)
        await state.clear()
        await message.answer(t("en", "broadcast_done", sent=sent, failed=failed))
    except Exception:
        logger.exception("Broadcast operation failed")
        await message.answer(t("en", "error"))
