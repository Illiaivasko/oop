#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Лабораторна робота: Основи програмування на Python
Студент: Івашко Ілля Богданович (КН-31)
Дисципліна: ООП
Викладач: Бугель
За матеріалами: BobasB/it_college/notes/04_python_basics
"""

import sys
from random import randint

# 1. Ознайомлення з основними типами даних
a = "змінна з текстом"
a1 = 'a'
b = 1  # числова змінна
b1 = 1.1
c = ["a", 1, 1.25, "Слово", a]  # List
d = {"a": "Слово", "b": 1, a: b}  # Dict
e = ("a", a)  # Tuple
f = {"ss", a + str(b)}  # Set

print(f"Текст: {a}, число: {b}, дійсне: {b1}")
print(f"Список (list): {c}")
print(f"Словник (dict): {d}")
print(f"Кортеж (tuple): {e}")
print(f"Множина (set): {f}")

# 2. Вбудовані константи та ключові слова
print("Перша константа: ", True)
print(f"Як можна так робити вивід? {True}")
print(f"Константа порожнечі: {None}, тип: {type(None)}")
print(f"Константа Ellipsis: {...}, тип: {type(...)}")

# 3. Вбудовані функції
print(abs(-12.5), f"є рівним {abs(12.5)}", "і якщо порівняти то: ", abs(-12.5) == abs(12.5))
print(f"Довжина списку c: {len(c)}")
print(f"Тип змінної b1: {type(b1)}")

# 4. Цикли for та while з else
letters = ["a", "b", "c"]
for i in range(len(letters)):
    print(f"На позиції {i} знаходиться буква {letters[i]}")
else:
    print("Ця конструкція безглузда!")

# 5. Розгалуження
A = randint(0, 1)
print(f"Значить А={A}" if A else f"Але може бути що А={A}")

# 6. try -> except -> finally
val = 0
try:
    print("Що буде якщо", 10 / val, "?")
except Exception as e:
    print("Невже це помилка >", e)
finally:
    print("О це так на тобі!")

# 7. Контекстний менеджер with
try:
    with open("README.md", "r", encoding="utf-8") as file:
        for idx, line in enumerate(file):
            if idx < 5:
                print(f"{idx})> {line.strip()}")
except FileNotFoundError:
    print("Файл README.md відсутній.")

# 8. Лямбда-функції
def a_b_func(first, second):
    return first, second

this_is_lambda = lambda first, age: f"Цей код написав: {first}, Мені {age:d} років"
print("Це просто функція:", a_b_func)
print("А це лямбда:", this_is_lambda)
print("Це її виклик:", this_is_lambda("Ілля", 18))
print(this_is_lambda(*a_b_func("Ілля", 18)))
