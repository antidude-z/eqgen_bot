"""Пакет для работы с функциями телеграм-бота"""

import json
import yaml

# отдельно написанный текст и элементы интерфейса
LOCALES: dict[str] = json.load(open('data/locales.json', 'r', encoding='utf-8'))

TEMPLATE_IDS: dict = yaml.load(open("data/equations/basic_templates.yaml", "r", encoding='utf-8'), yaml.Loader)

# константы для ConversationHandler'а
NAME_INPUT, DESCRIPTION_INPUT, VARIANTS_INPUT, VARIANTS, NAME, DESCRIPTION, EXAMPLES, MAIN_MENU, CREATE, EXAMPLES_MENU,\
    EXAMPLES_NEXT, EXAMPLES_PREVIOUS, EXAMPLES_ADD, EXAMPLES_REMOVE, EXAMPLES_EDIT, EXAMPLES_EDIT_INPUT, \
    EXAMPLES_BACK_TO_MAIN, EQUATIONS_MENU, EQUATIONS_NEXT, EQUATIONS_PREVIOUS, EQUATIONS_UPLOAD, EQUATIONS_SELECT_1, \
    EQUATIONS_SELECT_2, EQUATIONS_SELECT_3, EQUATIONS_SELECT_4, READY_WARNING, EQUATIONS_UPLOAD_INPUT, \
    EQUATIONS_BACK_TO_EX, EQUATIONS_UPLOAD_INPUT_2 = range(29)
