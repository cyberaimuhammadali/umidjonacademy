import logging
from typing import Any

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from data.texts import t
from database import Database
from handlers.states import RegistrationStates, SettingsStates
from keyboards.user import (
    LEVELS,
    SUBJECTS,
    language_keyboard,
    lesson_actions_keyboard,
    level_keyboard,
    main_menu_keyboard,
    quiz_options_keyboard,
    retake_quiz_keyboard,
    settings_keyboard,
    subject_keyboard,
)


logger = logging.getLogger(__name__)
router = Router()

LANG_MAP = {"Uzbek 🇺🇿": "uz", "English 🇬🇧": "en"}
LEVEL_MAP = {
    "School 🏫": "School",
    "University 🎓": "University",
    "Self-Learner 📚": "Self-Learner",
}

active_quizzes: dict[int, dict[str, Any]] = {}


async def _get_user_language(db: Database, telegram_id: int) -> str:
    user = await db.get_user_by_telegram_id(telegram_id)
    if user and user.get("language") in {"uz", "en"}:
        return str(user["language"])
    return "uz"


@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext, db: Database) -> None:
    if not message.from_user:
        return
    telegram_id = message.from_user.id
    try:
        user = await db.get_user_by_telegram_id(telegram_id)
        if not user:
            await db.create_user(telegram_id)
            await state.set_state(RegistrationStates.choosing_language)
            await message.answer(
                t("uz", "select_language"),
                reply_markup=language_keyboard(),
            )
            return

        language = str(user.get("language") or "uz")
        await state.clear()
        await message.answer(
            f"{t(language, 'welcome')}\n{t(language, 'main_menu')}",
            reply_markup=ReplyKeyboardRemove(),
        )
        await message.answer(
            t(language, "main_menu"),
            reply_markup=main_menu_keyboard(language),
        )
    except Exception:
        logger.exception("Failed in /start")
        await message.answer("Internal error.")


@router.message(RegistrationStates.choosing_language)
async def select_language(message: Message, state: FSMContext, db: Database) -> None:
    if not message.from_user or not message.text:
        return
    language = LANG_MAP.get(message.text.strip())
    if not language:
        await message.answer("Please choose from the keyboard.", reply_markup=language_keyboard())
        return
    try:
        await db.update_user_language(message.from_user.id, language)
        await state.set_state(RegistrationStates.choosing_level)
        await message.answer(t(language, "select_level"), reply_markup=level_keyboard())
    except Exception:
        logger.exception("Failed selecting language")
        await message.answer(t("en", "error"))


@router.message(RegistrationStates.choosing_level)
async def select_level(message: Message, state: FSMContext, db: Database) -> None:
    if not message.from_user or not message.text:
        return
    level = LEVEL_MAP.get(message.text.strip())
    if not level:
        await message.answer("Please choose from the keyboard.", reply_markup=level_keyboard())
        return
    try:
        user_lang = await _get_user_language(db, message.from_user.id)
        await db.update_user_level(message.from_user.id, level)
        await state.set_state(RegistrationStates.choosing_subject)
        await message.answer(t(user_lang, "select_subject"), reply_markup=subject_keyboard())
    except Exception:
        logger.exception("Failed selecting level")
        await message.answer(t("en", "error"))


@router.message(RegistrationStates.choosing_subject)
async def select_subject(message: Message, state: FSMContext, db: Database) -> None:
    if not message.from_user or not message.text:
        return
    subject = message.text.strip()
    if subject not in SUBJECTS:
        await message.answer("Please choose from the keyboard.", reply_markup=subject_keyboard())
        return
    try:
        user_lang = await _get_user_language(db, message.from_user.id)
        await db.update_user_subject(message.from_user.id, subject)
        await state.clear()
        await message.answer(t(user_lang, "main_menu"), reply_markup=ReplyKeyboardRemove())
        await message.answer(t(user_lang, "main_menu"), reply_markup=main_menu_keyboard(user_lang))
    except Exception:
        logger.exception("Failed selecting subject")
        await message.answer(t("en", "error"))


@router.callback_query(F.data == "menu:main")
async def menu_main(callback: CallbackQuery, db: Database) -> None:
    if not callback.from_user:
        return
    language = await _get_user_language(db, callback.from_user.id)
    await callback.message.answer(t(language, "main_menu"), reply_markup=main_menu_keyboard(language))
    await callback.answer()


