# TODO: Rename file to correct spelling KEYBOARDS
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

kb_main_menu = [
    [
        KeyboardButton(text="создать заметку"),
        KeyboardButton(text="создать папку")
    ],
    [
        KeyboardButton(text="все заметки"),
        KeyboardButton(text="все папки")
    ]
]
keyboard_main_menu = ReplyKeyboardMarkup(
    keyboard = kb_main_menu,
    resize_keyboard = True,
    one_time_keybord = True,
    input_field_placeholder = "Начальное меню"
)
