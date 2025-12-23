from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.filters import BaseFilter
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple

from src.config import ADMIN_TELEGRAM_ID
from src.services.user_service import UserService
from src.services.content_service import ContentService
from src.states.admin_states import AdminMedia

# Создаем роутер только для админов
router = Router()

# Функция для проверки, является ли пользователь администратором
async def is_admin_user(telegram_id: int, session: AsyncSession) -> bool:
    user_service = UserService(session)
    user = await user_service.get_user_by_telegram_id(str(telegram_id))
    return user is not None and user.status == 'ADMIN'

# Создаем кастомный фильтр для проверки статуса администратора
class AdminFilter(BaseFilter):
    async def __call__(self, message: types.Message, session: AsyncSession) -> bool:
        return await is_admin_user(message.from_user.id, session)

class AdminCallbackFilter(BaseFilter):
    async def __call__(self, callback_query: types.CallbackQuery, session: AsyncSession) -> bool:
        return await is_admin_user(callback_query.from_user.id, session)

# Применяем фильтр ко всем хендлерам в этом роутере
# router.message.filter(F.from_user.id == ADMIN_TELEGRAM_ID)
# router.callback_query.filter(F.from_user.id == ADMIN_TELEGRAM_ID)

# Удаляем глобальные фильтры, так как проверка статуса реализована в каждом обработчике


@router.message(Command("admin"), AdminFilter())
async def handle_admin_menu(message: types.Message, session: AsyncSession):
    """Отображает главное меню администратора."""
    user_service = UserService(session)
    user = await user_service.get_user_by_telegram_id(str(message.from_user.id))
    
    if user and user.status == 'ADMIN':
        text, keyboard = await generate_admin_panel_keyboard_with_ref_link(session, message, message.from_user.id)
        await message.answer(text, reply_markup=keyboard)
    else:
        await message.answer("❌ У вас нет прав администратора для выполнения этой операции.")

# --- Вспомогательная функция для генерации админ-панели ---

async def generate_admin_panel_keyboard(session: AsyncSession, message_or_callback, user_id: int) -> Tuple[str, types.InlineKeyboardMarkup]:
    """Генерирует сообщение и клавиатуру для админ-панели."""
    user_service = UserService(session)
    user = await user_service.get_user_by_telegram_id(str(user_id))
    
    # Проверяем наличие медиа-файлов
    content_service = ContentService(session)
    
    start_video_exists = await content_service.get_content_file_id(user.id, "start_video")
    tourist_voice_exists = await content_service.get_content_file_id(user.id, "tourist_voice")
    partner_voice_exists = await content_service.get_content_file_id(user.id, "partner_voice")
    
    # Определяем статусы кнопок
    start_video_status = "✅" if start_video_exists else "✏️"
    tourist_voice_status = "✅" if tourist_voice_exists else "✏️"
    partner_voice_status = "✅" if partner_voice_exists else "✏️"
    
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text=f"{start_video_status} Изменить кружок (старт)", callback_data="admin:change_start_video")],
            [types.InlineKeyboardButton(text=f"{tourist_voice_status} Изменить голос (турист)", callback_data="admin:change_tourist_voice")],
            [types.InlineKeyboardButton(text=f"{partner_voice_status} Изменить голос (партнер)", callback_data="admin:change_partner_voice")],
            [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:back_to_main")],
        ]
    )
    
    text = f"Добро пожаловать в настройки персонализации!"
    
    return text, keyboard