@router.callback_query(F.data == "menu:lessons")
async def my_lessons(callback: CallbackQuery, db: Database) -> None:
    if not callback.from_user:
        return
    telegram_id = callback.from_user.id
    try:
        user = await db.get_user_by_telegram_id(telegram_id)
        if not user:
            await callback.answer("Use /start first.", show_alert=True)
            return
        language = str(user.get("language") or "uz")
        subject = user.get("current_subject")
        level = user.get("level")
        current_lesson = int(user.get("current_lesson") or 1)
        if not subject or not level:
            await callback.message.answer(t(language, "select_subject"))
            await callback.answer()
            return

        lesson = await db.get_current_lesson(str(subject), str(level), current_lesson)
        if not lesson:
            await callback.message.answer(t(language, "no_lesson"))
            await callback.answer()
            return

        caption = f"{t(language, 'your_next_lesson')}\n{lesson['lesson_number']}. {lesson['title']}"
        await callback.bot.send_video(
            chat_id=telegram_id,
            video=lesson["video_file_id"],
            caption=caption,
            reply_markup=lesson_actions_keyboard(language, int(lesson["id"])),
        )
        await callback.answer()
    except Exception:
        logger.exception("Failed to show lesson")
        await callback.answer("Error.", show_alert=True)


@router.callback_query(F.data == "menu:progress")
async def my_progress(callback: CallbackQuery, db: Database) -> None:
    if not callback.from_user:
        return
    try:
        user = await db.get_user_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer("Use /start first.", show_alert=True)
            return
        language = str(user.get("language") or "uz")
        text = t(
            language,
            "progress_text",
            subject=user.get("current_subject") or "-",
            level=user.get("level") or "-",
            current_lesson=int(user.get("current_lesson") or 1),
        )
        await callback.message.answer(text, reply_markup=main_menu_keyboard(language))
        await callback.answer()
    except Exception:
        logger.exception("Failed to show progress")
        await callback.answer("Error.", show_alert=True)


@router.callback_query(F.data == "menu:settings")
async def open_settings(callback: CallbackQuery, db: Database) -> None:
    if not callback.from_user:
        return
    language = await _get_user_language(db, callback.from_user.id)
    await callback.message.answer(t(language, "settings_text"), reply_markup=settings_keyboard(language))
    await callback.answer()


