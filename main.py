import asyncio.exceptions
import os

import aiohttp
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Command
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from bot.keyboards import Keyboard
from bot.config import setup_config
from aiohttp import ClientSession, ClientTimeout
from json import loads
from bot.messages import MESSAGES
from bot.utils import PollStates


class Application:
    """
    Класс служит для хранения в памяти необходимых переменных
    """
    config = None
    poll_states = PollStates()
    poll_question = ""
    poll_answers = []


app = Application()
setup_config(app, config_path=os.path.join(
    os.path.dirname(os.path.realpath(__file__)), ".env"
))

bot = Bot(token=app.config.tg_bot.token)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())
kb = Keyboard()


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply(MESSAGES['start'])


async def fetch(url: str, headers: dict = None) -> tuple[dict, int]:
    """
    Функция служит для асинхронного получения данных по url
    :param url: адрес подключения
    :param headers: необходимые заголовки для сессии (авторизация)
    :return:
    """
    my_timeout = ClientTimeout(
        total=10,  # default value is 5 minutes, set to `None` for unlimited timeout
        sock_connect=10,  # How long to wait before an open socket allowed to connect
        sock_read=10  # How long to wait with no data being read before timing out
    )
    if headers is None:
        headers = {}

    client_args = dict(
        headers=headers,
        trust_env=True,
        timeout=my_timeout
    )
    data = ""
    code = -1
    try:
        async with ClientSession(**client_args) as session:
            async with session.get(url) as response:
                try:
                    data, code = await response.text(), response.status
                except aiohttp.ClientConnectorError as e:
                    print(e)
                    data, code = [], "networkError"
                except aiohttp.ClientResponseError as e:
                    print(e)
                    data, code = [], "responseError"
    except aiohttp.ServerTimeoutError as e:
        print(e)
        data, code = "timeoutError", "timeoutError"
    except Exception as e:
        print(e)

    if code == 200:
        result = loads(data)
    elif code in (range(400, 418)):
        result = loads(data)["error"]["message"]
    elif code == "timeoutError":
        result = "Сервер недоступен, попробуйте позднее."
    elif code == "responseError":
        result = "Сервер не отвечает, попробуйте позднее."
    elif code == "networkError":
        result = "Проблемы с сетью, попробуй позднее."
    else:
        result = ""
    return result, code


async def task_for_weather(city="Moscow"):
    """
    Вспомогательная функция служит для получения информация о погоде в городе.
    :param city:
    :return:
    """

    url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={app.config.tg_bot.openweather}"
    result, code = await fetch(url)
    if code == 200 and result:
        data = result[0]
        lon, lat = round(data["lon"], 2), round(data["lat"], 2)
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={app.config.tg_bot.openweather}&lang=ru"
        # Получаем прогноз погоды по координатам
        result, code = await fetch(url)
        if code == 200:
            data = [result["main"]["temp"] - 273.15,
                    result["weather"][0]["description"],
                    result["main"]["humidity"],
                    result["name"]]
        return data, code
    else:
        return "Введите правильные данные", -1


@dp.message_handler(state='*', commands=["п", "Погода"], commands_prefix="!/")
async def weather(message: types.Message, command: Command.CommandObj):
    """
    Функция служит для обработки ответа пользователя
    :param message: сообщение от пользователя
    :param command: команда
    :return:
    """
    city = command.args
    if city:
        result, code = await task_for_weather(city=city)
    else:
        result, code = await task_for_weather()
    if code == 200 and result:
        await message.answer(
            f"""Сейчас в г. {result[3]}
                Температура:\t{result[0]:.2f}°C
                Влажность:\t{result[2]}%
                Облачность:\t{result[1]}
                
                
                Чтобы узнать погоду в своём городе можно указать его вручную, например !п Нью-Йорк""",
            reply_markup=kb.markup3)
    else:
        await message.answer(result, reply_markup=kb.markup3)


