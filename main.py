#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Входная точка приложения, запускающая телеграм-бота и необходимые модули вместе с ним."""

import logging
from telegram.ext import ApplicationBuilder, CommandHandler, filters, MessageHandler,\
    CallbackQueryHandler, ConversationHandler, ContextTypes

from bot.main_menu import variants, name, description, variants_input, name_input, description_input, generate, \
    ready_warning, main_menu_handler

from bot.examples_menu import examples_previous, examples_next, examples_edit, examples_remove, \
    examples_edit_input, examples_menu_handler

from bot.equations_menu import equations_menu_handler, equations_upload, equations_upload_input_2, \
    equations_upload_input, equations_previous, equations_select, equations_next, cancel_upload

from bot.common_handlers import begin, start, about, error_handler, delete_fallback_messages, cancel

from bot.util import CustomContext

from bot import *

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filemode='w',
    filename='data/application.log'
)
logger = logging.getLogger(__name__)

context_types = ContextTypes(context=CustomContext)

application = ApplicationBuilder().token(open('data/token.txt', 'r').read()).context_types(
    context_types).concurrent_updates(True).build()

start_handler = CommandHandler(['start', 'help'], start)
about_handler = CommandHandler('about', about)

# entry_points - запускает меню генерации
# states - "состояния", при нахождении в которых обрабатываются (ожидаются) лишь указанные хэндлеры
# fallbacks - хэндлеры, которые обрабатываются, если ни один из других хэндлеров не прокатил

generate_handler = ConversationHandler(
    entry_points=[CommandHandler("generate", begin)],
    states={
        VARIANTS_INPUT: [MessageHandler(filters.TEXT, variants_input)],
        NAME_INPUT: [MessageHandler(filters.TEXT, name_input)],
        DESCRIPTION_INPUT: [MessageHandler(filters.TEXT, description_input)],
        EXAMPLES_EDIT_INPUT: [MessageHandler(filters.TEXT, examples_edit_input)],
        EQUATIONS_UPLOAD_INPUT: [MessageHandler(filters.ATTACHMENT, equations_upload_input),
                                 CommandHandler("cancel_upload", cancel_upload)],
        EQUATIONS_UPLOAD_INPUT_2: [CommandHandler("cancel_upload", cancel_upload),
                                   MessageHandler(filters.TEXT, equations_upload_input_2)],
        MAIN_MENU: [
            CallbackQueryHandler(name, pattern="^" + str(NAME) + "$"),
            CallbackQueryHandler(description, pattern="^" + str(DESCRIPTION) + "$"),
            CallbackQueryHandler(variants, pattern="^" + str(VARIANTS) + "$"),
            CallbackQueryHandler(examples_menu_handler, pattern="^" + str(EXAMPLES) + "$"),
            CallbackQueryHandler(generate, pattern="^" + str(CREATE) + "$"),
            CallbackQueryHandler(ready_warning, pattern="^" + str(READY_WARNING) + "$")
        ],
        EXAMPLES_MENU: [
            CallbackQueryHandler(equations_menu_handler, pattern="^" + str(EXAMPLES_ADD) + "$"),
            CallbackQueryHandler(examples_remove, pattern="^" + str(EXAMPLES_REMOVE) + "$"),
            CallbackQueryHandler(examples_edit, pattern="^" + str(EXAMPLES_EDIT) + "$"),
            CallbackQueryHandler(examples_next, pattern="^" + str(EXAMPLES_NEXT) + "$"),
            CallbackQueryHandler(examples_previous, pattern="^" + str(EXAMPLES_PREVIOUS) + "$"),
            CallbackQueryHandler(main_menu_handler, pattern="^" + str(EXAMPLES_BACK_TO_MAIN) + "$")
        ],
        EQUATIONS_MENU: [
            CallbackQueryHandler(equations_select(0), pattern="^" + str(EQUATIONS_SELECT_1) + "$"),
            CallbackQueryHandler(equations_select(1), pattern="^" + str(EQUATIONS_SELECT_2) + "$"),
            CallbackQueryHandler(equations_select(2), pattern="^" + str(EQUATIONS_SELECT_3) + "$"),
            CallbackQueryHandler(equations_select(3), pattern="^" + str(EQUATIONS_SELECT_4) + "$"),
            CallbackQueryHandler(equations_next, pattern="^" + str(EQUATIONS_NEXT) + "$"),
            CallbackQueryHandler(equations_previous, pattern="^" + str(EQUATIONS_PREVIOUS) + "$"),
            CallbackQueryHandler(equations_upload, pattern="^" + str(EQUATIONS_UPLOAD) + "$"),
            CallbackQueryHandler(examples_menu_handler, pattern="^" + str(EQUATIONS_BACK_TO_EX) + "$"),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel),
               MessageHandler(filters.ALL, delete_fallback_messages)]
)

application.add_handler(start_handler)
application.add_handler(about_handler)
application.add_handler(generate_handler)

application.add_error_handler(error_handler)

application.run_polling()