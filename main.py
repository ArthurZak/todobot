from telebot import TeleBot, types
import random
from datetime import date
from data_check import date2date, sorted_dates
from telegram_bot_calendar import DetailedTelegramCalendar
import configparser
import boto3
from botocore.exceptions import ClientError

HELP = """
Данный бот создан для ведения списка задач.
Всё управление ботом осуществляется при помощи кнопок меню. 

Для добавление задачи необходимо нажать кнопку "Добавить задачу", затем написать задачу
и далее выбрать необходимую дату, на которую хотите добавить задачу.
Для удаления или отметки задачи выполненной необходимо нажать соответствующую кнопку
и далее выбрать день и нужную задачу.  
"""

random_tasks = ['Поучить английский', 'Позаниматься спортом', 'Почитать книгу', 'Решить судоку', 'Порисовать',
                'Посмотреть новый фильм', 'Погулять', 'Поспать', 'Приготовить необычное блюдо']


def read_user(user_id):
    config1 = configparser.ConfigParser()
    config1.read("tokens.ini")
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url=config['TOKENS']['USER_STORAGE_URL'],
        region_name='us-east-1',
        aws_access_key_id=config['TOKENS']['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=config['TOKENS']['AWS_SECRET_ACCESS_KEY']
    )
    table = dynamodb.Table('Users_tasks')
    try:
        response = table.get_item(Key={'user_id': str(user_id)})
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        return response


def create_user(user_id, user_data):
    config1 = configparser.ConfigParser()
    config1.read("tokens.ini")
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url=config['TOKENS']['USER_STORAGE_URL'],
        region_name='us-east-1',
        aws_access_key_id=config['TOKENS']['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=config['TOKENS']['AWS_SECRET_ACCESS_KEY']
    )
    table = dynamodb.Table('Users_tasks')
    response = table.put_item(
        Item={
            'user_id': str(user_id),
            'user_data': user_data
        }
    )
    return response


def add_todo(Date, task, message):
    tasks = {message.chat.id: read_user(message.chat.id)['Item']['user_data']['tasks']}
    if Date in tasks[message.chat.id]:
        tasks[message.chat.id][Date].append(task)
        user_data = {'tasks': tasks[message.chat.id]}
        create_user(message.chat.id, user_data)
    else:
        tasks[message.chat.id][Date] = []
        tasks[message.chat.id][Date].append(task)
        user_data = {'tasks': tasks[message.chat.id]}
        create_user(message.chat.id, user_data)


def get_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_menu = types.KeyboardButton('Меню')
    markup.add(button_menu)
    return markup


def start_cal(m):
    msg_task = m.text
    print(msg_task)
    calendar, step = DetailedTelegramCalendar().build()
    bot.send_message(m.chat.id,
                     f"{m.text}",
                     reply_markup=calendar)

    @bot.callback_query_handler(func=DetailedTelegramCalendar.func())
    def cal(c):
        result, key, step1 = DetailedTelegramCalendar().process(c.data)
        if not result and key:
            bot.edit_message_text(f"{c.message.text}",
                                  c.message.chat.id,
                                  c.message.message_id,
                                  reply_markup=key)
        elif result:
            d = str(result).split('-')
            Date = '.'.join(d[::-1])
            msg = bot.edit_message_text(f"{Date} {c.message.text}",
                                        c.message.chat.id,
                                        c.message.message_id)
            add_task(msg)


# Регистрирует функцию ниже в качестве обработчика
def get_help(message):
    bot.send_message(message.chat.id, f'{HELP}')


def add_task(message):
    tasks = {message.chat.id: read_user(message.chat.id)['Item']['user_data']['tasks']}
    if message.chat.id in tasks:
        command = message.text.split(maxsplit=1)
        Date = date2date(command[0])
        task = command[1].capitalize()
        if len(task) < 3:
            text = 'Задача слишком короткая!'
        elif Date == 'Неверная дата':
            text = 'Неверно введена дата!\nСписок доступных для ввода форматов дат можно ' \
                   'посмотреть по команде /formatdates'
        else:
            add_todo(Date, task, message)
            text = f'Задача "{task}" добавлена на {Date}'
        bot.edit_message_text(f'{text}', message.chat.id, message.message_id)
        print(tasks)
    else:
        bot.send_message(message.chat.id, 'Для начала нажмите /start')


def random_task_add(message):
    tasks = {message.chat.id: read_user(message.chat.id)['Item']['user_data']['tasks']}
    if message.chat.id in tasks:
        Date = date2date('сегодня')
        task = random.choice(random_tasks).capitalize()
        if Date in tasks[message.chat.id] and (task in tasks[message.chat.id][Date] or
                                               f'{task} ✅' in tasks[message.chat.id][Date]):
            text = 'Похоже такая задача уже добавлена'
        else:
            add_todo(Date, task, message)
            text = f'Задача "{task}" добавлена на {Date}'
        bot.send_message(message.chat.id, text)
        print(tasks)
    else:
        bot.send_message(message.chat.id, 'Для начала нажмите /start')


