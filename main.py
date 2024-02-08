from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import logging
from db import Db
import config

# задаем уровень логов
logging.basicConfig(level=logging.INFO)

token = config.BOT_TOKEN

bot = Bot(token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)



class Form(StatesGroup):
    addMovie = State()  # Состояние добавление фильма
    removeMovie = State() # Состояние удаление фильма
    editMovie = State() # Состояние редактирование фильма
    editTThisMovie = State() # Состояние редактирование выбраного фильма

# старт
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    markup_inline = types.InlineKeyboardMarkup(row_width=1)
    inlineBtn1 = types.InlineKeyboardButton('Подписаться на канал', url=config.BOT_SUBSCRIPTION_LINK)
    inlineBtn2 = types.InlineKeyboardButton('Проверить подписку', callback_data='subscription_check')
    markup_inline.add(inlineBtn1, inlineBtn2)
    await message.answer('Здравствуйте, отправьте нам код фильма и получите название фильма\nДля начало подпишитесь на этот канал:', reply_markup=markup_inline)

    # если id юзера = id админа - то даём возможность добавлять фильмы в базу данных
    if str(message.from_id) == config.BOT_ADMIN_ID:
        markup_reply = types.ReplyKeyboardMarkup(row_width=2)
        markup_reply.add(types.KeyboardButton('Добавить фильм 📝'), types.KeyboardButton('Удалить фильм 🗑'), types.KeyboardButton('Редактировать фильм ✏️'), types.KeyboardButton('Список фильмов 📋'))
        await message.answer('Вы админ этого канала.\nВы можете добавить/удалить/редактировать/фильмы, и так же получить список всех фильмов', reply_markup=markup_reply)


@dp.callback_query_handler()
async def callback(call):
    # кнопки
    btnData = call.message.reply_markup['inline_keyboard'][1][0]['callback_data']
    if btnData == 'subscription_check':
        # Проверка на подписку
        try:
            subscriptionStatus = await bot.get_chat_member(chat_id=config.BOT_SUBSCRIPTION, user_id=call.message.chat.id)
        except Exception:
            subscriptionStatus = 'left'

        subscriptionStatus = subscriptionStatus.status if 'status' in subscriptionStatus else subscriptionStatus

        if subscriptionStatus == 'member':
            await call.message.answer('Вы успешно подписались, теперь вы можете найти свой фильм')
        else:
            await call.message.answer('Вы не подписались, попробуйте еще раз подписаться')

# обработка кнопок для редактирования базы данных
@dp.message_handler(lambda message: message.text == 'Список фильмов 📋')
async def listOfMovies(message: types.Message):
    # если id юзера != id админа - то лишаем прав на эту функцию
    if str(message.from_id) != config.BOT_ADMIN_ID:
        await message.reply('Для поиска фильма нужно ввести код')
        return None

    # бд - соединение с БД
    db = Db()
    # получение списка фильмов
    data = db.listOfMovies()
    data = data if data != '' else 'В базе данных еще нет фильмов'
    await message.reply(data)
    # закрытие соединения
    db.close()

# добавление фильма в базу данных
@dp.message_handler(lambda message: message.text == 'Добавить фильм 📝')
async def addMovie(message: types.Message):
    # если id юзера != id админа - то лишаем прав на эту функцию
    if str(message.from_id) != config.BOT_ADMIN_ID:
        await message.reply('Для поиска фильма нужно ввести код')
        return None
    await message.reply("Введите название фильма и код. Пример ввода: название || код")
    await Form.addMovie.set()


# обработка ввода данных для добавления его в базу данных
@dp.message_handler(state=Form.addMovie)
async def addMovie(message: types.Message, state: FSMContext):
    data = message.text.split(' || ')
    if len(data) <= 1:
        await message.reply('Некорректные данные. Добавление фильма должно быть в таком формате: название || код')
    else:
        if len(data[0]) > 255:  # название
            await message.reply('Ошибка: Название должно быть меньше 255 символов')
        if len(data[1]) > 20:  # код
            await message.reply('Ошибка: Код должен быть меньше 20 символов')
        # добавление в бд
        db = Db()
        data = db.addMovie(data[0], data[1])
        await message.reply(data)
        db.close()
    # закрытие соединения
    await state.finish()

