"""Работа с лэйтеком, создание документов"""

from pylatex import Command, Center, Section, Enumerate, NoEscape, Subsection, Document, FlushRight, LargeText, \
    FlushLeft


def generate_default_doc() -> Document:
    """Создать основу для будущего документа"""

    doc = Document(fontenc='T1,T2C', lmodern=False, textcomp=False,
                   geometry_options={"top": "0.75in", "bottom": "0.75in", "left": "0.75in", "right": "0.75in"})
    doc.preamble.append(Command('usepackage', "multicol"))
    doc.preamble.append(Command('usepackage', "amsmath"))
    doc.preamble.append(Command('usepackage', "amsfonts"))
    return doc


def generate_question_doc(variant_num: int, task_display_name: str, task_description: str, examples: list) -> Document:
    """Создать пдф-документ с заданиями"""

    # шапка документа из номера варианта, названия и описания
    doc = generate_default_doc()
    with doc.create(FlushRight()):
        doc.append(LargeText(f"Вариант {variant_num}"))
    with doc.create(Center()):
        doc.append(Command("LARGE"))
        doc.append(Command("textbf", task_display_name))
    with doc.create(FlushLeft()):
        doc.append(LargeText(Command('textit', task_description)))

    for num, example in enumerate(examples):  # нумеруем задания, оформляем в документе
        with doc.create(Section(f"Задание №{num + 1}", numbering=False)):
            doc.append(LargeText(Command('textit', example['description'])))
            cols = example['cols'][0]
            if cols > 1:  # если влезает больше одного уравнения в строку, делим на столбцы
                doc.append(Command("begin", ['multicols', str(cols)]))
            with doc.create(Enumerate()):  # нумеруем уже уравнения и пихаем форму в документ
                for equation in example['equations']:
                    doc.append(NoEscape(r"\item{$" + equation[0] + "$}"))
            if cols > 1:
                doc.append(Command("end", "multicols"))
    return doc


def generate_answer_doc(variants: list) -> Document:
    """Создать пдф-документ с ответами к заданиям"""

    # шапка документа
    doc = generate_default_doc()
    with doc.create(Center()):
        doc.append(Command("LARGE"))
        doc.append(Command("textbf", "Ответы к вариантам"))

    for var_num, examples in variants:  # разделяем варианты по секциям в документе
        with doc.create(Section(f"Вариант {var_num}", numbering=False)):
            for num, example in enumerate(examples):  # аналогично нумеруем задания и ответы,всё почти как в бланке выше
                with doc.create(Subsection(f"Задание №{num + 1}", numbering=False)):
                    cols = example['cols'][1]
                    if cols > 1:
                        doc.append(Command("begin", ['multicols', str(cols)]))
                    with doc.create(Enumerate()):
                        doc.append(Command("Large"))
                        for equation in example['equations']:
                            doc.append(NoEscape(r"\item{$" + equation[1] + "$}"))
                    if cols > 1:
                        doc.append(Command("end", "multicols"))
    return doc