async def generate_admin_panel_keyboard_with_ref_link(session: AsyncSession, message_or_callback, user_id: int) -> Tuple[str, types.InlineKeyboardMarkup]:
    """Генерирует сообщение и клавиатуру для админ-панели с реферальной ссылкой."""
    user_service = UserService(session)
    user = await user_service.get_user_by_telegram_id(str(user_id))
    
    # Проверяем наличие медиа-файлов
    content_service = ContentService(session)
    
    start_video_exists = await content_service.get_content_file_id(user.id, "start_video")
    tourist_voice_exists = await content_service.get_content_file_id(user.id, "tourist_voice")
    partner_voice_exists = await content_service.get_content_file_id(user.id, "partner_voice")
    
    # Определяем статусы кнопок
    start_video_status = "✅" if start_video_exists else "✏️"
    tourist_voice_status = "✅" if tourist_voice_exists else "✏️"
    partner_voice_status = "✅" if partner_voice_exists else "✏️"
    
    # Используем сохраненную реферальную ссылку из базы данных
    bot_link = user.telegram_bot_referral_link if user.telegram_bot_referral_link else f"https://t.me/{(await message_or_callback.bot.get_me()).username}?start={user.referral_code}"
    
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text=f"⚙️ Настроить воронку ({start_video_status}{tourist_voice_status}{partner_voice_status})", callback_data="admin:settings")],
        ]
    )
    
    text = (f"Добро пожаловать, {user.username}! Вы в режиме администратора.\n\n"
            f"🔗 Ваша реферальная ссылка:\n<code>{bot_link}</code>")
    
    return text, keyboard

    
# --- Обработчики запросов на смену медиа ---

@router.callback_query(lambda c: c.data == "admin:change_start_video", AdminCallbackFilter())
async def request_start_video(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    user_service = UserService(session)
    user = await user_service.get_user_by_telegram_id(str(callback.from_user.id))
    
    if user and user.status == 'ADMIN':
        await state.set_state(AdminMedia.waiting_for_start_video)
        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:settings")]
            ]
        )
        await callback.message.answer("Пришлите новый видео-кружок для стартового сообщения.", reply_markup=keyboard)
    else:
        await callback.message.answer("❌ У вас нет прав администратора для выполнения этой операции.")
    await callback.answer()

@router.callback_query(lambda c: c.data == "admin:change_tourist_voice", AdminCallbackFilter())
async def request_tourist_voice(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    user_service = UserService(session)
    user = await user_service.get_user_by_telegram_id(str(callback.from_user.id))
    
    if user and user.status == 'ADMIN':
        await state.set_state(AdminMedia.waiting_for_tourist_voice)
        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:settings")]
            ]
        )
        await callback.message.answer("Пришлите новое голосовое сообщение для ветки 'Турист'.", reply_markup=keyboard)
    else:
        await callback.message.answer("❌ У вас нет прав администратора для выполнения этой операции.")
    await callback.answer()

@router.callback_query(lambda c: c.data == "admin:change_partner_voice", AdminCallbackFilter())
async def request_partner_voice(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    user_service = UserService(session)
    user = await user_service.get_user_by_telegram_id(str(callback.from_user.id))
    
    if user and user.status == 'ADMIN':
        await state.set_state(AdminMedia.waiting_for_partner_voice)
        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:settings")]
            ]
        )
        await callback.message.answer("Пришлите новое голосовое сообщение для ветки 'Партнер'.", reply_markup=keyboard)
    else:
        await callback.message.answer("❌ У вас нет прав администратора для выполнения этой операции.")
    await callback.answer()

# --- Обработчики для кнопок из основного админ-меню ---

@router.callback_query(lambda c: c.data == "admin:settings", AdminCallbackFilter())
async def handle_admin_settings(callback: types.CallbackQuery, session: AsyncSession):
    """Обработчик кнопки 'Настроить воронку'."""
    user_service = UserService(session)
    user = await user_service.get_user_by_telegram_id(str(callback.from_user.id))
    
    if user and user.status == 'ADMIN':
        text, keyboard = await generate_admin_panel_keyboard(session, callback, callback.from_user.id)
        await callback.message.edit_text(text, reply_markup=keyboard)
    else:
        await callback.message.answer("❌ У вас нет прав администратора для выполнения этой операции.")
    await callback.answer()

