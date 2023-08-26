"""Меню №3: выбор/загрузка шаблонов уравнений"""

import sympy as sp
import yamale
from telegram import Update, InlineKeyboardMarkup
from telegram.constants import ParseMode
from pathlib import Path

from .util import answer_query, handle_input, make_button, remove_alarm, clear, CustomContext
from . import EQUATIONS_MENU, EQUATIONS_NEXT, EQUATIONS_PREVIOUS, EQUATIONS_UPLOAD, EQUATIONS_SELECT_1, \
    EQUATIONS_SELECT_2, EQUATIONS_SELECT_3, EQUATIONS_SELECT_4, EQUATIONS_BACK_TO_EX, EQUATIONS_UPLOAD_INPUT, \
    EQUATIONS_UPLOAD_INPUT_2, LOCALES, examples_menu, TEMPLATE_IDS

SCHEMA = yamale.make_schema("data/equations/schema.yaml")

# распределяем уравнения (т.е. пары айди - название) по страницам, 4 штуки на каждую, и сохраняем в equations
items = list(TEMPLATE_IDS.items())
equations = {}
for i in range(0, len(TEMPLATE_IDS), 4):
    equations[i // 4] = items[i: i + 4]

total_equations = len(equations)


@answer_query
async def equations_menu_handler(update: Update, context: CustomContext):
    """Показать или обновить меню шаблонов"""

    keyboard = [
        [make_button('eq_previous_button', EQUATIONS_PREVIOUS),
         make_button('eq_1_button', EQUATIONS_SELECT_1),
         make_button('eq_2_button', EQUATIONS_SELECT_2),
         make_button('eq_3_button', EQUATIONS_SELECT_3),
         make_button('eq_4_button', EQUATIONS_SELECT_4),
         make_button('eq_next_button', EQUATIONS_NEXT)],
        [make_button('upload_button', EQUATIONS_UPLOAD)],
        [make_button('back_button', EQUATIONS_BACK_TO_EX)]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    text = LOCALES['equations_menu']
    for n, x in enumerate(equations[context.eq_page]):
        text += LOCALES['bold_num'].format(n + 1, x[1])  # нумеруем и форматируем шаблоны в столбик
    text += LOCALES['page_num'].format(context.eq_page + 1, total_equations)  # "текущая страница / общее количество"

    await context.saved_message('main_menu').edit(text=text, reply_markup=reply_markup)

    return EQUATIONS_MENU


def add_equation(context: CustomContext, name: str):
    """Добавить в работу новое задание name с базовым количеством уравнений - 10"""
    if context.has_examples:  # если до этого уже были задания, переходим на один индекс вперёд (иначе вставляем в 0)
        context.selected_example += 1
    context.task['examples'].insert(context.selected_example, (name, 10))  # и вставляем туда же новое задание,
    # т.о оно сразу станет выделенным в списке заданий


def equations_select(n: int):
    """Обработчик выбора одного из базовых уравнений по кнопкам 1-4"""

    @answer_query
    async def _wrapper(update: Update, context: CustomContext):
        if n < len(equations[context.eq_page]):  # если уравнение с таким номером вообще существует на странице
            add_equation(context, equations[context.eq_page][n][0])  # добавляем задание

            return await examples_menu.examples_menu_handler(update, context)  # возвращаемся в меню заданий
    return _wrapper


@answer_query
async def equations_next(update: Update, context: CustomContext):
    """Перейти на следующую страницу списка шаблонов"""
    context.eq_page += 1
    if context.eq_page >= total_equations:
        context.eq_page = 0

    return await equations_menu_handler(update, context)


@answer_query
async def equations_previous(update: Update, context: CustomContext):
    """Перейти на предыдущую страницу списка шаблонов"""
    context.eq_page -= 1
    if context.eq_page < 0:
        context.eq_page = total_equations - 1

    return await equations_menu_handler(update, context)


@answer_query
async def equations_upload(update: Update, context: CustomContext):
    """Запросить у пользователя файл кастомного шаблона"""

    # целых два реплейса, потому что маркдаун отказывается работать с лишними . и _
    text = LOCALES['upload_1'].replace('/cancel_upload', '/cancel\_upload').replace('.', '\.')
    await context.saved_message('input').create(text=text, parse_mode=ParseMode.MARKDOWN_V2)

    return EQUATIONS_UPLOAD_INPUT


async def continue_upload(update: Update, context: CustomContext):
    """Запросить название шаблона после успешной загрузки файла"""
    return EQUATIONS_UPLOAD_INPUT_2


# вместо удаления запроса меняем его текст
@handle_input(continue_upload, equations_upload, file=True, edit_text=LOCALES['upload_2'])
async def equations_upload_input(update: Update, context: CustomContext, file):
    """Загрузить файл шаблона на диск и проверить его на ошибки"""

    file_id = file.file_unique_id
    user_id = str(update.effective_user.id)
    chat_id = update.effective_chat.id

    # если папки с шаблонами пользователя ещё нет, создать таковую
    path = Path(f"data/equations/custom/{user_id}")
    path.mkdir(exist_ok=True)

    file_path = path / f"{file_id}.yaml"

    await file.download_to_drive(file_path)  # скачиваем файл с серверов телеграма

    try:
        data = yamale.make_data(f"data/equations/custom/{user_id}/{file_id}.yaml")
        yamale.validate(SCHEMA, data)  # проверка структуры файла (разметка, типы данных etc.) на соответствие схеме

        # здесь отдельно проверяем, что семпай может обработать указанную в шаблоне форму уравнения
        for f in data[0][0]['form']:
            eq_text = f.split("=")
            sp.sympify(eq_text[0])
            sp.sympify(eq_text[1])
    except:
        # если произошла ошибка, отправляем 3-секундное сообщение о ней пользователю, удаляем файл
        # и возвращаемся в меню заданий
        msg = await context.bot.send_message(chat_id=chat_id, text=LOCALES['upload_error'], parse_mode=ParseMode.MARKDOWN)
        context.job_queue.run_once(remove_alarm, 3, chat_id=chat_id, name=user_id, data=[chat_id, msg.message_id])
        file_path.unlink()

        return False

    context.buffered_file_id = file_id  # если всё удачно, сохраняем айди файла и запрашиваем название шаблона

    return True


@handle_input(examples_menu.examples_menu_handler)
async def equations_upload_input_2(update: Update, context: CustomContext, text: str):
    """Добавить шаблон в список заданий под именем text"""
    add_equation(context, context.buffered_file_id)  # сначала добавляем новое задание в список
    context.eq_names[context.buffered_file_id] = clear(text)  # создаём для него локализацию (введенное юзером название)
    context.buffered_file_id = None  # чистим за собой следы и возвращаемся назад

    return True


async def cancel_upload(update: Update, context: CustomContext):
    """Отменить загрузку шаблона и вернуться в меню заданий"""
    await update.message.delete()
    await context.saved_message('input').delete()
    context.buffered_file_id = None

    return await examples_menu.examples_menu_handler(update, context)
