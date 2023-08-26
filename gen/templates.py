"""Модуль низкоуровневой генерации уравнений, включая работу с БД и sympy"""

import sympy as sp
import yaml
import random
import sqlite3 as sl


def make_equations(eq_id: str, amount: int, user_id: str = None) -> dict:
    """Создать уравнения в количестве amount по заданному в eq_id шаблону"""

    if not user_id:  # ищем шаблон в зависимости от того, кастомный он или нет
        conf = yaml.load(open(f"data/equations/basic/{eq_id}.yaml", "r", encoding='utf-8'), yaml.Loader)
    else:
        conf = yaml.load(open(f"data/equations/custom/{user_id}/{eq_id}.yaml", "r", encoding='utf-8'), yaml.Loader)

    # превращаем строчки с формой уравнения (или системы ур-ий) в удобоваримый семпаем формат
    forms = []
    for f in conf['form']:
        x = f.split("=")
        forms.append(sp.Eq(sp.sympify(x[0]), sp.sympify(x[1]), evaluate=False))

    # создаём словарь с доступными значениями аргументов (range + include - exclude)
    ranges = {}
    for arg_name, arg in conf['arguments'].items():
        ranges[arg_name] = list(range(*arg['range'])) + arg['include']
        for i in arg['exclude']:
            ranges[arg_name].remove(i)

    roots = sp.symbols(" ".join(conf['roots']))  # помечаем, какие из неизвестных - корни

    con = sl.connect("data/equations/pregen.db")

    if not user_id:
        # создаём таблицу для шаблона в базе данных, если таковой нет, и получаем из неё все уравнения (если есть)
        with con:
            check = con.execute(f"SELECT count(*) from sqlite_master where type='table' and name='{eq_id}'")
            if not list(check)[0][0]:
                con.execute(f"CREATE TABLE {eq_id} (form TEXT, solution TEXT);")
            equations_in_db = list(con.execute(f"select * from {eq_id}"))

        n = len(equations_in_db)

        # итоговое количество уравнений должно быть в минимум 10 раз больше требуемого кол-ва
        # поэтому по-настоящему мы генерируем только либо недостающие до "превосходства",
        # либо просто небольшое количество

        db_supremacy = 10 * amount
        if n < db_supremacy:
            eq_to_gen = db_supremacy - n
        else:
            eq_to_gen = 50
    else:
        eq_to_gen = amount  # если шаблон кастомный, генерируем ровно столько, сколько требуется

    generated_equations = []
    # для последующего расчёта кол-ва столбцов в задании (красивая разметка всё такое...)
    max_solution_length = 0
    max_form_length = 0

    for _ in range(eq_to_gen):
        arguments = {arg: random.choice(ranges[arg]) for arg in ranges}.items()  # подбираем рандомные значения арг-ов
        if len(forms) == 1:
            # подставляем аргументы в ур-е, решаем его, превращаем форму и ответ в лэйтек-формат
            final_eq = forms[0].subs(arguments, simultaneous=True)
            eq_text = sp.latex(final_eq)
            if len(eq_text) > max_form_length:
                max_form_length = len(eq_text)
            solution = sp.latex(sp.solveset(final_eq, roots))
        else:
            # аналогично для систем, только форма оформляется скобками
            eqs = [f.subs(arguments, simultaneous=True) for f in forms]
            texts = []
            for eq in sp.FiniteSet(*eqs):
                t = sp.latex(eq)
                if len(t) > max_form_length:
                    max_form_length = len(t)
                texts.append(t)
            eq_text = r"\begin{cases}" + r"\\".join(texts) + r"\end{cases}"
            solution = sp.latex(sp.nonlinsolve(eqs, roots))
        if len(solution) > max_solution_length:
            max_solution_length = len(solution)
        generated_equations.append((eq_text, solution))

    if not user_id:
        # пихаем созданные ур-я в БД, объединяем новые и существующие в единый список
        with con:
            con.executemany(f'INSERT INTO {eq_id} VALUES(?, ?)', generated_equations)
        all_equations = generated_equations + equations_in_db

        selected_equations = []
        hashes = []
        count = 0

        # производим рандомную выборку требуемого кол-ва уравнений из общего списка, исключая повторы с помощью хэшей
        while count != amount:
            eq = random.choice(all_equations)
            if hash(eq[0]) in hashes:
                continue
            hashes.append(hash(eq[0]))
            selected_equations.append(eq)
            count += 1
    else:
        selected_equations = generated_equations  # для кастомных ничего не меняется, отправляем все созданные ур-я

    return {'equations': selected_equations,
            'cols': [min(round(100 / max_form_length), 5), min(round(100 / max_solution_length), 5)],
            'description': conf['description']}
