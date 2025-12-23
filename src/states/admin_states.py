from aiogram.fsm.state import State, StatesGroup


class AdminMedia(StatesGroup):
    """
    Состояния для обновления медиа-файлов в админ-панели.
    """
    waiting_for_start_video = State()
    waiting_for_tourist_voice = State()
    waiting_for_partner_voice = State()
