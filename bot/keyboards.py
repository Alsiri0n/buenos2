from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


class Keyboard:
    """
    Класс реализует встроенную клавиатуру
    """
    def __init__(self):
        self.button1 = KeyboardButton('/Погода')
        self.button2 = KeyboardButton('/Курс')
        self.button3 = KeyboardButton('/Картинка')
        self.button4 = KeyboardButton('/Опрос')
        self.markup3 = ReplyKeyboardMarkup(resize_keyboard=True).add(self.button1).add(self.button2).add(self.button3).add(self.button4)

        self.markup4 = ReplyKeyboardMarkup().row(
            self.button1, self.button2, self.button3
        )

        self.markup5 = ReplyKeyboardMarkup().row(
            self.button1, self.button2, self.button3
        ).add(KeyboardButton('Средний ряд'))