def show_tasks(message):
    tasks = {message.chat.id: read_user(message.chat.id)['Item']['user_data']['tasks']}
    if message.chat.id in tasks:
        command = message.text
        text = ''
        if command == 'help':
            text = f'Пример ввода команды:\n/show или /show 01.01 или /show 01.01 14.02\nСписок доступных ' \
                   f'для ввода форматов времени можно посмотреть по команде \n/formatdates'
        elif command.lower() == 'все':
            if len(tasks[message.chat.id]) == 0:
                text = 'Задач нет!'
            else:
                sorted_dates_list = sorted_dates(tasks, message.chat.id)
                for Date in sorted_dates_list:
                    if Date >= date.today():
                        Date = Date.strftime("%d.%m.%Y")
                        text += "* " + Date.upper() + "\n"
                        for task in tasks[message.chat.id][Date]:
                            text += "- " + task + "\n"
        else:
            Date = date2date(command)
            if Date == 'Неверная дата':
                text = 'Неверно введена дата!\nСписок доступных для ввода форматов дат можно посмотреть ' \
                       'по команде /formatdates'
            elif Date in tasks[message.chat.id]:
                text = "* " + Date.upper() + "\n"
                for task in tasks[message.chat.id][Date]:
                    text += "- " + task + "\n"
            else:
                text = "Задач на эту дату нет!"
        bot.edit_message_text(f'{text}', message.chat.id, message.message_id)
    else:
        bot.send_message(message.chat.id, 'Для начала нажмите /start')


def show_all_past_tasks(message):
    tasks = {message.chat.id: read_user(message.chat.id)['Item']['user_data']['tasks']}
    if message.chat.id in tasks:
        text = ""
        if len(tasks[message.chat.id]) == 0:
            text = 'Вы ещё не добавили ни одну задачу!'
        else:
            sorted_dates_list = sorted_dates(tasks, message.chat.id)
            for Date in sorted_dates_list:
                if Date.date() < date.today():
                    Date = Date.strftime("%d.%m.%Y")
                    text += "* " + Date.upper() + "\n"
                    for task in tasks[message.chat.id][Date]:
                        text += "[] " + task + "\n"
            if text == '':
                text = 'Прошедших задач нет!'
        bot.send_message(message.chat.id, text)
    else:
        bot.send_message(message.chat.id, 'Для начала нажмите /start')


def delete_task(message):
    tasks = {message.chat.id: read_user(message.chat.id)['Item']['user_data']['tasks']}
    command = message.text.split(maxsplit=1)
    Date = date2date(command[0])
    task = command[1].capitalize()
    task_done = task + ' ✓ '
    if task in tasks[message.chat.id][Date]:
        tasks[message.chat.id][Date].remove(task)
        text = f'Задача "{task}" на дату {Date} удалена'
        if len(tasks[message.chat.id][Date]) == 0:
            del tasks[message.chat.id][Date]
        user_data = {'tasks': tasks[message.chat.id]}
        create_user(message.chat.id, user_data)
    elif task_done in tasks[message.chat.id][Date]:
        tasks[message.chat.id][Date].remove(task_done)
        text = f'Задача "{task}" на дату {Date} удалена'
        if len(tasks[message.chat.id][Date]) == 0:
            del tasks[message.chat.id][Date]
        user_data = {'tasks': tasks[message.chat.id]}
        create_user(message.chat.id, user_data)
    else:
        text = f'Отсутствует задача "{task}" на дату {Date}'
    bot.edit_message_text(f'{text}', message.chat.id, message.message_id)


def done_task(message):
    tasks = {message.chat.id: read_user(message.chat.id)['Item']['user_data']['tasks']}
    command = message.text.split(maxsplit=1)
    Date = date2date(command[0])
    task = command[1].capitalize()
    task_done = task + ' ✅'
    i = tasks[message.chat.id][Date].index(task)
    tasks[message.chat.id][Date].remove(task)
    tasks[message.chat.id][Date].insert(i, task_done)
    text = f'Задача "{task}" на дату {Date} помечена выполненной'
    user_data = {'tasks': tasks[message.chat.id]}
    create_user(message.chat.id, user_data)
    bot.edit_message_text(f'{text}', message.chat.id, message.message_id)