# удаление фильма из базы данных
@dp.message_handler(lambda message: message.text == 'Удалить фильм 🗑')
async def removeMovie(message: types.Message):
    # если id юзера != id админа - то лишаем прав на эту функцию
    if str(message.from_id) != config.BOT_ADMIN_ID:
        await message.reply('Для поиска фильма нужно ввести код')
        return None
    await message.reply("Введите код фильма, чтоб удалить его")
    await Form.removeMovie.set()

# обработка ввода данных для удаление фильма из базы данных
@dp.message_handler(state=Form.removeMovie)
async def removeMovie(message: types.Message, state: FSMContext):
    # удаление в бд
    db = Db()
    data = db.removeMovie(message.text)
    await message.reply(data)
    db.close()
    # закрытие соединения
    await state.finish()

# просим у юзера чтоб он ввел код для поиска фильма
@dp.message_handler(lambda message: message.text == 'Редактировать фильм ✏️')
async def editMovie(message: types.Message):
    # если id юзера != id админа - то лишаем прав на эту функцию
    if str(message.from_id) != config.BOT_ADMIN_ID:
        await message.reply('Для поиска фильма нужно ввести код')
        return None
    await message.reply("Введите код фильма, чтоб редактировать его")
    await Form.editMovie.set()

# поиск для редактирование фильма из базы данных
@dp.message_handler(state=Form.editMovie)
async def editMovie(message: types.Message, state: FSMContext):
    # поиск фильма в бд
    db = Db()
    data = db.searchMovies(message.text)
    if len(data) >= 1:
        await message.reply(f'Фильм найден.\nid: {data[0][0]}, название: {data[0][1]}, код: {data[0][2]}\nТеперь введите новые данные в таком формате: название || код')
        await state.update_data(code=message.text)
        await Form.editTThisMovie.set()
    else:
        await message.reply(f'Фильм не найден по коду: {message.text}')
        # закрытие соединения
        await state.finish()

    db.close()

# редактирование фильма в базе данных
@dp.message_handler(state=Form.editTThisMovie)
async def editTThisMovie(message: types.Message, state: FSMContext):
    code = await state.get_data()
    data = message.text.split(' || ')
    # валидация данных
    if len(data) <= 1:
        await message.reply('Некорректные данные. Редактирование фильма должно быть в таком формате: название || код')
    if len(data[0]) > 255: #название
        await message.reply('Ошибка: Название должно быть меньше 255 символов')
    if len(data[1]) > 20: #код
        await message.reply('Ошибка: Код должен быть меньше 20 символов')
    db = Db()
    dataEdit = db.editMovice(data[0], data[1], code['code'])
    await message.reply(dataEdit)
    db.close()
    # закрытие соединения
    await state.finish()

#сообщение от юзера (код фильма)
@dp.message_handler(content_types=['text'])
async def code(message: types.Message):
    try:
        # Проверка на подписку
        subscriptionStatus = await bot.get_chat_member(chat_id=config.BOT_SUBSCRIPTION, user_id=message.from_user.id)
    except Exception:
        subscriptionStatus = 'left'

    subscriptionStatus = subscriptionStatus.status if 'status' in subscriptionStatus else subscriptionStatus

    if subscriptionStatus == 'member':
        # бд - соединение с БД
        db = Db()
        # поиск фильма по коду
        data = db.searchMovies(message.text)
        data = f'Фильм по коду: {message.text}\n---------------\n' + data[0][1] if len(data) >= 1 else 'Фильм не найден'
        await message.answer(data)
        # закрытие соединения
        db.close()
    else:
        await message.answer('Вы не подписались, попробуйте еще раз подписаться')


#запуск
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)



