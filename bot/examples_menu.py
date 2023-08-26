"""Меню №2: управление заданиями в проверочной работе"""

from telegram import Update, InlineKeyboardMarkup
from is_natural_number import isNaturalNumber

from .util import make_button, answer_query, handle_input, CustomContext
from . import EXAMPLES_ADD, EXAMPLES_REMOVE, EXAMPLES_EDIT, EXAMPLES_PREVIOUS, EXAMPLES_NEXT, \
    EXAMPLES_BACK_TO_MAIN, EXAMPLES_MENU, EXAMPLES_EDIT_INPUT, LOCALES


@answer_query
async def examples_menu_handler(update: Update, context: CustomContext):
    """Показать или обновить меню заданий"""

    keyboard = [
        [make_button('ex_previous_button', EXAMPLES_PREVIOUS),
         make_button('ex_add_button', EXAMPLES_ADD),
         make_button('ex_edit_button', EXAMPLES_EDIT),
         make_button('ex_remove_button', EXAMPLES_REMOVE),
         make_button('ex_next_button', EXAMPLES_NEXT)],
        [make_button('back_button', EXAMPLES_BACK_TO_MAIN)]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    text = LOCALES['examples_menu']

    if context.has_examples:
        n = 0
        for ex_id, ex_amount in context.task['examples']:
            ex_name = context.eq_names[ex_id]  # тривиальное название шаблона

            # выбираем ключ к локализации в зависимости от того, выбрано сейчас данное задание или нет
            locale = 'selected_example' if n == context.selected_example else 'unselected_example'
            ex_text = LOCALES[locale].format(ex_name, ex_amount)

            # нумеруем полученную в результате строку
            text += LOCALES['bold_num'].format(n + 1, ex_text)
            n += 1
    else:
        text += LOCALES['no_examples_1']  # если задания отсутствуют, выводим предупреждение взамен пустого меню

    await context.saved_message('main_menu').edit(text=text, reply_markup=reply_markup)

    return EXAMPLES_MENU


@answer_query
async def examples_previous(update: Update, context: CustomContext):
    """Выбрать предыдущее задание в списке"""

    if context.has_examples:
        context.selected_example -= 1
        if context.selected_example < 0:
            context.selected_example = len(context.task['examples']) - 1

    return await examples_menu_handler(update, context)


@answer_query
async def examples_next(update: Update, context: CustomContext):
    """Выбрать следующее задание в списке"""

    if context.has_examples:
        context.selected_example += 1
        if context.selected_example >= len(context.task['examples']):
            context.selected_example = 0

    return await examples_menu_handler(update, context)


@answer_query
async def examples_remove(update: Update, context: CustomContext):
    """Удалить выбранное в списке задание"""

    sel = context.selected_example
    if context.has_examples:
        # если выбранное задание - последнее в списке и при этом не первое с начала (т.е. существует более 1 задания),
        # подвинуть выделение на 1 индекс назад
        if sel == len(context.task['examples']) - 1 and sel > 0:
            context.selected_example -= 1
        context.task['examples'].pop(sel)  # в любом случае, удаляем изначально выбранный элемент

    return await examples_menu_handler(update, context)


@answer_query
async def examples_edit(update: Update, context: CustomContext):
    """Запросить у пользователя количество уравнений в задании"""
    if context.has_examples:
        await context.saved_message('input').create(text=LOCALES['ex_edit_input'])
        return EXAMPLES_EDIT_INPUT
    else:
        return await examples_menu_handler(update, context)


@handle_input(examples_menu_handler, examples_edit)
async def examples_edit_input(update: Update, context: CustomContext, text: str):
    """Проверить пользовательский ввод и сохранить полученное кол-во уравнений"""

    sel = context.selected_example
    name = context.task['examples'][sel][0]  # получаем название старого шаблона (оно таким и останется)

    # требования к вводу - натуральное число, меньшее либо равное 50
    try:
        amount = int(text)
        if isNaturalNumber(amount) and amount <= 50:
            context.task['examples'][sel] = (name, amount)  # пихаем по выделенному индексу новый кортеж имя-количество
        else:
            raise ValueError  # всё равно кидаем исключение, когда число слишком большое
        return True  # возвращаемся в меню заданий
    except (ValueError, TypeError):
        return False  # повторяем запрос на ввод
