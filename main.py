from telebot import TeleBot, types
import random
from datetime import date, datetime
import schedule
import time
import threading
import json
from token_list import Token # нужно создать файл с токеном
from data_check import date2date, sorted_dates
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

token = Token

# Создание переменной для использования функциий библиотеки
bot = TeleBot(token)

HELP = """
ВАЖНО! Для использования команд из списка меню необходимо зажать нужную команду!
Список доступных команд:
  /help — Вывести список доступных команд.
  /add — Добавить задачу в список.
  /rem — Добавление напоминания.
  /del — Удалить задачу.
  /done — Отметить задачу выполненной.
  /show — Напечатать все добавленные задачи на выбранную дату (можно ввести несколько дат через пробел).
  /past — Вывести список прошедших здач.
  /random — Добавить случайную задачу на сегодня.
  /example — Вывести примеры ввода команд.
  /formatdates — Вывести список форматов дат доступных для ввода.

Для показа подсказки ввода команды введите:
  /команда help
"""

example = """
Пример ввода команд:
Для команд /add, /del, /done:
    /команда дата задача
Пример: 
    /add 01.01 Новый год 
Примечание: 
    для команды /del можно ввести только дату для удаления всех задач на выбранную дату
Пример:
    /del 01.01
Для команды /show:
    /команда дата
Пример:
    /show 01.01
Примечание:
    можно ввести несколько дат для отображения задач на выбранные даты
    или ничего не вводить для отображения всех задач на все записанные даты
Пример:
    /show 01.01 23.02

Для команд /help, /formatdates, 
/past, /random ничего дополнительно вводить не нужно.

Для команды /rem:
    /команда время
Пример:
    /rem 10:00

Список доступных для ввода ворматов дат и времени можно посмотреть по команде 
/formatdates
"""

dates_format = """
Дата:
- dd.mm / dd,mm / dd/mm / dd-mm,
- dd.mm.yyyy / dd,mm,yyyy / dd/mm/yyyy / dd-mm-yyyy,
- Сегодня/Завтра/Послезавтра/Today/Tomorrow,
- Дни недели.

Время:
- чч:мм / чч-мм / чч.мм / чч,мм
"""

tasks_file_name = 'tasks_file.json'
users = {}
tasks = {}
reminders = {}
random_tasks = ['Поучить английский', 'Позаниматься спортом', 'Почитать книгу', 'Решить судоку', 'Порисовать',
                'Посмотреть новый фильм', 'Погулять', 'Поспать', 'Приготовить необычное блюдо']


# Функция импорта датасета пользователей из файла
def load_tasks():
    try:
        with open(tasks_file_name, "r") as tasks_file:
            data_tasks, data_reminders, data_users = json.load(tasks_file)
            return data_tasks, data_reminders, data_users
    except:
        return {}, {}, {}


# Функция сохранения датасета пользователей в файл
def save_tasks():
    tasks_file = open(tasks_file_name, 'w')
    data = [tasks, reminders, users]
    json.dump(data, tasks_file)
    pass


# Функция добавления задачи в словарь
def add_todo(Date, task, message):
    if Date in tasks[message.chat.id]:
        tasks[message.chat.id][Date].append(task)
        save_tasks()
    else:
        tasks[message.chat.id][Date] = []
        tasks[message.chat.id][Date].append(task)
        save_tasks()


# Импорт датасета пользователей из файла и преобразование ключей из str в int
dataset_tasks, dataset_reminders, dataset_users = load_tasks()
for key, value in dataset_tasks.items():
    tasks[int(key)] = value
for key, value in dataset_reminders.items():
    reminders[int(key)] = value
for key, value in dataset_users.items():
    users[int(key)] = value


def get_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttom_menu = types.KeyboardButton('Меню')
    markup.add(buttom_menu)
    return markup


@bot.message_handler(commands=['start_cal'])
def start_cal(m):
    msg_task = m.text
    print(msg_task)
    calendar, step = DetailedTelegramCalendar().build()
    bot.send_message(m.chat.id,
                     f"{m.text}",
                     reply_markup=calendar)


    @bot.callback_query_handler(func=DetailedTelegramCalendar.func())
    def cal(c):
        result, key, step = DetailedTelegramCalendar().process(c.data)
        if not result and key:
            bot.edit_message_text(f"{c.message.text}",
                                  c.message.chat.id,
                                  c.message.message_id,
                                  reply_markup=key)
        elif result:
            d = str(result).split('-')
            date = '.'.join(d[::-1])
            msg = bot.edit_message_text(f"{date} {c.message.text}",
                                  c.message.chat.id,
                                  c.message.message_id)
            add_task(msg)



