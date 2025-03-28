import sqlite3
import time
from os import remove as os_remove
from data.settings import period

# list with number of days in months for correct calculation/
# список с количеством дней в месяцах для правильного рассчёта
months = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


# function of finding the nearest pill in a given period/ функция нахождения ближайшей таблетки в заданный период
def check_period(schedule):
    # get current date and current time/ получение текущей даты и текущего времени
    now_date, now_time = time.strftime("%d.%m.%Y::%H.%M", time.localtime(time.time())).split("::")
    schedule = schedule.split(" ")
    # we go through the list with dates and times of reception and search by the specified parameters/
    # проходим по списку с датами и временами приёма и ищем по заданным параметрам
    for i in schedule:
        schedule_date, schedule_time = i.split("::")
        if schedule_date == now_date and now_time < schedule_time:
            if schedule_time < time_sum(now_time, period):
                return f"{schedule_date}::{schedule_time}"
            return False
    return False


# function of getting the next pill if the previous function did not work/
# функция получения следующей таблетки, если не сработала предыдущая функция
def next_pill(schedule):
    now_date, now_time = time.strftime("%d.%m.%Y::%H.%M", time.localtime(time.time())).split("::")
    schedule = schedule.split(" ")
    for i in schedule:
        schedule_date, schedule_time = i.split("::")
        if (schedule_date == now_date and now_time < schedule_time) or schedule_date > now_date:
            return f"{schedule_date}::{schedule_time}"
    return False


# function to sum date and number of days/ функция суммирования даты и количества дней
def date_sum(date: str, date_period: int):
    day, month, year = map(int, date.split("."))
    day += date_period
    while months[month] < day:
        day -= months[month]
        month += 1
        if month > 12:
            month -= 12
            year += 1
    return f"{day}.{month}.{year}"


# time and hours summation function/ функция суммирования времени и часов
def time_sum(n_time: str, time_period: int):
    hour, minute = map(int, n_time.split("."))
    minute += time_period * 60
    if time_period >= 0:
        while minute > 60:
            minute -= 60
            hour += 1
    else:
        while minute < 0:
            minute += 60
            hour -= 1
    if hour < 10:
        return f"0{hour}.{minute}".ljust(5, "0")
    return f"{hour}.{minute}".ljust(5, "0")


# function to calculate schedule for the next 4 days/ функция рассчёта расписания для следующих 4 дней
def taking_period_calculation(req: list, now_dt: str = ""):
    # we get the initial time, duration and period/ получаем начальное время, длительность и периодичность
    schedule = []
    if len(now_dt) > 0:
        now_date, now_time = now_dt.split("::")
    else:
        now_date, now_time = time.strftime("%d.%m.%Y::%H.%M", time.localtime(time.time())).split("::")
    if len(now_time) < 5:
        now_time = "0" + now_time
    taking_duration, taking_period = req

    # we check that the time is a multiple of 15/ проверяем, чтобы время было кратно 15
    time_check = list(map(int, now_time.split(".")))[1]
    while time_check % 15 != 0:
        time_check += 1
    now_time = time_sum(now_time[:3] + str(time_check), 0)

    # get settlement end date/ получаем дату окончания рассчётов
    if 0 < taking_duration < 4:
        end_date = date_sum(now_date, taking_duration)
    elif taking_duration == 0:
        return schedule
    else:
        end_date = date_sum(now_date, 4)

    # we calculate each reception in a given period, checking that it falls during daytime/
    # рассчитываем каждый приём в заданном периоде, проверяя, что он попадает в дневное время
    while now_date < end_date:
        now_time = time_sum(now_time, taking_period)
        if int(now_time[:2]) > 24:
            now_date = date_sum(now_date, 1)
            now_time = time_sum(now_time, -24)

        if "07" < now_time[:2] < "22":
            schedule.append(f"{now_date}::{now_time}")
        elif "07" < now_time[:2]:
            schedule.append(f"{now_date}::08.00")
        else:
            schedule.append(f"{date_sum(now_date, 1)}::08.00")

    return schedule


