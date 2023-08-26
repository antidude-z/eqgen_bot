"""Основные хэндлеры, обеспечивающие работу базовых функций бота"""

import logging
import html
import json
import traceback

from telegram import Update
from telegram.ext import ConversationHandler
from telegram.constants import ParseMode

from . import main_menu, LOCALES, TEMPLATE_IDS
from .util import CustomContext, clear_output

logger = logging.getLogger(__name__)


async def begin(update: Update, context: CustomContext):
    """Войти в меню генерации новой работы (/generate) и создать словарь пользовательских данных"""

    await update.message.delete()

    await context.saved_message('main_menu').create(LOCALES['loading'])

    context.task = {'variants': 1, 'name': '', 'description': '', 'examples': []}
    context.eq_names = TEMPLATE_IDS.copy()
    context.selected_example = 0
    context.eq_page = 0
    context.buffered_file_id = None
    context.is_generating = False

    return await main_menu.main_menu_handler(update, context)


async def start(update: Update, context: CustomContext):
    """Отправить пользователю приветственное сообщение/справку"""
    await update.message.reply_text(LOCALES['start'], parse_mode=ParseMode.MARKDOWN)


async def about(update: Update, context: CustomContext):
    """Отправить пользователю сведения о проекте"""
    await update.message.reply_text(LOCALES['about'].replace('$', '\\'),  # меняем доллары на экранирующий бэкслеш
                                    parse_mode=ParseMode.MARKDOWN_V2)


async def delete_fallback_messages(update: Update, context: CustomContext):
    """Удалить лишние сообщения, отправленные во время работы меню генерации"""
    await update.message.delete()


async def cancel(update: Update, context: CustomContext):
    """Выйти из меню генерации, очистив сообщения и пользовательские данные (полный сброс)"""

    await update.message.delete()
    await context.saved_message('main_menu').delete()
    await context.saved_message('input').delete()

    # на случай, если уже добавил кастомный шаблон, мы его всё равно удалим
    clear_output(context.task['name'], str(update.effective_user.id))

    context.user_data.clear()

    return ConversationHandler.END


async def error_handler(update: object, context: CustomContext) -> None:
    """Обработчик ошибок на стороне телеграм-бота"""

    # 1. отправляет исключение в логи
    # 2. затем оформляет сообщение разработчику и кидает его в лс по указанному айди

    logger.error("Exception while handling an update:", exc_info=context.error)

    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    await context.bot.send_message(
        chat_id=913035252, text=message, parse_mode=ParseMode.HTML
    )