@bot.message_handler(commands=['start'])
def start(message):
    markup = get_menu()
    user_id = message.chat.id
    if user_id in tasks:
        text = 'Похоже вы уже используете TODO'
    else:
        tasks[user_id] = {}
        reminders[user_id] = {}
        users[user_id] = message.from_user.first_name
        save_tasks()
        text = f'Привет {message.from_user.first_name}!\nВсё готово, можно начинать\n{HELP}\n' \
               f'Для показа подсказки ввода команд введите /команда help или /example'
    bot.send_message(message.chat.id, text, reply_markup=markup)


# Регистрирует функцию ниже в качестве обработчика
@bot.message_handler(commands=['help'])
# Функция принимающая сообщения
def help(message):
    bot.send_message(message.chat.id, f'{HELP}')


@bot.message_handler(commands=['example'])
def command_example(message):
    bot.send_message(message.chat.id, f'{example}')


@bot.message_handler(commands=['formatdates'])
def command_formatdates(message):
    bot.send_message(message.chat.id, f'Список форматов дат и времени доступных для ввода:\n{dates_format}')


@bot.message_handler(commands=['rem'])
def command_reminder(message):
    try:
        command = message.text
        if command == 'help':
            text = f'Пример ввода команды:\n/rem 10:00\nСписок доступных для ввода форматов времени ' \
                   f'можно посмотреть по команде \n/formatdates'
            bot.send_message(message.chat.id, text)
        else:
            try:
                usertime_loc = command.replace('.', ':').replace('-', ':').replace(',', ':')
                usertime = usertime_loc.split(':')
                usertime[0] = str(int(usertime[0]) + 3)
                usertime = ':'.join(usertime)
                try:
                    if (int(usertime.split(':')[0]) not in tuple(range(0, 24))) or (
                            int(usertime.split(':')[1]) not in tuple(range(0, 60))):
                        bot.send_message(message.chat.id,
                                         f'Время введено неправильно.\nСписок доступных для ввода форматов '
                                         f'времени можно посмотреть по команде /formatdates')
                    else:
                        reminders[message.chat.id] = usertime
                        save_tasks()
                        bot.send_message(message.chat.id,
                                         f'Создано напоминание о задачах на {usertime_loc}')
                except:
                    bot.send_message(message.chat.id,
                                     f'Время введено неправильно.\nСписок доступных для ввода форматов '
                                     f'времени можно посмотреть по команде /formatdates')
            except:
                bot.send_message(message.chat.id, f'Введите команду в формате\n/rem время\n\nИли введите '
                                                  f'/example для отображения примеров ввода команд')
    except:
        text = 'Введите команду в формате\n/rem время\n\nИли введите /example для отображения примеров ввода команд'
        bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['add'])
def add_task(message):
    if message.chat.id in tasks:
        command = message.text.split(maxsplit=1)
        d = command[0].split('-')
        d = '.'.join(d[::-1])
        if command:
            Date = date2date(d)
            task = command[1].capitalize()
            if len(task) < 3:
                text = 'Задача слишком короткая!'
            elif Date == 'Неверная дата':
                text = 'Неверно введена дата!\nСписок доступных для ввода форматов дат можно ' \
                       'посмотреть по команде /formatdates'
            else:
                add_todo(Date, task, message)
                text = f'Задача "{task}" добавлена на {Date}'
            bot.send_message(message.chat.id, text)
            print(tasks)
    else:
        bot.send_message(message.chat.id, 'Для начала нажмите /start')


@bot.message_handler(commands=['random'])
def random_task_add(message):
    if message.chat.id in tasks:
        Date = date2date('сегодня')
        task = random.choice(random_tasks).capitalize()
        if Date in tasks[message.chat.id] and task in tasks[message.chat.id][Date]:
            text = 'Похоже такая задача уже добавлена'
        else:
            add_todo(Date, task, message)
            text = f'Задача "{task}" добавлена на {Date}'
        bot.send_message(message.chat.id, text)
        print(tasks)
    else:
        bot.send_message(message.chat.id, 'Для начала нажмите /start')