# Функция и обработчки для отметки задач выполнеными или удаления
def get_tasks(message):
    tasks = {message.chat.id: read_user(message.chat.id)['Item']['user_data']['tasks']}
    if message.text == 'Показать задачи':
        action_text = f'👁‍ Выберите дату'
    elif message.text == 'Удалить задачу':
        action_text = f'❌ Выберите дату:'
    elif message.text == 'Отметить выполненной':
        action_text = f'✅ Выберите дату:'
    if message.chat.id in tasks:
        sorted_dates_list = sorted_dates(tasks, message.chat.id)
        date_list = [day.strftime("%d.%m.%Y") for day in sorted_dates_list if day >= date.today()]
        markup = types.InlineKeyboardMarkup()
        if message.text == 'Показать задачи':
            button = types.InlineKeyboardButton(text='Все', callback_data='Все')
            markup.add(button)
        for item in date_list:
            button = types.InlineKeyboardButton(text=item, callback_data=item)
            markup.add(button)
    bot.send_message(message.chat.id, action_text, reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.message.text[0] in ('👁', '❌', '✅'))
    def callback_data(call):
        tasks = {message.chat.id: read_user(message.chat.id)['Item']['user_data']['tasks']}
        if call.message.text[0] == '👁':
            msg = bot.edit_message_text(f'{call.data}', call.message.chat.id,
                                        call.message.message_id)
            show_tasks(msg)
        elif call.data in tasks[call.message.chat.id]:
            tasks_list = [task for task in tasks[call.message.chat.id][call.data]]
            markup1 = types.InlineKeyboardMarkup()
            for item1 in tasks_list:
                button1 = types.InlineKeyboardButton(text=item1, callback_data=item1)
                markup1.add(button1)
            bot.edit_message_text(f'{call.message.text[0]} {call.data}', call.message.chat.id,
                                  call.message.message_id, reply_markup=markup1)
        else:
            if call.message.text[0] == '❌':
                msg = bot.edit_message_text(f'{call.message.text[2:]} {call.data}', call.message.chat.id,
                                            call.message.message_id)
                delete_task(msg)
            elif call.message.text[0] == '✅':
                msg = bot.edit_message_text(f'{call.message.text[2:]} {call.data}', call.message.chat.id,
                                            call.message.message_id)
                done_task(msg)


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("tokens.ini")
    token = config['TOKENS']['TOKEN']

    # Создание переменной для использования функциий библиотеки
    bot = TeleBot(token)


    @bot.message_handler(commands=['start'])
    def start(message):
        user_id = message.chat.id
        user_data = read_user(user_id)
        if 'Item' not in user_data:
            user_data = {'tasks': {}, 'name': message.from_user.first_name}
            create_user(user_id, user_data)
            text = f'Привет {message.from_user.first_name}!\nВсё готово, можно начинать\n{HELP}\n' \
                   f'Для показа подсказки ввода команд введите /команда help или /example'
        else:
            text = 'Похоже вы уже используете TODO'
        markup = get_menu()
        bot.send_message(message.chat.id, text, reply_markup=markup)


    @bot.message_handler(content_types=['text'])
    def get_text(message):
        tasks = {message.chat.id: read_user(message.chat.id)['Item']['user_data']['tasks']}
        if message.chat.id in tasks:
            msg = message.text
            if msg == 'Меню':
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                button_add = types.KeyboardButton('Добавить задачу')
                button_rand = types.KeyboardButton('Случайная задача')
                button_done = types.KeyboardButton('Отметить выполненной')
                button_del = types.KeyboardButton('Удалить задачу')
                button_show = types.KeyboardButton('Показать задачи')
                button_help = types.KeyboardButton('Подсказка')
                button_back = types.KeyboardButton('Назад')
                markup.add(button_add, button_rand)
                markup.add(button_done, button_del)
                markup.add(button_show, button_help)
                markup.add(button_back)
                bot.send_message(message.chat.id, 'Выберите команду', reply_markup=markup)
            elif msg == 'Добавить задачу':
                msg = bot.send_message(message.chat.id, 'Введите задачу')
                bot.register_next_step_handler(msg, start_cal)
            elif msg == 'Случайная задача':
                random_task_add(message)
            elif msg == 'Отметить выполненной':
                get_tasks(message)
            elif msg == 'Удалить задачу':
                get_tasks(message)
            elif msg == 'Показать задачи':
                get_tasks(message)
            elif msg == 'Подсказка':
                get_help(message)
            elif message.text == 'Назад':
                markup = get_menu()
                bot.send_message(message.chat.id, 'Для выбора команды нажмите "меню"', reply_markup=markup)
            else:
                text = 'Я вас не понимаю(\nВведите /help для отображения списка доступных команд.'
                bot.send_message(message.chat.id, text)
        else:
            bot.send_message(message.chat.id, 'Для начала введите /start')


    bot.polling(none_stop=True)
