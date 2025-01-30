# -*- coding: utf-8 -*-

import os, django, sys

sys.path.append(r'C:/Users/ast04/Desktop/projects/notes-bot/notes_project')
os.environ['DJANGO_SETTINGS_MODULE'] = 'notes_project.settings'
django.setup()

from dotenv import load_dotenv

import asyncio
import logging

import keybords as kb

from aiogram import Bot, Dispatcher, types, F
# from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.filters.command import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, BotCommandScopeDefault, BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from django.core.management import execute_from_command_line
from django.utils import timezone
from django.contrib.auth import get_user_model

from asgiref.sync import sync_to_async

from notes.models import Note, Folder


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()  # Загружаем переменные окружения из .env
API_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher()

user_model = get_user_model()


# Состояния заметок
class NoteStates(StatesGroup):   
    waiting_for_note_title = State()
    waiting_for_note_text = State()
    waiting_for_folder_choice = State()

# Состояния папок
class FolderStates(StatesGroup):
    waiting_for_folder_name = State()


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Запустить бота"),
        BotCommand(command="/add_note", description="Создать заметку"),
        BotCommand(command="/add_folder", description="Создать папку"),
        BotCommand(command="/all_notes", description="Все заметки"),
        BotCommand(command="/all_folders", description="Все папки")
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())


# Кастомный пользователь
@sync_to_async
def create_custom_user(user_id, username):
    if not username:
        username = f"user_{user_id}"

    user, created = user_model.objects.get_or_create(
        telegram_id=user_id,
        defaults={"username": username}
    )
    
    if created:
        logger.info(f"Создан новый пользователь: {user.username} (ID: {user.telegram_id})")
    else:
        logger.info(f"Пользователь {user.username} уже существует (ID: {user.telegram_id}) \nuser.id = {user.id} \n dict = {user.__dict__}")

    return user


# Команда /main_menu
@dp.message(Command("main_menu"))
async def send_welcome(message: types.Message):
    await message.reply("Выберите действие")


@sync_to_async
def get_user_by_id(user_id):
    return user_model.objects.get(id=user_id)


# Команда /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    # Создаем пользователя, если он не существует
    user = await create_custom_user(user_id, username)
    
    if user:
        await message.reply(f"Привет, {message.from_user.first_name}! Вы успешно зарегистрированы в боте.")
    else:
        await message.reply("Произошла ошибка при регистрации пользователя.")

    await bot.send_message(message.from_user.id, "Привет! Я твой бот для заметок.", reply_markup=kb.keyboard_main_menu)


# Создание заметки
@dp.message(Command("add_note"))
@dp.message(F.text == "создать заметку")
async def add_note(message: types.Message, state: FSMContext):
    await message.reply("Пожалуйста, введите заголовок вашей заметки:")
    await state.set_state(NoteStates.waiting_for_note_title)

# Добавление заголовка заметки
@dp.message(NoteStates.waiting_for_note_title)
async def get_note_title(message: types.Message, state: FSMContext):
    note_title = message.text
    await state.update_data(note_title=note_title)
    await message.reply("Теперь введите описание вашей заметки:")
    await state.set_state(NoteStates.waiting_for_note_text)


# Асинхронное получение всех заметок пользователя
@sync_to_async
def get_user_notes(user_id):
    user = user_model.objects.filter(telegram_id=user_id).first()
    if not user:
        logger.warning(f"Пользователь с ID {user_id} не найден в базе!")
        return []
    
    notes = list(user.notes.all())
    logger.info(f"Найдено {len(notes)} заметок для пользователя {user.username} (ID: {user_id})")
    return notes


# Команда /all_notes
@dp.message(Command("all_notes"))
@dp.message(F.text == "все заметки")
async def show_all_notes(message: types.Message):
    user_id = message.from_user.id
    notes = await get_user_notes(user_id)

    if notes is None:
        await message.reply("Вы не зарегистрированы! Введите /start для регистрации.")
        return

    if notes:
        buttons = [
            [InlineKeyboardButton(text=note.title, callback_data=f"show_{note.id}")]
            for note in notes
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.reply("Вот все ваши заметки:", reply_markup=keyboard)
    else:
        await message.reply("У вас пока нет сохраненных заметок.")


# Асинхронное получение заметки по ID
@sync_to_async
def get_note_by_id(note_id):
    try:
        return Note.objects.get(id=note_id)
    except Note.DoesNotExist:
        return None

# Обработчик для показа деталей заметки
@dp.callback_query(F.data.startswith('show_'))
async def show_note_detail(callback_query: types.CallbackQuery):
    note_id = callback_query.data[len('show_'):]  # Получаем ID заметки
    note = await get_note_by_id(note_id)

    if not note:
        await callback_query.message.answer("Заметка не найдена или была удалена.")
        await callback_query.answer()
        return

    # Кнопка "Удалить"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Удалить", callback_data=f"delete_{note.id}")]
        ]
    )

    # Детали заметки
    await callback_query.message.answer(
        f"Заголовок: <b>{note.title}</b>\n\nОписание: \n{note.content if note.content else 'Описание отсутствует.'}\n",
        reply_markup=keyboard,
        parse_mode="HTML"    # форматирование текста
    )
    await callback_query.answer()


