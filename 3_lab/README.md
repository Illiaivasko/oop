# Звіт до роботи
## Тема: Знайомство з ООП
### Мета роботи: навчитися використовувати основні принципи ООП у Python, розглянути конструкції побудови класу, створення та ініціалізацію об'єктів, роботу зі змінними класу, атрибутами екземплярів, статичними методами та властивостями (@property).

---
### Виконання роботи
* **Результати виконання завдань та відповіді на контрольні запитання:**
  1. **Чому при передачі `None` створюється об'єкт з іменем `Anonymous`?**  
     У конструкторі `__init__` застосовано тернарний вираз: `self.name = name if name is not None else self.anonymous_user().name`. Якщо параметр `name` має значення `None`, інтерпретатор переходить до правої гілки виразу та викликає класовий метод `anonymous_user()`, який повертає екземпляр з іменем `"Anonymous"`.
  2. **Як змінити текст привітання при виклику методу `say_hello()`?**  
     Статичний метод `say_hello(message="...")` приймає необов'язковий параметр привітання. Якщо викликати метод без параметрів, повертається стандартний рядок `"Hello to everyone!"`. Для зміни тексту передаємо аргумент у виклик методу: `me.say_hello("Доброго дня викладачу Бугель Ю.О.!")`.
  3. **Функція підрахунку букв імені:**  
     У клас `MyName` додано метод `count_letters(self) -> int`, який використовує вбудовану функцію `len(self.name)` та повертає кількість символів в імені екземпляра.
  4. **Чому кількість імен у списку (4) відрізняється від значення `total_names` (5)?**  
     У списку `names` передано 4 значення: `"Bohdan"`, `"Marta"`, `"Illia"` та `None`. Коли черга доходить до `None`, у тілі конструктора викликається класовий метод `anonymous_user()`. Цей метод інстанціює окремий повноцінний екземпляр класу `cls("Anonymous")`, викликаючи для нього `__init__` та збільшуючи `MyName.total_names` на 1 (лічильник стає рівним 4). Потім повертається значення його імені в перший конструктор, який продовжує виконання і знову збільшує `MyName.total_names` на 1 (лічильник стає 5). Тобто для опрацювання одного `None` конструктор виконується двічі.
  5. **Автоматична капіталізація імені:**  
     У конструкторі додано виклик методу `.capitalize()`. Тепер навіть якщо передати рядок з маленької літери (наприклад, `"taras"`), атрибут `self.name` збереже коректне значення `"Taras"`.
  6. **Динамічний домен поштової скриньки:**  
     Метод `create_email(self, domain="itcollege.lviv.ua")` тепер приймає параметр домену із дефолтним значенням коледжу, що дозволяє генерувати електронну пошту для будь-яких сервісів (наприклад, `lpnu.ua` чи `gmail.com`).
  7. **Валідація імені:**  
     Додано перевірку `not name.isalpha()`. Якщо переданий рядок містить цифри або сторонні знаки, програма викликає виняток:
     ```python
     ValueError("Ім'я може містити лише літери!")
     ```
  8. **Властивість `full_name` та збереження у файл:**  
     Реалізовано властивість `@property full_name`, яка повертає рядок у форматі `User #<id>: <name> (<email>)`, та метод `save_to_file("users.txt")`, що автоматично дописує запис користувача у текстовий файл.

---

* Вставлений код програми (`app.py`):
```python
class MyName:
    """Опис класу / Документація роботи з об'єктами класу MyName"""
    total_names = 0  # Змінна класу (Class Variable)

    def __init__(self, name=None) -> None:
        """Ініціалізація екземпляра класу з валідацією та автоматичною капіталізацією"""
        if name is not None:
            # Завдання 7: перевірка на наявність лише літер
            if not isinstance(name, str) or not name.isalpha():
                raise ValueError("Ім'я може містити лише літери!")
            self.name = name.capitalize()
        else:
            # Завдання 1: якщо None, беремо ім'я від анонімного користувача
            self.name = self.anonymous_user().name

        MyName.total_names += 1
        self.my_id = self.total_names

    @property
    def whoami(self) -> str:
        """Властивість класу для отримання представлення імені"""
        return f"My name is {self.name}"

    @property
    def my_email(self) -> str:
        """Властивість класу для отримання поштової скриньки за замовчуванням"""
        return self.create_email()

    def create_email(self, domain: str = "itcollege.lviv.ua") -> str:
        """Метод екземпляра з динамічним доменом пошти (Завдання 6)"""
        return f"{self.name.lower()}@{domain}"

    def count_letters(self) -> int:
        """Метод підрахунку кількості літер в імені (Завдання 3)"""
        return len(self.name)

    @property
    def full_name(self) -> str:
        """Властивість повного представлення користувача (Завдання 8)"""
        return f"User #{self.my_id}: {self.name} ({self.my_email})"

    def save_to_file(self, filename: str = "users.txt") -> None:
        """Метод збереження запису користувача у файл (Завдання 9)"""
        with open(filename, "a", encoding="utf-8") as f:
            f.write(f"{self.full_name}\n")

    @classmethod
    def anonymous_user(cls):
        """Метод класу для створення анонімного користувача"""
        return cls("Anonymous")

    @staticmethod
    def say_hello(message="Hello to everyone!") -> str:
        """Статичний метод з кастомним привітанням (Завдання 2)"""
        return f"You say: {message}"


if __name__ == "__main__":
    print("Розпочинаємо створювати обєкти!")

    # Модифіковано програму: додано власне ім'я Illia
    names = ("Bohdan", "Marta", "Illia", None)
    all_names = {name: MyName(name) for name in names}

    for name, me in all_names.items():
        print(f"""{">*<"*20}
This is object: {me} 
This is object attribute: {me.name} / {me.my_id}
This is {type(MyName.whoami)}: {me.whoami} / {me.my_email}
This is {type(me.create_email)} call: {me.create_email()}
This is static {type(MyName.say_hello)} with defaults: {me.say_hello()} 
This is class variable {type(MyName.total_names)}: from class {MyName.total_names} / from object {me.total_names}
{"<*>"*20}""")

    print(f"\nМи завершили створення. Всього створено імен у системі: {MyName.total_names}!")

    # Демонстрація виконання індивідуальних завдань
    print("\n" + "="*50)
    print("ДЕМОНСТРАЦІЯ ВИКОНАННЯ ІНДИВІДУАЛЬНИХ ЗАВДАНЬ:")
    print("="*50)

    # 1. Кастомне привітання
    user = all_names["Illia"]
    print("1. Кастомне привітання:")
    print("  ", user.say_hello("Доброго дня викладачу Бугель Ю.О.!"))

    # 2. Підрахунок кількості літер
    print("\n2. Кількість літер в імені:")
    for n, obj in all_names.items():
        print(f"   Ім'я: {obj.name} -> {obj.count_letters()} літер")

    # 3. Автоматична капіталізація
    user_lower = MyName("taras")
    print("\n3. Перевірка капіталізації:")
    print(f"   Введено 'taras' -> Збережено: {user_lower.name}")

    # 4. Динамічний email домен
    print("\n4. Динамічний email домен:")
    print(f"   Стандартний: {user.create_email()}")
    print(f"   Кастомний: {user.create_email('lpnu.ua')}")

    # 5. Властивість full_name та збереження у файл
    print("\n5. Властивість full_name та збереження у файл:")
    print(f"   {user.full_name}")
    user.save_to_file("users.txt")
    print("   Запис успішно додано у файл users.txt")

    # 6. Валідація некоректного імені
    print("\n6. Перевірка валідації імені з цифрами:")
    try:
        invalid_user = MyName("User123")
    except ValueError as e:
        print(f"   Успішно спрацювала валідація: {e}")
```

