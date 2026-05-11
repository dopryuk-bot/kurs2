"""
Centralized lesson time configuration for ЧНУ ФМІ schedule.
All time references in the system use this single source of truth.
"""
from datetime import time

LESSON_TIMES: dict[int, tuple[time, time]] = {
    1: (time(8, 20),  time(9, 40)),
    2: (time(9, 50),  time(11, 10)),
    3: (time(11, 30), time(12, 50)),
    4: (time(13, 0),  time(14, 20)),
    5: (time(14, 40), time(16, 0)),
    6: (time(16, 10), time(17, 30)),
}

LESSON_CHOICES = [
    (num, f'{num} пара  ({start.strftime("%H:%M")} – {end.strftime("%H:%M")})')
    for num, (start, end) in LESSON_TIMES.items()
]

WEEKDAY_NAMES_UK = [
    'Понеділок',
    'Вівторок',
    'Середа',
    'Четвер',
    'П\'ятниця',
    'Субота',
]

WEEKDAY_SHORT_UK = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб']
