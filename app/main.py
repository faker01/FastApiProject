from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette import status
from utils import Database, db_to_string, taking_period_calculation, check_period

app = FastAPI()  # uvicorn app.main:app
db = Database()


class Schedule_response(BaseModel):
    schedule_id: int


class Schedule_request(BaseModel):
    user_id: int
    pill: str
    duration: int
    period: int


@app.post('/schedule', response_model=Schedule_response)
async def post_schedule(schedule: Schedule_request):
    new_schedule = [schedule.user_id, schedule.pill, schedule.duration, schedule.period]
    pill_schedule = ' '.join(taking_period_calculation(new_schedule[2:]))
    if new_schedule[2] > 0:
        if new_schedule[2] < 4:
            new_schedule[2] = 0
        else:
            new_schedule[2] -= 4

    new_schedule = [new_schedule[0], new_schedule[1], pill_schedule, new_schedule[2], new_schedule[3]]
    req = list(db.add_schedule(new_schedule))

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


@app.get('/schedules')
async def get_schedules_by_user_id(user_id):
    schedules = list(db.get_user_schedules_id(user_id))
    if len(schedules):
        return schedules
    else:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Не удалось найти пользователя в базе данных"}
        )


@app.get('/schedule')
async def get_schedule_by_schedule_id(user_id, schedule_id):
    schedule = list(db.get_user_schedule(user_id, schedule_id))

    if len(schedule):
            return schedule
    else:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Не удалось найти расписание в базе данных"}
        )


@app.get('/next_takings')
async def get_next_taking(user_id):
    print(list(db.get_user_schedules_id(user_id)))
    schedules_ids = map(lambda x: x[0], list(db.get_user_schedules_id(user_id)))
    pills_in_period = []

    for i in schedules_ids:
        pill = list(db.get_user_schedule(user_id, i)[0])
        print(pill)
        next_pill_time = check_period(pill[1])
        if next_pill_time:
            pills_in_period.append([pill[0], next_pill_time])
    return pills_in_period
