"""Вспомогательные функции и классы для бота"""

import string
from pathlib import Path

from telegram import Update, InlineKeyboardButton
from telegram.ext import CallbackContext, Application
from telegram.error import BadRequest
from telegram.constants import ParseMode
from typing import Callable

from . import LOCALES


class CustomContext(CallbackContext):
    """Модификация контекста для удобства работы с user_data"""

    def __init__(self, application: Application, chat_id=None, user_id=None) -> None:
        super().__init__(application=application, chat_id=chat_id, user_id=user_id)
        self.chat_id = chat_id

    def saved_message(self, msg_name: str):
        """Получить доступ к сохраненному в user_data сообщению"""
        return SavedMessage(self, msg_name, self.chat_id)

    @property
    def has_examples(self) -> int:
        """Проверить наличие добавленных заданий у пользователя"""
        return len(self.task['examples']) > 0

    @staticmethod
    def get_user_data(x: str) -> Callable:
        """Создать функцию для получения пользовательских данных по ключу x"""
        def _wrapper(cls):
            return cls.user_data.get(x)  # либо значение ключа x, либо None
        return _wrapper

    @staticmethod
    def set_user_data(x: str) -> Callable:
        """Создать функцию для установки пользовательских данных по ключу x"""
        def _wrapper(cls, value):
            cls.user_data[x] = value
        return _wrapper

    # Создаём свойства для всех польз. данных кроме main_menu_msg и input_msg, которые обрабатываются отдельно
    # buffered_file_id - промежуточно сохраненный айди кастомного шаблона
    # eq_names - локализация айдишников базовых и кастомных шаблонов
    # eq_page - номер страницы в списке шаблонов
    # selected_example - номер выбранного задания в списке заданий
    # is_generating - идёт ли у пользователя генерация работы (чтобы предотвратить лишние нажатия кнопки "Готово")
    # task - параметры генерируемой работы

    buffered_file_id = property(fget=get_user_data('buffered_file_id')).setter(set_user_data('buffered_file_id'))
    eq_names = property(fget=get_user_data('eq_names')).setter(set_user_data('eq_names'))
    eq_page = property(fget=get_user_data('eq_page')).setter(set_user_data('eq_page'))
    selected_example = property(fget=get_user_data('selected_example')).setter(set_user_data('selected_example'))
    is_generating = property(fget=get_user_data('is_generating')).setter(set_user_data('is_generating'))
    task = property(fget=get_user_data('task')).setter(set_user_data('task'))


class SavedMessage:
    """Сообщение с сохранённым айди для дальнейшей работы с ним"""

    def __init__(self, context: CustomContext, msg_name, chat_id):
        self.context = context
        self.msg_name = msg_name + "_msg"
        self.chat_id = chat_id

    @property
    def msg_id(self) -> int:
        """Свойство, содержащее айди данного сообщения"""
        return self.context.user_data.get(self.msg_name)  # аналогично, user_data[x] либо None

    @msg_id.setter
    def msg_id(self, value) -> None:
        """Сменить айди сообщения на другой"""
        self.context.user_data[self.msg_name] = value

    async def create(self, text: str, parse_mode=ParseMode.MARKDOWN, **kwargs):
        """Создать это сообщение, если оно ещё не существует"""
        if not self.msg_id:
            msg = await self.context.bot.send_message(chat_id=self.chat_id, text=text, parse_mode=parse_mode, **kwargs)
            self.msg_id = msg.message_id  # сохраняем айди нового сообщения на будущее

    async def edit(self, text: str, parse_mode=ParseMode.MARKDOWN, **kwargs):
        """Изменить текст и другие параметры сообщения"""
        if self.msg_id:
            try:
                await self.context.bot.edit_message_text(chat_id=self.chat_id, message_id=self.msg_id, text=text,
                                                         parse_mode=parse_mode, **kwargs)
            except BadRequest:  # ругается, если тексты новго и старого сообщений совпали (т.е. осталось без изменений)
                pass

    async def delete(self):
        """Удалить сообщение"""
        if self.msg_id:
            try:
                await self.context.bot.delete_message(chat_id=self.chat_id, message_id=self.msg_id)
            except BadRequest:
                pass
            self.msg_id = None  # сбрасываем айди


def answer_query(func: Callable) -> Callable:
    """Декоратор ответа на query-запрос при срабатывании хэндлера"""

    async def answered(update: Update, context: CustomContext):
        query = update.callback_query
        if query is not None:
            await query.answer()

        return await func(update, context)

    return answered


def handle_input(success_func: Callable, fail_func: Callable = None, file: bool = False, edit_text: str = None) -> Callable:
    """Декоратор, обрабатывающий пользовательский ввод"""

    def ti_decorator(func: Callable) -> Callable:
        async def _wrapper(update: Update, context: CustomContext):
            # получаем ввод
            result = await update.message.effective_attachment.get_file() if file else update.message.text

            # удаляем сообщение пользователя, больше оно не нужно
            await update.message.delete()

            # если обернутая функция вернула True, изменяем/удаляем сообщение бота и выполняем success_func,
            # иначе выполняем fail_func
            if await func(update, context, result):
                msg = context.saved_message('input')
                if edit_text:
                    await msg.edit(edit_text)
                else:
                    await msg.delete()

                return await success_func(update, context)
            else:
                return await fail_func(update, context)

        return _wrapper

    return ti_decorator


def clear(s: str) -> str:
    """Очистить строку от символов пунктуации для корректного отображения в интерфейсе"""
    for letter in string.punctuation:
        s = s.replace(letter, '')
    return s


def make_button(locale_name: str, callback_id: int) -> InlineKeyboardButton:
    """Упрощение создания кнопок в reply_markup'ах"""
    return InlineKeyboardButton(LOCALES[locale_name], callback_data=str(callback_id))


async def remove_alarm(context: CustomContext) -> None:
    """Удалить сообщение по прошествию заданного времени"""
    await context.bot.delete_message(chat_id=context.job.data[0], message_id=context.job.data[1])


def clear_output(name: str, user_id: str) -> None:
    """Очистить out/user_id и equations/custom/user_id"""

    path = Path(f"out/{user_id}")
    if path.exists():
        for x in (path / 'pdf').glob("*.pdf"):
            Path(x).unlink()
        (path / 'zip' / f'{name}.zip').unlink(missing_ok=True)

    path2 = Path(f"data/equations/custom/{user_id}")
    if path2.exists():
        for x in path2.glob("*.yaml"):
            Path(x).unlink()
