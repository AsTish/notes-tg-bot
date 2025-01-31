# -*- coding: utf-8 -*-

import asyncio
import logging
from django.core.management.base import BaseCommand
from telegram_bot.bot import main  # Импортируем функцию запуска бота

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Запускает Telegram-бота"

    def handle(self, *args, **kwargs):
        logger.info("Запуск Telegram-бота...")
        try:
            asyncio.run(main())  # Запускаем бота
        except KeyboardInterrupt:
            logger.info("Бот остановлен вручную.")
