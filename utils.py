import sqlite3
import time
from os import remove as os_remove
from data.settings import period


months = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def check_period(schedule):
    now_date, now_time = time.strftime("%d.%m.%Y::%H.%M", time.localtime(time.time())).split("::")
    schedule = schedule.split(" ")
    for i in schedule:
        print(i)
        schedule_date, schedule_time = i.split("::")
        if schedule_date == now_date and now_time < schedule_time < time_sum(schedule_time, period):
            return schedule_time
    return False

def db_to_string(req):
    return f"""for user: {req[0]} {req[1]} {req[2]} {req[3]}"""


def date_sum(date: str, date_period: int):
    day, month, year = map(int, date.split("."))
    day += date_period
    while months[month] < day:
        day -= months[month]
        month += 1
    return f"{day}.{month}.{year}"


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
        return f"0{hour}.{minute}"
    return f"{hour}.{minute}"


def taking_period_calculation(req):
    schedule = []
    now_date, now_time = time.strftime("%d.%m.%Y::%H.%M", time.localtime(time.time())).split("::")
    if len(now_time) < 5:
        now_time = "0" + now_time
    taking_duration, taking_period = req

    time_check = list(map(int, now_time.split(".")))[1]
    while time_check % 15 != 0:
        time_check += 1
    now_time = now_time[:3] + str(time_check)

    if 0 < taking_duration < 4:
        end_date = date_sum(now_date, taking_duration)
    elif taking_duration == 0:
        return schedule
    else:
        end_date = date_sum(now_date, 4)

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
        return self.cur.fetchone()

    # function to add schedule for user / функция добавления расписания для пользователя
    def add_schedule(self, schedule: list):
        self.cur.execute(f'''INSERT INTO Schedule(user_id, pill, schedule, duration, period) 
                        VALUES ({schedule[0]}, "{schedule[1]}", "{schedule[2]}", {schedule[3]}, {schedule[4]})''')
        self.con.commit()
        return self.cur.fetchone()


"""db = Database()
print(db.add_user('lion'))
print(db.add_user('wolf'))
print(db.add_schedule([1, "ttttt", ' '.join(taking_period_calculation([10, 3])), 10, 3]))
print(db.add_schedule([1, "yyyyy", ' '.join(taking_period_calculation([-1, 12])), -1, 12]))
print(db.add_schedule([1, "uuuuu", ' '.join(taking_period_calculation([16, 24])), 16, 24]))
print(db.add_schedule([2, "tttgg", ' '.join(taking_period_calculation([10, 3])), 10, 3]))
print(db.add_schedule([2, "yyyhh", ' '.join(taking_period_calculation([-1, 2])), -1, 2]))"""