@bot.message_handler(commands=['show'])
def show_tasks(message):
    if message.chat.id in tasks:
        command = message.text.split()
        text = ""
        if len(command) == 1:
            if command[0] == 'help':
                text = f'Пример ввода команды:\n/show или /show 01.01 или /show 01.01 14.02\nСписок доступных ' \
                       f'для ввода форматов времени можно посмотреть по команде \n/formatdates'
            elif command[0].lower() == 'все':
                if len(tasks[message.chat.id]) == 0:
                    text = 'Задач нет!'
                else:
                    sorted_dates_list = sorted_dates(tasks, message.chat.id)
                    for Date in sorted_dates_list:
                        if Date.date() >= date.today():
                            Date = Date.strftime("%d.%m.%Y")
                            text += "* " + Date.upper() + "\n"
                            for task in tasks[message.chat.id][Date]:
                                text += "[] " + task + "\n"
            else:
                Date = date2date(command[0])
                if Date == 'Неверная дата':
                    text = 'Неверно введена дата!\nСписок доступных для ввода форматов дат можно посмотреть ' \
                           'по команде /formatdates'
                elif Date in tasks[message.chat.id]:
                    text = "* " + Date.upper() + "\n"
                    for task in tasks[message.chat.id][Date]:
                        text += "[] " + task + "\n"
                else:
                    text = "Задач на эту дату нет!"
        elif len(command) > 1:
            Dates = command
            for i in range(len(Dates)):
                Dates[i] = date2date(Dates[i])
            if 'Неверная дата' in Dates:
                text = "Какая-то из дат неверная!"
            else:
                sorted_dates_list = sorted_dates(Dates, message.chat.id)
                for Date in sorted_dates_list:
                    Date = Date.strftime("%d.%m.%Y")
                    Date = date2date(Date)
                    if Date in tasks[message.chat.id]:
                        text += "* " + Date.upper() + "\n"
                        for task in tasks[message.chat.id][Date]:
                            text += "[] " + task + "\n"
                    else:
                        text = "Какая-то из дат неверная!"
        else:
            text = "Задач на эту дату нет!"
        bot.send_message(message.chat.id, text)
    else:
        bot.send_message(message.chat.id, 'Для начала нажмите /start')


@bot.message_handler(commands=['past'])
def show_all_past_tasks(message):
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


@bot.message_handler(commands=['del', 'delete'])
def delete_task(message):
    if message.chat.id in tasks:
        command = message.text.split(maxsplit=1)
        if len(command) < 1:
            text = 'Введите команду в формате:\n/del дата задача\nдля удаления выбранной задачи\n\n' \
                   'Или в формате:\n/del дата\nдля удаления всех задач на выбранную дату\n\n' \
                   'Или введите /example для отображения примеров ввода команд'
        elif len(command) == 1:
            if message.text.split()[0] == 'help':
                text = f'Пример ввода команды:\n/del 01.01 Новый год! или /del 01.01\n' \
                       f'Список доступных для ввода форматов времени можно посмотреть по команде \n/formatdates'
            else:
                Date = date2date(command[0])
                if Date == 'Неверная дата':
                    text = 'Неверная дата\nСписок доступных для ввода форматов времени ' \
                           'можно посмотреть по команде \n/formatdates'
                else:
                    if Date in tasks[message.chat.id]:
                        del tasks[message.chat.id][Date]
                        text = f'Все задачи на дату {Date} удалены'
                        save_tasks()
                    else:
                        text = f'Даты {Date} пока нет в вашем списке'
        else:
            Date = date2date(command[0])
            if Date == 'Неверная дата':
                text = 'Неверная дата\nСписок доступных для ввода форматов времени ' \
                       'можно посмотреть по команде \n/formatdates'
            elif Date in tasks[message.chat.id]:
                task = command[1].capitalize()
                task_done = task + ' ✓ '
                if task in tasks[message.chat.id][Date]:
                    tasks[message.chat.id][Date].remove(task)
                    text = f'Задача "{task}" на дату {Date} удалена'
                    if len(tasks[message.chat.id][Date]) == 0:
                        del tasks[message.chat.id][Date]
                    save_tasks()
                elif task_done in tasks[message.chat.id][Date]:
                    tasks[message.chat.id][Date].remove(task_done)
                    text = f'Задача "{task}" на дату {Date} удалена'
                    if len(tasks[message.chat.id][Date]) == 0:
                        del tasks[message.chat.id][Date]
                    save_tasks()
                else:
                    text = f'Отсутствует задача "{task}" на дату {Date}'
            else:
                text = f'Даты {Date} пока нет в вашем списке'
        bot.send_message(message.chat.id, text)
    else:
        bot.send_message(message.chat.id, 'Для начала нажмите /start')