---

* Результат виконання програми в терміналі:
```text
Розпочинаємо створювати обєкти!
>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<
This is object: <__main__.MyName object at 0x100fc31a0> 
This is object attribute: Bohdan / 1
This is <class 'property'>: My name is Bohdan / bohdan@itcollege.lviv.ua
This is <class 'method'> call: bohdan@itcollege.lviv.ua
This is static <class 'function'> with defaults: You say: Hello to everyone! 
This is class variable <class 'int'>: from class 5 / from object 5
<*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*>
>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<
This is object: <__main__.MyName object at 0x100fc3200> 
This is object attribute: Marta / 2
This is <class 'property'>: My name is Marta / marta@itcollege.lviv.ua
This is <class 'method'> call: marta@itcollege.lviv.ua
This is static <class 'function'> with defaults: You say: Hello to everyone! 
This is class variable <class 'int'>: from class 5 / from object 5
<*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*>
>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<
This is object: <__main__.MyName object at 0x100fc3260> 
This is object attribute: Illia / 3
This is <class 'property'>: My name is Illia / illia@itcollege.lviv.ua
This is <class 'method'> call: illia@itcollege.lviv.ua
This is static <class 'function'> with defaults: You say: Hello to everyone! 
This is class variable <class 'int'>: from class 5 / from object 5
<*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*>
>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<>*<
This is object: <__main__.MyName object at 0x100fc32c0> 
This is object attribute: Anonymous / 5
This is <class 'property'>: My name is Anonymous / anonymous@itcollege.lviv.ua
This is <class 'method'> call: anonymous@itcollege.lviv.ua
This is static <class 'function'> with defaults: You say: Hello to everyone! 
This is class variable <class 'int'>: from class 5 / from object 5
<*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*><*>

Ми завершили створення. Всього створено імен у системі: 5!

==================================================
ДЕМОНСТРАЦІЯ ВИКОНАННЯ ІНДИВІДУАЛЬНИХ ЗАВДАНЬ:
==================================================
1. Кастомне привітання:
   You say: Доброго дня викладачу Бугель Ю.О.!

2. Кількість літер в імені:
   Ім'я: Bohdan -> 6 літер
   Ім'я: Marta -> 5 літер
   Ім'я: Illia -> 5 літер
   Ім'я: Anonymous -> 9 літер

3. Перевірка капіталізації:
   Введено 'taras' -> Збережено: Taras

4. Динамічний email домен:
   Стандартний: illia@itcollege.lviv.ua
   Кастомний: illia@lpnu.ua

5. Властивість full_name та збереження у файл:
   User #3: Illia (illia@itcollege.lviv.ua)
   Запис успішно додано у файл users.txt

6. Перевірка валідації імені з цифрами:
   Успішно спрацювала валідація: Ім'я може містити лише літери!
```

---
### Висновок
Під час виконання лабораторної роботи я ознайомився з базовими концепціями об'єктно-орієнтованого програмування у Python. Я навчився створювати класи, ініціалізувати об'єкти за допомогою конструктора `__init__`, розрізняти змінні класу та атрибути конкретного екземпляра. Також я опанував використання декораторів `@property`, класових методів (`@classmethod`) і статичних методів (`@staticmethod`), реалізував валідацію вхідних даних через підняття винятків `ValueError` та налагодив запис структурованих даних у текстовий файл.
