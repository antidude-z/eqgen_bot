"""Меню №1: основные настройки и генерация проверочной работы"""

import asyncio
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ConversationHandler
from telegram.constants import ParseMode
from is_natural_number import isNaturalNumber

from gen import task
from . import NAME, DESCRIPTION, VARIANTS, EXAMPLES, READY_WARNING, CREATE, MAIN_MENU, VARIANTS_INPUT, \
    NAME_INPUT, DESCRIPTION_INPUT, LOCALES
from .util import handle_input, answer_query, make_button, clear, remove_alarm, CustomContext, clear_output


@answer_query
async def main_menu_handler(update: Update, context: CustomContext):
    """Показать или обновить главное меню"""

    has_critical_warnings = False  # если у работы нет названия/заданий - генерация невозможна, предупреждаем об этом

    # форматируем название либо указываем, что пользователь его ещё не задал (критическая!)
    if context.task['name'] == '':
        name_text = LOCALES['no_name']
        has_critical_warnings = True
    else:
        name_text = LOCALES['name'].format(context.task['name'])

    # аналогично форматируем описание, только не помечаем его отсутствие как критическую ошибку
    if context.task['description'] == '':
        desc_text = LOCALES['no_desc']
    else:
        desc_text = LOCALES['description'].format(context.task['description'])

    vars_text = context.task['variants']

    # если заданий ещё нет, добавляем внизу менюшки текст, предупреждающий об этом
    warning = ''
    if not context.has_examples:
        has_critical_warnings = True
        warning = LOCALES['no_examples']

    keyboard = [
        [make_button('name_button', NAME),
         make_button('desc_button', DESCRIPTION)],
        [make_button('vars_button', VARIANTS),
         make_button('examples_button', EXAMPLES)],
        [make_button('ready_button', READY_WARNING if has_critical_warnings else CREATE)]  # пред-ие либо генерация
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    text = LOCALES['main_menu'].format(name_text, desc_text, vars_text, warning)  # собираем по кусочкам текст меню

    await context.saved_message('main_menu').edit(text=text, reply_markup=reply_markup)

    return MAIN_MENU


@answer_query
async def variants(update: Update, context: CustomContext):
    """Запросить у пользователя количество вариантов"""
    await context.saved_message('input').create(LOCALES['variants_input'])
    return VARIANTS_INPUT


@answer_query
async def name(update: Update, context: CustomContext):
    """Запросить у пользователя название работы"""
    await context.saved_message('input').create(LOCALES['name_input'])
    return NAME_INPUT


@answer_query
async def description(update: Update, context: CustomContext):
    """Запросить у пользователя описание работы"""
    await context.saved_message('input').create(LOCALES['description_input'])
    return DESCRIPTION_INPUT


@handle_input(main_menu_handler, variants)
async def variants_input(update: Update, context: CustomContext, text: str):
    """Проверить пользовательский ввод и сохранить полученное кол-во вариантов"""

    # требования к вводу - натуральное число, меньшее либо равное 30
    try:
        amount = int(text)
        if isNaturalNumber(amount) and amount <= 10:
            context.task['variants'] = amount
        else:
            raise ValueError  # всё равно кидаем исключение, когда число слишком большое
        return True  # возвращаемся в главное меню
    except (ValueError, TypeError):
        return False  # повторяем запрос на ввод


@handle_input(main_menu_handler)
async def name_input(update: Update, context: CustomContext, text):
    """Сохранить полученное название работы"""
    context.task['name'] = clear(text)
    return True


@handle_input(main_menu_handler)
async def description_input(update: Update, context: CustomContext, text):
    """Сохранить полученное описание работы"""
    context.task['description'] = clear(text)
    return True


@answer_query
async def generate(update: Update, context: CustomContext):
    """Создать новую проверочную работу по нажатию кнопки 'Готово'"""

    if context.is_generating:
        return await main_menu_handler(update, context)

    context.is_generating = True

    user_id = str(update.effective_user.id)
    chat_id = update.effective_chat.id

    msg = await context.bot.send_message(chat_id=chat_id, text=LOCALES['please_wait'],
                                         parse_mode=ParseMode.MARKDOWN)  # сообщение "пожалуйста, подождите..."

    # в отдельном треде (в целях асинхронности) запускаем генерацию работы и ждём результата
    await asyncio.to_thread(task.generate, context.task, user_id)

    # удаляем сообщение об ожидании и главное меню
    await msg.delete()
    await context.saved_message('main_menu').delete()

    # новым сообщением отправляем готовый архив из папки zip
    await context.bot.send_document(chat_id=chat_id,
                                    document=open(f"out/{user_id}/zip/{context.task['name']}.zip", 'rb'),
                                    parse_mode=ParseMode.MARKDOWN, caption=LOCALES['ready'])

    # чистим оставшиеся после использования бота файлы
    await asyncio.to_thread(clear_output, context.task['name'], user_id)

    context.is_generating = False

    return ConversationHandler.END


@answer_query
async def ready_warning(update: Update, context: CustomContext):
    """Показать предупреждение о неполной настройке новой работы"""

    user_id = str(update.effective_user.id)
    chat_id = update.effective_chat.id

    msg = await context.bot.send_message(chat_id=chat_id, text=LOCALES['ready_warning'], parse_mode=ParseMode.MARKDOWN)

    # удаляем предупреждение через 3 секунды
    context.job_queue.run_once(remove_alarm, 3, chat_id=chat_id, name=user_id, data=[chat_id, msg.message_id])

    return await main_menu_handler(update, context)