@router.callback_query(lambda c: c.data == "admin:back_to_main", AdminCallbackFilter())
async def handle_back_to_main(callback: types.CallbackQuery, session: AsyncSession):
    """Обработчик кнопки 'Назад' для возврата в главное меню."""
    user_service = UserService(session)
    user = await user_service.get_user_by_telegram_id(str(callback.from_user.id))
    
    if user and user.status == 'ADMIN':
        text, keyboard = await generate_admin_panel_keyboard_with_ref_link(session, callback, callback.from_user.id)
        await callback.message.edit_text(text, reply_markup=keyboard)
    else:
        await callback.message.answer("❌ У вас нет прав администратора для выполнения этой операции.")
    await callback.answer()

@router.callback_query(lambda c: c.data == "admin:get_ref_link", AdminCallbackFilter())
async def handle_get_ref_link(callback: types.CallbackQuery, session: AsyncSession):
    """Обработчик кнопки 'Моя реф. ссылка'."""
    user_service = UserService(session)
    user = await user_service.get_user_by_telegram_id(str(callback.from_user.id))
    
    if user and user.status == 'ADMIN':
        text, keyboard = await generate_admin_panel_keyboard_with_ref_link(session, callback, callback.from_user.id)
        await callback.message.edit_text(text, reply_markup=keyboard)
    else:
        await callback.message.answer("❌ У вас нет прав администратора для выполнения этой операции.")
    await callback.answer()

# --- Обработчики получения медиа ---

@router.message(AdminMedia.waiting_for_start_video, F.video_note, AdminFilter())
async def process_start_video(message: types.Message, state: FSMContext, session: AsyncSession):
    file_id = message.video_note.file_id
    user_service = UserService(session)
    user = await user_service.get_user_by_telegram_id(str(message.from_user.id))
    
    if user:
        content_service = ContentService(session)
        await content_service.update_content(user.id, "start_video", file_id)
        await state.clear()
        
        # Отправляем сообщение об успешном обновлении с кнопкой "Назад"
        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="⬅️ Назад в настройки", callback_data="admin:settings")]
            ]
        )
        await message.answer("✅ Стартовый кружок успешно обновлен!", reply_markup=keyboard)
    else:
        await message.answer("❌ Ошибка: пользователь не найден.")

@router.message(AdminMedia.waiting_for_tourist_voice, F.voice, AdminFilter())
async def process_tourist_voice(message: types.Message, state: FSMContext, session: AsyncSession):
    file_id = message.voice.file_id
    user_service = UserService(session)
    user = await user_service.get_user_by_telegram_id(str(message.from_user.id))
    
    if user:
        content_service = ContentService(session)
        await content_service.update_content(user.id, "tourist_voice", file_id)
        await state.clear()
        
        # Отправляем сообщение об успешном обновлении с кнопкой "Назад"
        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="⬅️ Назад в настройки", callback_data="admin:settings")]
            ]
        )
        await message.answer("✅ Голосовое для 'Туриста' успешно обновлено!", reply_markup=keyboard)
    else:
        await message.answer("❌ Ошибка: пользователь не найден.")

@router.message(AdminMedia.waiting_for_partner_voice, F.voice, AdminFilter())
async def process_partner_voice(message: types.Message, state: FSMContext, session: AsyncSession):
    file_id = message.voice.file_id
    user_service = UserService(session)
    user = await user_service.get_user_by_telegram_id(str(message.from_user.id))
    
    if user:
        content_service = ContentService(session)
        await content_service.update_content(user.id, "partner_voice", file_id)
        await state.clear()
        
        # Отправляем сообщение об успешном обновлении с кнопкой "Назад"
        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="⬅️ Назад в настройки", callback_data="admin:settings")]
            ]
        )
        await message.answer("✅ Голосовое для 'Партнера' успешно обновлено!", reply_markup=keyboard)
    else:
        await message.answer("❌ Ошибка: пользователь не найден.")