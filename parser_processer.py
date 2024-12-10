from datetime import datetime, timedelta
from importlib import import_module
from os import listdir
from time import timezone

from celery import Celery

from data_base import add_task, update_task_status, delete_task, TaskStatus, PARSING_RESULTS

PARSERS_FOLDER = 'Parsers'
celeryApp = Celery("myapp", broker='redis://localhost:32768/0', backend='redis://localhost:32768/0')
parsers = {parser: import_module(f"Parsers.{parser}") for parser in [file.removesuffix('.py')
                                                                     for file in listdir(PARSERS_FOLDER)
                                                                     if file.endswith(".py")]}


def setup_parser(name: str, description: str, parser_name: str, eta: datetime):
    celery_eta = eta + timedelta(seconds=timezone)
    task_id = launch_parser.apply_async(args=(parser_name,), eta=celery_eta).task_id
    add_task(task_id, name, description, str(eta), parser_name)


def save_parser_result(task_id: str, result: str):
    result_file = open(fr"{PARSING_RESULTS}\{task_id}.txt", 'w')
    result_file.write(result)
    result_file.close()


def cancel_task(task_id: str):
    celeryApp.control.revoke(task_id, terminate=True)
    delete_task(task_id)


@celeryApp.task(bind=True)
def launch_parser(self, parser_name: str):
    task_id = self.request.id
    result: str
    status: TaskStatus
    try:
        result = str(parsers[parser_name].run())
        status = TaskStatus.COMPLETED_TASK
    except Exception as e:
        result = str(e)
        status = TaskStatus.ERROR_TASK

    save_parser_result(task_id, result)
    update_task_status(task_id, status)
