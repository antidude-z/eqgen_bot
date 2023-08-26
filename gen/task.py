"""Модуль, отвечающий за сборку новой работы и чистку лишних файлов после неё"""

import time
import shutil
import yaml
import logging
from pathlib import Path

from .templates import make_equations
from .latex import generate_answer_doc, generate_question_doc

logger = logging.getLogger(__name__)


def generate(task: dict, user_id: str) -> None:
    """Создать работу по заданным параметрам и сохранить результат в папке out"""

    t = time.time()  # для учёта затраченного времени на генерацию (дико долго xD)

    template_ids = list(yaml.load(open("data/equations/basic_templates.yaml", "r", encoding='utf-8'), yaml.Loader).keys())

    total_variants = task['variants']
    task_display_name = task['name']
    task_description = task['description']
    examples_conf: list[tuple] = task['examples']

    # Если пользователь впервые создаёт работу, создать необходимые папки для pdf- и zip-файлов

    path = Path(f"out/{user_id}")
    path.mkdir(exist_ok=True)
    (path / 'pdf').mkdir(exist_ok=True)
    (path / 'zip').mkdir(exist_ok=True)

    logger.info(f"User (id = {user_id}) has begun generating new task.\ntask = {task}")

    variants: list[tuple] = []

    for num in range(1, total_variants + 1):
        examples: list[dict] = []
        for eq_id, amount in examples_conf:
            # если айди нет в списке базовых шаблонов, сообщаем функции искать шаблон в 'custom/user_id'
            if eq_id in template_ids:
                example = make_equations(eq_id, amount)
            else:
                example = make_equations(eq_id, amount, user_id=user_id)
            examples.append(example)
        variants.append((num, examples))

        doc = generate_question_doc(num, task_display_name, task_description, examples)
        doc.generate_pdf(filepath=f"out/{user_id}/pdf/Вариант {num}", compiler="pdflatex")

    answers = generate_answer_doc(variants)
    answers.generate_pdf(filepath=f"out/{user_id}/pdf/Ответы", compiler="pdflatex")

    shutil.make_archive(f"out/{user_id}/zip/{task_display_name}", 'zip', str(path / 'pdf'))  # архивируем готовые пдфки

    logger.info(f"Used (id = {user_id}) successfully finished generation in {time.time() - t} seconds")
