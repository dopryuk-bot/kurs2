"""
Timetable grid builder — converts QuerySet into template-ready structure.
"""
from datetime import date, timedelta

from apps.schedules.constants import (
    LESSON_TIMES,
    WEEKDAY_NAMES_UK,
    WEEKDAY_SHORT_UK,
)
from apps.schedules.services.semester import get_active_semester, get_week_info


def get_monday(target_date: date) -> date:
    return target_date - timedelta(days=target_date.weekday())


def navigate_week(monday: date, direction: str) -> date:
    delta = timedelta(weeks=1)
    return monday - delta if direction == 'prev' else monday + delta


def build_timetable_grid(schedules) -> tuple[dict, list[int]]:
    """
    Converts a flat QuerySet into a 2D grid: {weekday: {lesson_number: [Schedule, ...]}}.
    Returns (grid, sorted list of lesson numbers that appear in the data).
    """
    grid: dict[int, dict] = {day: {} for day in range(6)}
    used_lessons: set[int] = set()

    for s in schedules:
        grid[s.weekday].setdefault(s.lesson_number, []).append(s)
        used_lessons.add(s.lesson_number)

    return grid, sorted(used_lessons)


def build_timetable_context(schedules, target_date: date, semester=None) -> dict:
    """
    Returns a fully template-ready timetable context dict.

    Row structure:
        rows[i] = {
            'lesson_number': int,
            'start_time': time,
            'end_time': time,
            'cells': [{'slot': Schedule|None, 'is_today': bool, 'date': date}, ...]
        }
    """
    if semester is None:
        semester = get_active_semester()

    monday = get_monday(target_date)
    today = date.today()
    grid, used_lessons = build_timetable_grid(schedules)

    # Column metadata
    columns = []
    for day_idx in range(6):
        col_date = monday + timedelta(days=day_idx)
        columns.append({
            'index': day_idx,
            'name': WEEKDAY_NAMES_UK[day_idx],
            'short': WEEKDAY_SHORT_UK[day_idx],
            'date': col_date,
            'is_today': col_date == today,
        })

    # Row metadata — each cell carries its column context for the template
    rows = []
    lesson_range = used_lessons if used_lessons else range(1, 7)
    for lesson_num in lesson_range:
        start, end = LESSON_TIMES.get(lesson_num, ('', ''))
        cells = []
        for day_idx, col in enumerate(columns):
            schedules_for_cell = grid[day_idx].get(lesson_num, [])
            cells.append({
                'slots': schedules_for_cell,
                'slot': schedules_for_cell[0] if schedules_for_cell else None,
                'is_today': col['is_today'],
                'date': col['date'],
            })
        rows.append({
            'lesson_number': lesson_num,
            'start_time': start,
            'end_time': end,
            'cells': cells,
        })

    week_info = get_week_info(monday, semester) if semester else {}

    return {
        'columns': columns,
        'rows': rows,
        'monday': monday,
        'friday': monday + timedelta(days=4),
        'prev_monday': navigate_week(monday, 'prev'),
        'next_monday': navigate_week(monday, 'next'),
        'semester': semester,
        **week_info,
    }
