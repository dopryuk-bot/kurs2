"""
Semester domain services.
"""
from datetime import date, timedelta

from apps.schedules.models import Semester, WeekType


def get_active_semester() -> Semester | None:
    """
    Returns the most relevant semester for today:
    1. Semester whose date range contains today.
    2. If none active — the most recently started one.
    No manual is_active flag needed.
    """
    today = date.today()
    current = (
        Semester.objects.filter(start_date__lte=today, end_date__gte=today)
        .order_by('-start_date')
        .first()
    )
    if current:
        return current
    return Semester.objects.order_by('-start_date').first()


def get_first_study_week_date(start_date: date) -> date:
    """
    Returns the Monday of the week that contains start_date.
    If start_date IS a Monday — returns it as-is.
    """
    return start_date - timedelta(days=start_date.weekday())


def get_week_info(target_date: date, semester: Semester | None = None) -> dict:
    if semester is None:
        semester = get_active_semester()
    if semester is None:
        return {}

    week_number = semester.get_week_number(target_date)
    week_type = semester.get_week_type(target_date)

    if week_number is None:
        return {}

    return {
        'semester': semester,
        'week_number': week_number,
        'week_type': week_type,
        'week_type_display': WeekType(week_type).label if week_type else '',
        'is_odd': week_type == WeekType.ODD,
        'is_even': week_type == WeekType.EVEN,
    }


def validate_semester_dates(start_date: date, end_date: date) -> list[str]:
    errors = []
    if end_date <= start_date:
        errors.append('Дата завершення повинна бути після дати початку.')
    return errors