async def task_for_course(fr="RUB", to="USD", amount=100):
    """
    Вспомогательная функция для создания запроса к сайту с конвертером валют
    :param fr: из какой валюты
    :param to: в какую валюту
    :param amount: сумма
    :return:
    """
    url = f"https://api.apilayer.com/exchangerates_data/convert?to={to}&from={fr}&amount={amount}"
    headers = {
        "apikey": app.config.tg_bot.exchange
    }
    result, code = await fetch(url, headers)
    if code == 200:
        result = result["result"]
    return result, code


@dp.message_handler(state='*', commands=["к", "Курс"], commands_prefix="!/")
async def course(message: types.Message, command: Command.CommandObj):
    """
    Функция служит для обработки ответа пользователя
    :param message: сообщение от пользователя
    :param command: команда
    :return:
    """
    fr, to, amount = ["RUB", "USD", 100]
    if command.args:
        fr, to, amount = command.args.split()[:3]
    result, code = await task_for_course(fr=fr, to=to, amount=amount)

    if code == 200:
        await message.answer(f"{amount} {fr} = {result} {to}\n\n Можно использовать вручную, например, !к RUB USD 100",
                             reply_markup=kb.markup3)
    elif code in range(400, 418):
        await message.answer(result, reply_markup=kb.markup3)
    else:
        await message.answer(result, reply_markup=kb.markup3)


async def task_for_images() -> tuple[str, int]:
    """
    Вспомогательная функция для получения изображения с сайта
    :return:
    """
    url = f"https://api.pexels.com/v1/search?query=cats&per_page=1"
    headers = {
        "Authorization": app.config.tg_bot.pexels
    }
    result, code = await fetch(url, headers)
    if code == 200:
        result = result["photos"][0]["src"]["small"]
    return result, code


@dp.message_handler(state='*', commands=["Картинка"])
async def images(message: types.Message):
    """
    Функция служит для обработки ответа пользователя
    :param message:
    :return:
    """
    result, code = await task_for_images()
    if code == 200:
        await message.answer_photo(types.InputFile.from_url(result), reply_markup=kb.markup3)
    else:
        await message.answer(result, reply_markup=kb.markup3)


@dp.message_handler(state=app.poll_states.STATE_2_QUESTION, commands=["p", "Опрос"], commands_prefix="!/")
async def poll(message: types.Message):
    """
    Вспомогательная функция для создания голосования. Отправляет сформированное голосование в чат.
    :param message:
    :return:
    """
    await message.answer_poll(question=app.poll_question,
                              options=app.poll_answers,
                              is_anonymous=False,
                              reply_markup=kb.markup3)
    state = dp.current_state(user=message.from_user.id)
    await state.set_state(app.poll_states.all()[0])


@dp.message_handler(state=app.poll_states.STATE_1_ANSWER, commands=["p", "Опрос"], commands_prefix="!/")
async def poll_answers(message: types.Message, command: Command.CommandObj):
    """
    Вспомогательная функция, реализует получения вариантов ответа на голосование
    :param message: сообщение от пользователя
    :param command: команда
    :return:
    """
    if command.args:
        type_of_poll = command.args.split()[0]
        if type_of_poll == "a":
            state = dp.current_state(user=message.from_user.id)
            await state.set_state(app.poll_states.all()[2])
            app.poll_answers = command.args.split()[1:]
        await message.reply('Ответы записаны. Введите !p для создания опроса.', reply=False)


@dp.message_handler(state="*", commands=["p", "Опрос"], commands_prefix="!/")
async def poll_question(message: types.Message, command: Command.CommandObj):
    """
    Вспомогательная функция реализует получение вопроса для голосования
    :param message: сообщение от пользователя
    :param command: команда
    :return:
    """
    if command.args:
        type_of_poll = command.args.split()[0]
        if type_of_poll == "q":
            state = dp.current_state(user=message.from_user.id)
            await state.set_state(app.poll_states.all()[1])
            app.poll_question = str(command.args[2:])
        await message.reply('Вопрос записан. Введите ответы через пробел !p a Да Нет Наверное', reply=False)
    else:
        await message.reply('Для создания опроса введитe !p q Ваш Вопрос?', reply=False)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
