from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta


# Функция проверка даты на корректность и приведение к общему виду ДД.ММ.ГГГГ
def date2date(d):
    error = "Неверная дата"
    week = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']
    week_en = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    d = str(d)
    d = d.lower()
    if d == 'сегодня' or d == 'today':
        d = date.today()
    elif d == 'завтра' or d == 'tomorrow':
        d = date.today() + timedelta(days=1)
    elif d == 'послезавтра':
        d = date.today() + timedelta(days=2)
    elif d in week or d in week_en:
        d_of_w = date.today().weekday()
        d_of_week = week.index(d)
        if d_of_week > d_of_w:
            d = date.today() + timedelta(days=(d_of_week - d_of_w))
        else:
            d = date.today() + timedelta(days=(7 + d_of_week - d_of_w))
    else:  # дата представлена цифрами
        d = d.replace('-', '.')  # можно писать 20-04-2025
        d = d.replace('/', '.')  # можно писать 20/04/2025
        d = d.replace(',', '.')  # можно писать 20,04,2025
        dd = d.split(".")
        if len(dd) == 3:  # если в дате 3 компонента
            if len(dd[2]) == 2:  # если в году две цифры
                dd[2] = '20' + dd[2]
                d = '.'.join(dd)
            try:
                d = datetime.strptime(d, '%d.%m.%Y')  # в году 4 цифры
            except:  # print("except - в дате 3 компонента")
                return error
        elif len(dd) == 2:  # если в дате 2 компонента
            # print('в дате 2 компонента')
            d = d + '.' + str(date.today().year)  # добавим текущий год
            try:
                d = datetime.strptime(d, '%d.%m.%Y')
                # d = d.date() # преобразовать d в тип date, для возможности сравнения
                if d.date() < date.today():  # если введенная дата раньше сегодня, то прибавим 1 год
                    d = d + relativedelta(years=1)
            except:
                return error
        else:
            return error
    d = d.strftime("%d.%m.%Y")
    return d


# Функция сортировки дат
def sorted_dates(dictionary, id):
    try:
        date_list = [datetime.strptime(date2date(d), '%d.%m.%Y').date() for d in dictionary[id].keys()]
        date_list.sort()
        return date_list
    except:
        date_list = [datetime.strptime(date2date(d), '%d.%m.%Y').date() for d in dictionary]
        date_list.sort()
        return date_list