# Асинхронное создание папки
@sync_to_async
def create_folder(folder_name, user):
    logger.info(f"\nfolder name = {folder_name} \nuser = {user}")
    return Folder.objects.create(name=folder_name, user=user)

# Команда для создания папки
@dp.message(Command("add_folder"))
@dp.message(F.text == "создать папку")
async def create_folder_handler(message: types.Message, state: FSMContext):
    await message.reply("Пожалуйста, введите имя вашей папки:")
    await state.set_state(FolderStates.waiting_for_folder_name)

# Обработчик ввода имени папки
@dp.message(FolderStates.waiting_for_folder_name)
async def get_folder_name(message: types.Message, state: FSMContext):
    folder_name = message.text.strip()

    if not folder_name:
        await message.reply("Название папки не может быть пустым. Попробуйте еще раз:")
        return

    user_id = message.from_user.id

    # Получаем пользователя из базы
    try:
        user = await sync_to_async(user_model.objects.get)(telegram_id=user_id)
    except user_model.DoesNotExist:
        await message.reply("Вы не зарегистрированы! Введите /start для регистрации.")
        return

    logger.info("пользователь существует")

    # Проверяем, существует ли уже такая папка
    folder_exists = await sync_to_async(Folder.objects.filter(name=folder_name, user=user).exists)()

    logger.info(f"папка существует = {folder_exists}")

    if folder_exists:
        await message.reply(f"Папка с именем '{folder_name}' уже существует.")
    else:
        await create_folder(folder_name, user)
        await message.reply(f"Папка '{folder_name}' успешно создана!")
        logger.info(f"Папка '{folder_name}' успешно создана!")

    await state.clear()  # Сбрасываем состояние