@bot.message_handler(commands=['done'])
def done_task(message):
    if message.chat.id in tasks:
        command = message.text.split(maxsplit=1)
        if len(command) < 2:
            try:
                if message.text.split()[0] == 'help':
                    text = f'Пример ввода команды:\n/done 01.01 Новый год!\nСписок доступных для ввода форматов' \
                           f' дат можно посмотреть по команде \n/formatdates'
                else:
                    text = f'Введите команду в формате:\n/done дата задача\nчтобы добавить задачу в список.' \
                           f'\n\nИли введите /example для отображения примеров ввода команд'
            except:
                text = f'Введите команду в формате:\n/done дата задача\nчтобы добавить задачу в список.' \
                       f'\n\nИли введите /example для отображения примеров ввода команд'
        else:
            Date = date2date(command[0])
            if Date == 'Неверная дата':
                text = 'Неверная дата\nСписок доступных для ввода форматов времени можно ' \
                       'посмотреть по команде \n/formatdates'
            else:
                if Date in tasks[message.chat.id]:
                    task = command[1].capitalize()
                    task_done = task + ' ✓ '
                    if task in tasks[message.chat.id][Date]:
                        i = tasks[message.chat.id][Date].index(task)
                        tasks[message.chat.id][Date].remove(task)
                        tasks[message.chat.id][Date].insert(i, task_done)
                        text = f'Задача "{task}" на дату {Date} помечена выполненной'
                        save_tasks()
                    elif task_done in tasks[message.chat.id][Date]:
                        text = f'Задача "{task}" на дату {Date} уже была помечена выполненной'
                    else:
                        text = f'Отсутствует задача {task} на дату {Date}'
                else:
                    text = f'Даты {Date} пока нет в вашем списке'
        bot.send_message(message.chat.id, text)
    else:
        bot.send_message(message.chat.id, 'Для начала нажмите /start')


@bot.message_handler(content_types=['text'])
def get_text(message):
    if message.chat.id in tasks:
        msg = message.text
        if msg == 'Меню':
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            buttom_add = types.KeyboardButton('Добавить задачу')
            buttom_rand = types.KeyboardButton('Случайная задача')
            buttom_done = types.KeyboardButton('Отметить выполненной')
            buttom_del = types.KeyboardButton('Удалить задачу')
            buttom_show = types.KeyboardButton('Показать задачи')
            buttom_help = types.KeyboardButton('Подсказка')
            buttom_back = types.KeyboardButton('Назад')
            buttom_rem = types.KeyboardButton('Напоминание')
            markup.add(buttom_add, buttom_rand)
            markup.add(buttom_done, buttom_del)
            markup.add(buttom_show, buttom_rem)
            markup.add(buttom_help, buttom_back)
            bot.send_message(message.chat.id, 'Выберите команду', reply_markup=markup)
        elif msg == 'Добавить задачу':
            msg = bot.send_message(message.chat.id, 'Введите задачу')
            bot.register_next_step_handler(msg, start_cal)
        elif msg == 'Случайная задача':
            random_task_add(message)
        elif msg == 'Отметить выполненной':
            msg = bot.send_message(message.chat.id, 'Введите дату и задачу')
            bot.register_next_step_handler(msg, done_task)
        elif msg == 'Удалить задачу':
            msg = bot.send_message(message.chat.id, 'Введите дату для удаления всех задач на эту дату\nИли введите дату и задачу для удаления одной задачи ')
            bot.register_next_step_handler(msg, delete_task)
        elif msg == 'Показать задачи':
            msg = bot.send_message(message.chat.id, 'Введите дату\nВведите "Все" для отображения всех задач')
            bot.register_next_step_handler(msg, show_tasks)
        elif msg == 'Напоминание':
            msg = bot.send_message(message.chat.id, 'Введите время')
            bot.register_next_step_handler(msg, command_reminder)
        elif msg == 'Подсказка':
            command_formatdates(message)
        elif message.text == 'Назад':
            markup = get_menu()
            bot.send_message(message.chat.id, 'Для выбора команды нажмите "меню"', reply_markup=markup)
        else:
            text = 'Я вас не понимаю(\nВведите /help для отображения списка доступных команд.'
            bot.send_message(message.chat.id, text)
    else:
        bot.send_message(message.chat.id, 'Для начала введите /start')


def cronTask():
    now = datetime.now().strftime("%H:%M")
    if len(reminders) > 0:
        for userid, usertime in reminders.items():
            if now == usertime:
                t = 'сегодня'
                Date = date2date(t)
                if userid in tasks:
                    if Date in tasks[userid]:
                        text = Date.upper() + "\n"
                        for task in tasks[userid][Date]:
                            text += "[] " + task + "\n"
                        bot.send_message(userid, f'Привет {users[userid]}!\nВот задачи на сегодня:\n{text}')

def runBot():
    # Функция для постоянного обращения к телеграм
    bot.polling(none_stop=True)

def runScheluders():
    schedule.every(1).minute.do(cronTask)

    # Start cron task after some time interval
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    t1 = threading.Thread(target=runBot)
    t2 = threading.Thread(target=runScheluders)
    t1.start()
    t2.start()