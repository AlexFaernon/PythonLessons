from datetime import datetime

from pydantic import BaseModel, Field


class Task(BaseModel):
    id: str = Field(title="ID задачи")
    name: str = Field(title='Имя')
    description: str = Field(title='Описание')
    parser: str = Field(title="Парсер")
    eta: datetime = Field(title="Назначенное время")
    status: str = Field(title="Статус", default="???")
    result: str = Field(title="Результат", default="")
