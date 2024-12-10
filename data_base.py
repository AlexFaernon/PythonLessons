import sqlite3
from os import listdir
from enum import Enum
from task import Task
from datetime import datetime

PARSING_RESULTS = 'Parsing results'
TASKS_DB = 'tasks.db'

main_connection = sqlite3.connect(TASKS_DB)
main_cursor = main_connection.cursor()
main_cursor.execute('''
CREATE TABLE IF NOT EXISTS Tasks (
id INTEGER PRIMARY KEY,
taskId TEXT NOT NULL,
name TEXT NOT NULL,
description TEXT NOT NULL,
eta TEXT NOT NULL,
parser TEXT NOT NULL,
status TEXT
)
''')
main_connection.commit()
main_connection.close()


class TaskStatus(Enum):
    PLANNED_TASK = 'Запланирована'
    COMPLETED_TASK = 'Выполнена'
    ERROR_TASK = 'Ошибка'


def add_task(task_id: str, name: str, description: str, eta: str, parser: str):
    connection = sqlite3.connect(TASKS_DB)
    cursor = connection.cursor()
    cursor.execute('INSERT INTO Tasks (taskId, name, description, eta, parser, status) VALUES (?, ?, ?, ?, ?, ?)',
                   (task_id, name, description, eta, parser, TaskStatus.PLANNED_TASK.value))
    connection.commit()
    connection.close()


def get_tasks() -> list[Task]:
    connection = sqlite3.connect(TASKS_DB)
    cursor = connection.cursor()

    cursor.execute('SELECT * FROM Tasks')
    tasks_raw = cursor.fetchall()

    tasks = []
    all_results = [file for file in listdir(PARSING_RESULTS)]
    for taskRecord in tasks_raw:
        task_id = taskRecord[1]
        name = taskRecord[2]
        desc = taskRecord[3]
        eta = datetime.strptime(taskRecord[4], '%Y-%m-%d %H:%M:%S')
        parser = taskRecord[5]
        status = taskRecord[6]
        result = ''
        if status != TaskStatus.PLANNED_TASK:
            result_maybe = [result for result in all_results if result.startswith(task_id)]
            result = result_maybe[0] if len(result_maybe) == 1 else 'Результат не найден'
        tasks.append(
            Task(id=task_id, name=name, description=desc, parser=parser, eta=eta, status=status, result=result))

    connection.close()
    return tasks


def update_task_status(task_id: str, new_status: TaskStatus):
    connection = sqlite3.connect(TASKS_DB)
    cursor = connection.cursor()
    cursor.execute('UPDATE Tasks SET status = ? WHERE taskId = ?', (new_status.value, task_id))
    connection.commit()
    connection.close()
    pass


def delete_task(task_id: str):
    connection = sqlite3.connect(TASKS_DB)
    cursor = connection.cursor()
    cursor.execute('DELETE FROM Tasks WHERE taskId = ?', (task_id,))
    connection.commit()
    connection.close()