# Обработчик ввода текста заметки и выбора папки
@dp.message(NoteStates.waiting_for_note_text)
async def get_note_text(message: types.Message, state: FSMContext):
    note_text = message.text
    await state.update_data(note_text=note_text)

    user_id = message.from_user.id
    try:
        user = await sync_to_async(user_model.objects.get)(telegram_id=user_id)
    except user_model.DoesNotExist:
        await message.reply("Пользователь не найден! Введите /start для регистрации.")
        return

    # Получаем список папок пользователя
    folders = await get_user_folders(user)

    if folders:
        buttons = [[InlineKeyboardButton(text=folder.name, callback_data=f"folder_{folder.id}")]
                   for folder in folders]
        buttons.append([InlineKeyboardButton(text="Без папки", callback_data="folder_none")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        await message.reply("Выберите папку для сохранения заметки:", reply_markup=keyboard)
        await state.set_state(NoteStates.waiting_for_folder_choice)
    else:
        await message.reply("У вас нет папок. Заметка будет сохранена без папки.")
        logger.info("вызов save_note")
        await save_note(message, state, None, user)


# Выбор папки
@dp.callback_query(NoteStates.waiting_for_folder_choice)
async def choose_folder(callback_query: types.CallbackQuery, state: FSMContext):
    folder_id = callback_query.data[len("folder_"):] if callback_query.data != "folder_none" else None
    
 
    user_id = callback_query.from_user.id

    try:
        user = await sync_to_async(user_model.objects.get)(telegram_id=user_id)
    except user_model.DoesNotExist:
        await callback_query.message.reply("Пользователь не найден! Введите /start для регистрации.")
        return

    await save_note(callback_query.message, state, folder_id, user)
    await callback_query.answer()


# Проверка существования пользователя
@sync_to_async
def check_user_exists(user_id):
    return user_model.objects.filter(telegram_id=user_id).exists()



# Функция сохранения заметки
async def save_note(message, state, folder_id, user):
    logger.info(f"Начинаем сохранение заметки. User: {user}, Folder ID: {folder_id}")
    
    user_data = await state.get_data()
    note_title = user_data.get("note_title")
    note_text = user_data.get("note_text")

    logger.info(f"Полученные данные: Title: {note_title}, Text: {note_text}")

    folder = None
    if folder_id:
        try:
            folder = await sync_to_async(Folder.objects.get)(id=int(folder_id), user=user)
            logger.info(f"Папка найдена: {folder.name}")
        except Folder.DoesNotExist:
            await message.reply("Выбранная папка не найдена, заметка будет сохранена без папки.")
            logger.info(f"Папка с ID {folder_id} не найдена!")


    user_exists = await check_user_exists(user.telegram_id)

    if not user_exists:
        logger.info(f"Ошибка: пользователь {user.telegram_id} не найден в базе!")
        await message.reply("Ошибка: ваш профиль не найден")
        return

    # Создание заметки
    note = await create_note(note_title, note_text, user, folder)
    logger.info(f"Заметка создана с ID: {note.id}")

    folder_msg = f" в папке '{folder.name}'" if folder else " без папки"
    await message.answer(f"Заметка '{note_title}' успешно сохранена{folder_msg}! ✅")
    
    await state.clear()


# Функция создания заметки
@sync_to_async
def create_note(title, content, user, folder=None):
    try:
        logger.info(f"Создаем заметку: {title}, User ID: {user.id if user else 'None'}, Folder: {folder}")

        if not title:
            raise ValueError("Ошибка: title не может быть пустым!")

        if not user:
            raise ValueError("Ошибка: user не передан!")

        # user = user_model.objects.get(telegram_id=)
        user.save()

        logger.info("Перед созданием заметки...")
        logger.info(f"user = {user} \nuser.id = {user.id} \ntitle = {title} \ncontent = {content} \nfolder = {folder}")
        logger.info(f"Тип user: {type(user)}")


        note = Note.objects.create(
            title=title,
            content=content,
            user=user,
            folder=folder,
            created_at=timezone.now(),
            updated_at=timezone.now()
        )


        logger.info(f"Заметка создана с ID: {note.id}")
        return note

    except Exception as e:
        logger.error(f"Ошибка при создании заметки: {e}")
        raise


# Функция получения папок пользователя
@sync_to_async
def get_user_folders(user):
    return list(Folder.objects.filter(user=user))


# Получение всех заметок в папке
@sync_to_async
def get_folder_notes(folder):
    return list(folder.notes.all())


# Список всех папок пользователя
@dp.message(Command("all_folders"))
@dp.message(F.text == "все папки")
async def show_all_folders(message: types.Message):
    user_id = message.from_user.id

    try:
        user = await sync_to_async(user_model.objects.get)(telegram_id=user_id)
    except user_model.DoesNotExist:
        await message.reply("Вы не зарегистрированы! Введите /start для регистрации.")
        return

    folders = await get_user_folders(user)

    if folders:
        buttons = [
            [
                InlineKeyboardButton(text=folder.name, callback_data=f"folder_{folder.id}"),
                InlineKeyboardButton(text="❌", callback_data=f"to_delete_folder_{folder.id}")
            ]
            for folder in folders
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.reply("Ваши папки:", reply_markup=keyboard)
    else:
        await message.reply("У вас пока нет сохраненных папок.")


# Отображение содержимого папки
@dp.callback_query(F.data.startswith('folder_'))
async def show_folder_detail(callback_query: types.CallbackQuery):
    folder_id = int(callback_query.data[len('folder_'):])  # ID папки
    user_id = callback_query.from_user.id

    try:
        user = await sync_to_async(user_model.objects.get)(telegram_id=user_id)
    except user_model.DoesNotExist:
        await callback_query.message.reply("Вы не зарегистрированы! Введите /start для регистрации.")
        await callback_query.answer()
        return

    try:
        folder = await sync_to_async(Folder.objects.get)(id=folder_id, user=user)
    except Folder.DoesNotExist:
        await callback_query.message.reply("Эта папка не найдена.")
        await callback_query.answer()
        return

    notes = await get_folder_notes(folder)

    if notes:
        buttons = [
            [InlineKeyboardButton(text=note.title, callback_data=f"show_{note.id}")]
            for note in notes
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback_query.message.answer(f"Папка: {folder.name}\nВыберите заметку:", reply_markup=keyboard)
    else:
        await callback_query.message.answer(f"Папка: {folder.name} пуста.")

    await callback_query.answer()  
    

# Удаление заметки (из папки тоже)
@dp.callback_query(F.data.startswith('delete_'))
async def delete_note(callback_query: types.CallbackQuery):
    note_id = int(callback_query.data[len('delete_'):])  # Получаем ID заметки
    user_id = callback_query.from_user.id

    try:
        user = await sync_to_async(user_model.objects.get)(telegram_id=user_id)
    except user_model.DoesNotExist:
        await callback_query.message.reply("Вы не зарегистрированы! Введите /start для регистрации.")
        await callback_query.answer()
        return

    try:
        note, folder = await get_note_with_folder(note_id, user)

        note_title = note.title
        await sync_to_async(note.delete)()  # Удаляем заметку

        folder_msg = f" из папки '{folder.name}'" if folder else ""

        await callback_query.message.edit_text(f"Заметка '{note_title}' успешно удалена{folder_msg}.")
    except Note.DoesNotExist:
        await callback_query.message.answer("Заметка не найдена или уже была удалена.")

    await callback_query.answer()


# Функция для запроса подтверждения удаления папки
@dp.callback_query(F.data.startswith('to_delete_folder_'))
async def confirm_delete_folder(callback_query: types.CallbackQuery):
    folder_id = int(callback_query.data[len('to_delete_folder_'):])  # Получаем ID папки
    user_id = callback_query.from_user.id

    try:
        user = await sync_to_async(user_model.objects.get)(telegram_id=user_id)
    except user_model.DoesNotExist:
        await callback_query.message.reply("Вы не зарегистрированы! Введите /start для регистрации.")
        await callback_query.answer()
        return

    try:
        folder = await sync_to_async(Folder.objects.get)(id=folder_id, user=user)
    except Folder.DoesNotExist:
        await callback_query.message.answer("Папка не найдена или уже была удалена.")
        await callback_query.answer()
        return

    # Создаем кнопки подтверждения
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Удалить со всем содержимым", callback_data=f"confirm_all_delete_{folder.id}")],
        [InlineKeyboardButton(text="Удалить, но сохранить заметки", callback_data=f"confirm_keep_delete_{folder.id}")],
        [InlineKeyboardButton(text="Не удалять", callback_data="cancel_delete_folder")]
    ])

    await callback_query.message.answer(f"Вы уверены, что хотите удалить папку '{folder.name}'?", reply_markup=keyboard)
    await callback_query.answer()


# Функция удаления папки вместе с содержимым
@dp.callback_query(F.data.startswith('confirm_all_delete_'))
async def delete_folder_with_notes(callback_query: types.CallbackQuery):
    folder_id = int(callback_query.data[len('confirm_all_delete_'):])  # Получаем ID папки
    user_id = callback_query.from_user.id

    try:
        user = await sync_to_async(user_model.objects.get)(telegram_id=user_id)
    except user_model.DoesNotExist:
        await callback_query.message.reply("Вы не зарегистрированы! Введите /start для регистрации.")
        await callback_query.answer()
        return

    try:
        folder = await sync_to_async(Folder.objects.get)(id=folder_id, user=user)
        
        # Удаляем все заметки в папке
        await sync_to_async(Note.objects.filter(folder=folder).delete)()

        # Удаляем папку
        folder_name = folder.name
        await sync_to_async(folder.delete)()

        await callback_query.message.edit_text(f"Папка '{folder_name}' и все её заметки удалены.")
    except Folder.DoesNotExist:
        await callback_query.message.answer("Папка не найдена или уже была удалена.")

    await callback_query.answer()


# Функция удаления папки без удаления заметок (они останутся без папки)
@dp.callback_query(F.data.startswith('confirm_keep_delete_'))
async def delete_folder_keep_notes(callback_query: types.CallbackQuery):
    folder_id = int(callback_query.data[len('confirm_keep_delete_'):])  # Получаем ID папки
    user_id = callback_query.from_user.id

    try:
        user = await sync_to_async(user_model.objects.get)(telegram_id=user_id)
    except user_model.DoesNotExist:
        await callback_query.message.reply("Вы не зарегистрированы! Введите /start для регистрации.")
        await callback_query.answer()
        return

    try:
        folder = await sync_to_async(Folder.objects.get)(id=folder_id, user=user)
        
        # Обновляем все заметки в папке (удаляем привязку к папке)
        await sync_to_async(Note.objects.filter(folder=folder).update)(folder=None)

        # Удаляем папку
        folder_name = folder.name
        await sync_to_async(folder.delete)()

        await callback_query.message.edit_text(f"Папка '{folder_name}' удалена, но её заметки сохранены.")
    except Folder.DoesNotExist:
        await callback_query.message.answer("Папка не найдена или уже была удалена.")

    await callback_query.answer()


# Функция отмены удаления
@dp.callback_query(F.data == "cancel_delete_folder")
async def cancel_delete_folder(callback_query: types.CallbackQuery):
    await callback_query.message.answer("Удаление папки отменено.")
    await callback_query.answer()


# Получение заметки и её папки (через sync_to_async)
@sync_to_async
def get_note_with_folder(note_id, user):
    note = Note.objects.get(id=note_id, user=user)
    folder = note.folder  # Получаем папку (если есть)
    return note, folder


# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())