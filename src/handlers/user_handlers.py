from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.utils.deep_linking import decode_payload
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.user_service import UserService
from src.services.content_service import ContentService
from src.handlers.admin_handlers import generate_admin_panel_keyboard_with_ref_link

router = Router()

# Объединенный обработчик для /start
@router.message(CommandStart())
async def handle_start(message: types.Message, session: AsyncSession):
    """
    Обработчик команды /start.
    - Регистрирует или находит пользователя.
    - Разделяет логику для ADMIN и USER.
    - Обрабатывает реферальный код (deep link).
    - Отправляет соответствующее приветственное сообщение.
    """
    # Получаем payload из команды /start более надежным способом
    start_payload = None
    if message.text and message.text.startswith('/start '):
        try:
            # Берем часть после "/start "
            payload_part = message.text[len('/start '):].strip()
            start_payload = payload_part  # Используем напрямую, так как реферальный код не зашифрован
        except Exception:
            # Если не удалось декодировать payload, просто игнорируем его
            start_payload = None

    user_service = UserService(session)
    user = await user_service.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        start_payload=start_payload,
        bot=message.bot,  # Передаем бота для генерации реферальной ссылки
    )

    # Проверяем статус пользователя
    if user.status == 'ADMIN':
        # Логика для администратора
        text, keyboard = await generate_admin_panel_keyboard_with_ref_link(session, message, message.from_user.id)
        await message.answer(text, reply_markup=keyboard)
        return

    # Логика для обычного пользователя (USER)
    content_service = ContentService(session)
    admin_id_to_use = user.referred_by_user_id if user.referred_by_user_id else user.id
    start_video_id = await content_service.get_content_file_id(admin_id_to_use, "start_video")
    
    # Добавляем обработку ошибок при получении медиа-файла
    if start_video_id is None:
        # Если у реферала нет медиа, пробуем получить у самого пользователя
        start_video_id = await content_service.get_content_file_id(user.id, "start_video")

    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="📉 Хочу скидки", callback_data="branch:tourist")],
            [types.InlineKeyboardButton(text="💵 Хочу денег", callback_data="branch:partner")],
        ]
    )
    
    if start_video_id:
        await message.answer_video_note(video_note=start_video_id)
    await message.answer("Нажмешь не туда.\n\nУвидишь не то.\n\nОпределись с целью 🥷", reply_markup=keyboard)



@router.callback_query(lambda c: c.data == "branch:tourist")
async def handle_tourist_branch(callback: types.CallbackQuery, session: AsyncSession):
    """Обработчик ветки 'Турист'."""
    # Удаляем сообщение с кнопками
    await callback.message.delete()
    
    user_service = UserService(session)
    user = await user_service.get_user_by_telegram_id(str(callback.from_user.id))
    
    content_service = ContentService(session)
    if user.status == 'ADMIN':
        admin_id_to_use = user.id
    else:
        admin_id_to_use = user.referred_by_user_id if user.referred_by_user_id else user.id
    voice_id = await content_service.get_content_file_id(admin_id_to_use, "tourist_voice")
    
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(
                text="📱 ГЛЯНУТЬ ЦЕНЫ",
                web_app=types.WebAppInfo(url="https://clubsmarttravel.vercel.app/?source=travel")
            )]
        ]
    )
    if voice_id:
        await callback.message.answer_voice(voice=voice_id)
    await callback.message.answer("Платформа по ссылке.\n\nНе верь мне на слово.\n\nВерь своим глазам.\n\nОткрывай. Сравнивай.", reply_markup=keyboard)
    await callback.answer() # Закрываем "часики" на кнопке


@router.callback_query(lambda c: c.data == "branch:partner")
async def handle_partner_branch(callback: types.CallbackQuery, session: AsyncSession):
    """Обработчик ветки 'Партнер'."""
    # Удаляем сообщение с кнопками
    await callback.message.delete()
    
    user_service = UserService(session)
    user = await user_service.get_user_by_telegram_id(str(callback.from_user.id))

    content_service = ContentService(session)
    if user.status == 'ADMIN':
        admin_id_to_use = user.id
    else:
        admin_id_to_use = user.referred_by_user_id if user.referred_by_user_id else user.id
    voice_id = await content_service.get_content_file_id(admin_id_to_use, "partner_voice")

    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(
                text="📱 ПОСМОТРЕТЬ СУТЬ",
                web_app=types.WebAppInfo(url="https://clubsmarttravel.vercel.app/?source=business")
            )]
        ]
    )
    
    if voice_id:
        await callback.message.answer_voice(voice=voice_id)
    await callback.message.answer("Вся механика бизнеса — внутри.\n\nБез воды.\n\nТолько факты.\n\nВникай.", reply_markup=keyboard)
    await callback.answer()

