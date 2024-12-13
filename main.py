import enum
from datetime import datetime
from typing import Annotated

from aenum import extend_enum
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastui import FastUI, AnyComponent, prebuilt_html, components as c
from fastui.components.display import DisplayLookup, DisplayMode
from fastui.events import PageEvent, GoToEvent, BackEvent
from fastui.forms import fastui_form
from pydantic import BaseModel, Field

import data_base as db
from parser_processer import parsers, setup_parser, cancel_task
from task import Task

fast_api_app = FastAPI()
tasks = []


def get_task(task_id: str) -> Task | None:
    task_maybe = [task for task in tasks if task.id == task_id]

    if len(task_maybe) == 0:
        return None

    return task_maybe[0]


class ParserNames(enum.Enum):
    pass


for parser_name in parsers.keys():
    extend_enum(ParserNames, parser_name, parser_name)


class SelectParser(BaseModel):
    name: str = Field(title='Название')
    description: str = Field(title='Описание')
    parsers_enum: ParserNames = Field(title="Доступные парсеры")
    eta: datetime = Field(title="Дата запуска")


@fast_api_app.get("/api/", response_model=FastUI, response_model_exclude_none=True)
def main_page() -> list[AnyComponent]:
    global tasks
    tasks = db.get_tasks()
    return [
        c.Page(
            components=[
                c.Heading(text="Расписание парсеров", level=1),
                c.Div(components=[c.Button(text="Добавить задачу в очередь", on_click=PageEvent(name='new-task'))]),
                c.Table(
                    data_model=Task,
                    data=tasks,
                    columns=[
                        DisplayLookup(field='name', on_click=GoToEvent(url='/task/{id}')),
                        DisplayLookup(field='parser'),
                        DisplayLookup(field='eta', mode=DisplayMode.datetime),
                        DisplayLookup(field='status')
                    ],
                    no_data_message='Нет задач'
                ),
                c.Modal(
                    title='Новая задача',
                    open_trigger=PageEvent(name='new-task'),
                    body=[
                        c.ModelForm(
                            model=SelectParser,
                            submit_url="/api/click",
                        ),
                    ]
                )
            ]
        )
    ]


@fast_api_app.get("/api/refresh")
def refresh():
    return [c.FireEvent(event=GoToEvent(url='/'))]


@fast_api_app.post("/api/click")
def event(form: Annotated[SelectParser, fastui_form(SelectParser)]):
    setup_parser(form.name, form.description, form.parsers_enum.value, form.eta)
    return [c.FireEvent(event=GoToEvent(url='/refresh'))]


@fast_api_app.get("/api/download/{task_id}", response_model=FastUI, response_model_exclude_none=True)
def download_result(task_id: str):
    print('download')
    return FileResponse(path=f'{db.PARSING_RESULTS}/{task_id}.txt',
                        filename=f'{get_task(task_id).name}_result.txt',
                        media_type='application/octet-stream',
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@fast_api_app.post("/api/cancel/{task_id}")
def revoke_task(task_id: str):
    print('cancel')
    cancel_task(task_id)
    return [c.FireEvent(event=GoToEvent(url='/refresh'))]


@fast_api_app.post("/api/run/{task_id}")
def run_task_now(task_id: str):
    print('exec now')
    task = get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    cancel_task(task_id)
    setup_parser(task.name, task.description, task.parser, datetime.now().replace(microsecond=0))
    return [c.FireEvent(event=GoToEvent(url='/refresh'))]


@fast_api_app.get("/api/task/{task_id}", response_model=FastUI, response_model_exclude_none=True)
def get_task_page(task_id: str) -> list[AnyComponent]:
    task = get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    body = [
        c.Link(components=[c.Text(text='<- Назад')], on_click=BackEvent()),
        c.Heading(text=f'Задача {task.name}'),
        c.Paragraph(text=f'ID: {task.id}'),
        c.Paragraph(text=f'Описание: {task.description}'),
        c.Paragraph(text=f'Статус: {task.status}')
    ]
    if task.status == db.TaskStatus.PLANNED_TASK.value:
        body += [
            c.Div(components=[c.Button(text='Выполнить сейчас', on_click=PageEvent(name='run-task-now'))]),
            c.Form(
                form_fields=[c.FormFieldInput(name='task', title='', initial=task_id, html_type='hidden')],
                submit_url=f'/api/run/{task_id}',
                submit_trigger=PageEvent(name='run-task-now'),
                footer=[]
            ),
            c.Div(components=[
                c.Button(text='Отменить задачу', named_style='warning', on_click=PageEvent(name='delete-task'))]),
            c.Form(
                form_fields=[c.FormFieldInput(name='task', title='', initial=task_id, html_type='hidden')],
                submit_url=f'/api/cancel/{task_id}',
                submit_trigger=PageEvent(name='delete-task'),
                footer=[]
            )
        ]
    else:
        if task.result != 'Результат не найден':
            text = 'Скачать файл ошибки' if task.status == db.TaskStatus.ERROR_TASK.value else 'Скачать результат'
            body += [c.Link(components=[
                c.Text(text=text)], on_click=GoToEvent(url=f'/api/download/{task_id}', target='_blank'))]
        else:
            body += [c.Paragraph(text='Файл не найден!')]

    return [c.Page(components=body)]


@fast_api_app.get('/{path:path}')
async def html_landing() -> HTMLResponse:
    """Simple HTML page which serves the React app, comes last as it matches all paths."""
    return HTMLResponse(prebuilt_html(title='Парсеры'))