@router.callback_query(F.data == "settings:language")
async def settings_language(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    if not callback.from_user:
        return
    language = await _get_user_language(db, callback.from_user.id)
    await state.set_state(SettingsStates.change_language)
    await callback.message.answer(t(language, "select_language"), reply_markup=language_keyboard())
    await callback.answer()


@router.callback_query(F.data == "settings:level")
async def settings_level(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    if not callback.from_user:
        return
    language = await _get_user_language(db, callback.from_user.id)
    await state.set_state(SettingsStates.change_level)
    await callback.message.answer(t(language, "select_level"), reply_markup=level_keyboard())
    await callback.answer()


@router.callback_query(F.data == "settings:subject")
async def settings_subject(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    if not callback.from_user:
        return
    language = await _get_user_language(db, callback.from_user.id)
    await state.set_state(SettingsStates.change_subject)
    await callback.message.answer(t(language, "select_subject"), reply_markup=subject_keyboard())
    await callback.answer()


@router.message(SettingsStates.change_language)
async def settings_language_save(message: Message, state: FSMContext, db: Database) -> None:
    if not message.from_user or not message.text:
        return
    language = LANG_MAP.get(message.text.strip())
    if not language:
        await message.answer("Please choose from keyboard.", reply_markup=language_keyboard())
        return
    await db.update_user_language(message.from_user.id, language)
    await state.clear()
    await message.answer(t(language, "changed_language"), reply_markup=ReplyKeyboardRemove())
    await message.answer(t(language, "main_menu"), reply_markup=main_menu_keyboard(language))


@router.message(SettingsStates.change_level)
async def settings_level_save(message: Message, state: FSMContext, db: Database) -> None:
    if not message.from_user or not message.text:
        return
    level = LEVEL_MAP.get(message.text.strip())
    if not level:
        await message.answer("Please choose from keyboard.", reply_markup=level_keyboard())
        return
    language = await _get_user_language(db, message.from_user.id)
    await db.update_user_level(message.from_user.id, level)
    await state.clear()
    await message.answer(t(language, "changed_level"), reply_markup=ReplyKeyboardRemove())
    await message.answer(t(language, "main_menu"), reply_markup=main_menu_keyboard(language))


@router.message(SettingsStates.change_subject)
async def settings_subject_save(message: Message, state: FSMContext, db: Database) -> None:
    if not message.from_user or not message.text:
        return
    subject = message.text.strip()
    if subject not in SUBJECTS:
        await message.answer("Please choose from keyboard.", reply_markup=subject_keyboard())
        return
    language = await _get_user_language(db, message.from_user.id)
    await db.update_user_subject(message.from_user.id, subject)
    await state.clear()
    await message.answer(t(language, "changed_subject"), reply_markup=ReplyKeyboardRemove())
    await message.answer(t(language, "main_menu"), reply_markup=main_menu_keyboard(language))


async def _send_quiz_question(callback: CallbackQuery, language: str, session: dict[str, Any]) -> None:
    idx = int(session["index"])
    questions = session["questions"]
    total = len(questions)
    question = questions[idx]
    text = (
        f"{t(language, 'quiz')}\n"
        f"{t(language, 'quiz_question_prefix', current=idx + 1, total=total)}\n\n"
        f"{question['question_text']}"
    )
    await callback.message.answer(text, reply_markup=quiz_options_keyboard(int(question["id"])))


@router.callback_query(F.data.startswith("lesson:completed:"))
async def lesson_completed(callback: CallbackQuery, db: Database) -> None:
    if not callback.from_user or not callback.data:
        return
    try:
        language = await _get_user_language(db, callback.from_user.id)
        lesson_id = int(callback.data.split(":")[-1])
        questions = await db.get_quiz_by_lesson(lesson_id)
        if not questions:
            await callback.answer("Quiz not available.", show_alert=True)
            return
        session = {
            "lesson_id": lesson_id,
            "questions": questions[:15],
            "index": 0,
            "score": 0,
        }
        active_quizzes[callback.from_user.id] = session
        await _send_quiz_question(callback, language, session)
        await callback.answer()
    except Exception:
        logger.exception("Failed to start quiz")
        await callback.answer("Error.", show_alert=True)


@router.callback_query(F.data.startswith("quiz:answer:"))
async def quiz_answer(callback: CallbackQuery, db: Database) -> None:
    if not callback.from_user or not callback.data:
        return
    telegram_id = callback.from_user.id
    session = active_quizzes.get(telegram_id)
    if not session:
        await callback.answer("Quiz session expired.", show_alert=True)
        return

    try:
        _, _, question_id_raw, selected_option = callback.data.split(":")
        question_id = int(question_id_raw)
        questions = session["questions"]
        idx = int(session["index"])
        if idx >= len(questions):
            await callback.answer("Quiz already finished.", show_alert=True)
            return
        current_question = questions[idx]
        if int(current_question["id"]) != question_id:
            await callback.answer("Invalid question.", show_alert=True)
            return

        language = await _get_user_language(db, telegram_id)
        if selected_option.lower() == str(current_question["correct_option"]).lower():
            session["score"] = int(session["score"]) + 1
            await callback.answer(t(language, "correct"))
        else:
            await callback.answer(t(language, "wrong"))

        session["index"] = idx + 1
        if int(session["index"]) < len(questions):
            await _send_quiz_question(callback, language, session)
            return

        user = await db.get_user_by_telegram_id(telegram_id)
        lesson = await db.get_lesson_by_id(int(session["lesson_id"]))
        if not user or not lesson:
            active_quizzes.pop(telegram_id, None)
            return

        score = int(session["score"])
        total = len(questions)
        passed = score >= 12
        await db.record_quiz_result(int(user["id"]), int(lesson["id"]), score, passed)
        if passed and int(user.get("current_lesson") or 1) == int(lesson["lesson_number"]):
            await db.increment_user_lesson(telegram_id)

        text = (
            f"{t(language, 'score', score=score, total=total)}\n"
            f"{t(language, 'you_passed') if passed else t(language, 'you_failed')}"
        )
        if passed:
            await callback.message.answer(text, reply_markup=main_menu_keyboard(language))
        else:
            await callback.message.answer(
                text,
                reply_markup=retake_quiz_keyboard(int(lesson["id"]), language),
            )
        active_quizzes.pop(telegram_id, None)
    except Exception:
        logger.exception("Failed to process quiz answer")
        await callback.answer("Error.", show_alert=True)
