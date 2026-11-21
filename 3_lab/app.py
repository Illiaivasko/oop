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

    # 4. Динамічний домен пошти
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