class Database:
    # initializing class for work with db/ инициализация класса для работы с бд
    def __init__(self):
        # сreate a database. If it exists, then connect/ создаём базу данных. Если существует, то подключаемся
        self.con = sqlite3.connect("data/db.db")
        # creating of cursor/ создаём курсор для работы с базой данных
        self.cur = self.con.cursor()
        # create the users table if it does not exist/ создаём таблицу пользователей, если она не создана
        self.cur.execute('''CREATE TABLE IF NOT EXISTS Users (id INTEGER PRIMARY KEY, username TEXT NOT NULL)''')
        # create a table with pills linked to the users who take them/ создаём таблицу с таблетками,
        # привязывязанную к пользователям, которые их принимают
        self.cur.execute('''CREATE TABLE IF NOT EXISTS Schedule (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, 
                    pill TEXT NOT NULL, schedule TEXT NOT NULL, duration INTEGER NOT NULL, period INTEGER NOT NULL)''')

    # deleting db/ удаление бд
    def db_delete(self):
        self.con.commit()
        self.con.close()
        os_remove("data/db.db")

    # db shutdown/ прекращение работы с бд
    def db_shutdown(self):
        self.con.commit()
        self.con.close()

    # function to take user_id by name/ функция для получения user_id по имени
    def get_user_id(self, name: str):
        self.cur.execute(f'''SELECT id FROM Users WHERE username = {name}''')
        return self.cur.fetchall()

    # function to get list of pills and their id by user_id/ функция для получения списка таблеток и их id по user_id
    def get_user_schedules_id(self, user_id: int):
        self.cur.execute(f'''SELECT id, pill FROM Schedule WHERE user_id = {user_id}''')
        return self.cur.fetchall()

    # function to get duration and periodicity of pill by id/
    # функция для получения продолжительности и периодичности таблетки по id
    def get_user_schedule(self, user_id: int, schedule_id: int):
        self.cur.execute(f'''SELECT pill, schedule, duration, period FROM Schedule 
                            WHERE id = {schedule_id} AND user_id = {user_id}''')
        return self.cur.fetchall()

    # function to add new user/ функция добавления нового пользователя
    def add_user(self, name: str):
        self.cur.execute(f'''INSERT INTO Users(username) VALUES ("{name}")''')
        self.con.commit()
        return self.cur.fetchall()

    # function to add schedule for user / функция добавления расписания для пользователя
    def add_schedule(self, schedule: list):
        self.cur.execute(f'''INSERT INTO Schedule(user_id, pill, schedule, duration, period) 
                        VALUES ({schedule[0]}, "{schedule[1]}", "{schedule[2]}", {schedule[3]}, {schedule[4]})''')
        self.con.commit()
        self.cur.execute(f'''SELECT id FROM Schedule WHERE user_id = {schedule[0]}''')
        return self.cur.fetchall()[-1]

    def update_schedule(self, schedule_id: int, schedule: str, duration: int):
        self.cur.execute(f'''UPDATE Schedule SET schedule="{schedule}", duration={duration} WHERE id={schedule_id}''')
        self.con.commit()
        return self.cur.fetchall()


"""db = Database()
print(db.add_user('lion'))
print(db.add_user('wolf'))
print(db.add_schedule([1, "ttttt", ' '.join(taking_period_calculation([10, 3])), 10, 3]))
print(db.add_schedule([1, "yyyyy", ' '.join(taking_period_calculation([-1, 12])), -1, 12]))
print(db.add_schedule([1, "uuuuu", ' '.join(taking_period_calculation([16, 24])), 16, 24]))
print(db.add_schedule([2, "tttgg", ' '.join(taking_period_calculation([10, 3])), 10, 3]))
print(db.add_schedule([2, "yyyhh", ' '.join(taking_period_calculation([-1, 2])), -1, 2]))"""
