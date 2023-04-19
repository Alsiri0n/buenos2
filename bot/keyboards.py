from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


class Keyboard:
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
        inline_btn_1 = InlineKeyboardButton('Weee', callback_data='Weather')
        self.inline_kb1 = InlineKeyboardMarkup().add(inline_btn_1)
