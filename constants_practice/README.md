# Відпрацювання заняття від 20.10.2026
## Дисципліна: ООП
### Викладач: Бугель
### Студент: Івашко Ілля (КН-31)
### Тема: Дослідження вбудованих констант у Python

---

### Хід роботи
У файлах `constants_practice.py` та `constants_practice.ipynb` виведено значення та тип для кожної з вказаних констант за допомогою функції `type()`:

```python
# Вбудовані константи в Python

print("True:", True, type(True))
print("False:", False, type(False))
print("None:", None, type(None))
print("Ellipsis:", ..., type(...))
print("NotImplemented:", NotImplemented, type(NotImplemented))
print("__debug__:", __debug__, type(__debug__))
```

Результат виконання:
```text
True: True <class 'bool'>
False: False <class 'bool'>
None: None <class 'NoneType'>
Ellipsis: Ellipsis <class 'ellipsis'>
NotImplemented: NotImplemented <class 'NotImplementedType'>
__debug__: True <class 'bool'>
```

---

### Висновок
Ознайомився з системними константами Python. Перевірив їхні типи: True та False мають тип bool, None має тип NoneType, три крапки належать до типу ellipsis, а NotImplemented та __debug__ повертають відповідні системні типи. Завдання виконано.
