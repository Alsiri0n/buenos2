import os
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


async def fetch(session, url) -> ClientSession.get:
    async with session.get(url) as response:
        try:
            data = await response.text(), response.status
        except TimeoutError as e:
            data = "", "timeoutError"
        except BaseException as e:
            print(e)
            data = "", "timeoutError"
        return data


async def task_for_weather(city="Moscow"):
    url_for_coord = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={app.config.tg_bot.openweather}"
    async with ClientSession() as session:
        result, code = await fetch(session, url_for_coord)
        data = loads(result)[0]
        lon, lat = round(data["lon"], 2), round(data["lat"], 2)
        url_weather = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={app.config.tg_bot.openweather}&lang=ru"
        result, code = await fetch(session, url_weather)
        result = loads(result)
        data = [result["main"]["temp"] - 273.15,
                result["weather"][0]["description"],
                result["main"]["humidity"],
                result["name"]]
    return data


@dp.message_handler(state='*', commands=["п", "Погода"], commands_prefix="!/")
async def weather(message: types.Message, command: Command.CommandObj):
    city = command.args
    if city:
        result = await task_for_weather(city=city)
    else:
        result = await task_for_weather()
    await message.answer(
        f"""Сейчас в г. {result[3]}
            Температура:\t{result[0]:.2f}°C
            Влажность:\t{result[2]}%
            Облачность:\t{result[1]}
            
            
            Чтобы узнать погоду в своём городе можно указать его вручную, например !п Нью-Йорк""",
        reply_markup=kb.markup3)


async def task_for_course(fr="RUB", to="USD", amount=100):
    url = f"https://api.apilayer.com/exchangerates_data/convert?to={to}&from={fr}&amount={amount}"
    headers = {
        "apikey": app.config.tg_bot.exchange
    }
    my_timeout = ClientTimeout(
        total=None,  # default value is 5 minutes, set to `None` for unlimited timeout
        sock_connect=10,  # How long to wait before an open socket allowed to connect
        sock_read=10  # How long to wait with no data being read before timing out
    )

    client_args = dict(
        headers=headers,
        trust_env=True,
        timeout=my_timeout
    )
    async with ClientSession(**client_args) as session:
        try:
            response, code = await fetch(session, url)
        except TimeoutError as e:
            response, code = "timeoutError", "timeoutError"
    if code == 200:
        result = loads(response)["result"]
    elif code == 400:
        result = loads(response)["error"]["message"]
        # print(response, code)
    elif code == "timeoutError":
        result = "Сервер недоступен, попробуйте позднее"
    else:
        result = ""
    return result


@dp.message_handler(state='*', commands=["к", "Курс"], commands_prefix="!/")
async def course(message: types.Message, command: Command.CommandObj):
    fr, to, amount = ["RUB", "USD", 100]
    if command.args:
        fr, to, amount = command.args.split()[:3]
    result = await task_for_course(fr=fr, to=to, amount=amount)
    if result == "Сервер недоступен, попробуйте позднее":
        await message.answer(result, reply_markup=kb.markup3)
    elif result == 'You have entered an invalid "from" property. [Example: from=EUR]':
        await message.answer(result, reply_markup=kb.markup3)
    elif result == 'You have entered an invalid "to" property. [Example: to=GBP]':
        await message.answer(result, reply_markup=kb.markup3)
    else:
        await message.answer(f"{amount} {fr} = {result} {to}\n\n Можно использовать вручную, например, !к RUB USD 100",
                             reply_markup=kb.markup3)


async def task_for_images():
    url = f"https://api.pexels.com/v1/search?query=cats&per_page=1"
    headers = {
        "Authorization": app.config.tg_bot.pexels
    }
    my_timeout = ClientTimeout(
        total=None,  # default value is 5 minutes, set to `None` for unlimited timeout
        sock_connect=10,  # How long to wait before an open socket allowed to connect
        sock_read=10  # How long to wait with no data being read before timing out
    )

    client_args = dict(
        headers=headers,
        trust_env=True,
        timeout=my_timeout
    )
    async with ClientSession(**client_args) as session:
        try:
            response, code = await fetch(session, url)
        except TimeoutError as e:
            response, code = "timeoutError", "timeoutError"
    if code == 200:
        result = loads(response)["photos"][0]["src"]["small"]
    elif code == 400:
        result = loads(response)["error"]["message"]
        # print(response, code)
    elif code == "timeoutError":
        result = "Сервер недоступен, попробуйте позднее"
    else:
        result = ""
    return result


@dp.message_handler(state='*', commands=["Картинка"])
async def picture(message: types.Message):
    result = await task_for_images()
    # print(result)
    await message.answer_photo(types.InputFile.from_url(result), reply_markup=kb.markup3)


@dp.message_handler(state=app.poll_states.STATE_3_ENDED, commands=["p", "Опрос"], commands_prefix="!/")
async def poll(message: types.Message):
    await message.answer_poll(question=app.poll_question,
                              options=app.poll_answers,
                              is_anonymous=False,
                              reply_markup=kb.markup3)
    state = dp.current_state(user=message.from_user.id)
    await state.set_state(app.poll_states.all()[0])


@dp.message_handler(state=app.poll_states.STATE_2_QUESTION, commands=["p", "Опрос"], commands_prefix="!/")
async def poll_answers(message: types.Message, command: Command.CommandObj):
    if command.args:
        type_of_poll = command.args.split()[0]
        if type_of_poll == "a":
            state = dp.current_state(user=message.from_user.id)
            await state.set_state(app.poll_states.all()[3])
            app.poll_answers = command.args.split()[1:]
        await message.reply('Ответы записаны. Введите !p для создания опроса.', reply=False)


@dp.message_handler(state="*", commands=["p", "Опрос"], commands_prefix="!/")
async def poll_question(message: types.Message, command: Command.CommandObj):
    if command.args:
        type_of_poll = command.args.split()[0]
        if type_of_poll == "q":
            state = dp.current_state(user=message.from_user.id)
            await state.set_state(app.poll_states.all()[2])
            app.poll_question = str(command.args[2:])
        await message.reply('Вопрос записан. Введите ответы через пробел !p a Да Нет Наверное', reply=False)


@dp.message_handler(state='*')
async def default(message: types.Message):
    state = dp.current_state(user=message.from_user.id)
    current_state = await state.get_state()
    print(current_state)
    print(app.poll_states.all())
    await state.set_state(app.poll_states.STATE_0_DEFAULT)

    await message.answer(message.text + MESSAGES["state_reset"])

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
