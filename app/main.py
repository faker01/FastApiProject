from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette import status
from utils import Database, taking_period_calculation, check_period, next_pill

# start of application and database/ запуск приложения и БД
app = FastAPI()  # uvicorn app.main:app
db = Database()


# POST request response model/ модель ответа на POST запрос
class Schedule_response(BaseModel):
    schedule_id: int


# POST request model/ модель POST запроса
class Schedule_request(BaseModel):
    user_id: int
    pill: str
    duration: int
    period: int


# POST function to create a schedule/ функция POST для создания расписания
@app.post('/schedule', response_model=Schedule_response)
async def post_schedule(schedule: Schedule_request):
    # data acquisition/ получение данных
    new_schedule = [schedule.user_id, schedule.pill, schedule.duration, schedule.period]
    # creating and formatting a schedule/ создание и форматирование расписания
    pill_schedule = ' '.join(taking_period_calculation(new_schedule[2:]))
    # update remaining appointment time/ обновление оставшегося время приёма
    if new_schedule[2] > 0:
        if new_schedule[2] < 4:
            new_schedule[2] = 0
        else:
            new_schedule[2] -= 4
    # creating a query in the DB/ создание запроса в БД
    new_schedule = [new_schedule[0], new_schedule[1], pill_schedule, new_schedule[2], new_schedule[3]]
    req = list(db.add_schedule(new_schedule))
    # query result/ результат запроса
    if req:
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"message": f"Успешно добавлен, Schedule_id={req[0]}"}
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Не удалось добавить в базу данных"}
        )


# function to get list of pills and their id/ функция получения списка таблеток и их id
@app.get('/schedules')
async def get_schedules_by_user_id(user_id):
    # DB query/ запрос в БД
    schedules = list(db.get_user_schedules_id(user_id))
    # if there is an answer, then it displays, otherwise error 404/ если ответ есть, то выдаёт, иначе ошибка 404
    if len(schedules):
        return schedules
    else:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Не удалось найти пользователя в базе данных"}
        )


# function to get a specific schedule by schedule_id and user_id/
# функция получения определённого расписания по schedule_id и user_id
@app.get('/schedule')
async def get_schedule_by_schedule_id(user_id, schedule_id):
    # DB query/ запрос в БД
    schedule = db.get_user_schedule(user_id, schedule_id)
    # if there is an answer, then it displays, otherwise error 404/ если ответ есть, то выдаёт, иначе ошибка 404
    if len(schedule):
        return schedule
    else:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Не удалось найти расписание в базе данных"}
        )


# function to get pills soon/ функция получения таблеток в ближайшее время
@app.get('/next_takings')
async def get_next_taking(user_id):
    # getting id for user schedules/ получения id для расписаний пользователя
    schedules_ids = map(lambda x: x[0], list(db.get_user_schedules_id(user_id)))
    pills_in_period = []
    # cycle through all schedules/ цикл по всем расписаниям
    for i in schedules_ids:
        # we get the value from the DB and process it/ получаем значение из БД и обрабатываем
        db_req = db.get_user_schedule(user_id, i)
        pill = db_req[0]

        # we get the closest one in a given period/ получаем ближайшую в заданный период
        next_pill_time = check_period(pill[1])

        # if it exists, then we add it to the list, otherwise we look for the closest one that
        # is not related to the period/
        # если она существует, то добавляем в список, иначе ищем ближайшую не относящуюся к периоду
        if next_pill_time:
            pills_in_period.append([pill[0], next_pill_time])
        else:
            next_pill_time = next_pill(pill[1])
        # updating schedule for the next 4 days/ обновляем расписание для следующих 4 дней
        new_schedule = taking_period_calculation([pill[2], pill[3]], next_pill_time)
        delta = int(new_schedule[0].split("::")[1][:2]) - int(pill[1].split(" ")[0].split("::")[1][:2])
        # update remaining appointment time/ обновление оставшегося время приёма
        duration = pill[2]
        if duration > 0:
            duration -= delta
        # update row in DB/ обновление строки в БД
        db.update_schedule(i, " ".join(new_schedule), duration)
    if len(pills_in_period):
        return pills_in_period
    else:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Не удалось найти ближайшие приёмы в заданный период"}
        )
