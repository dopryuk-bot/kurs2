"""
Re-export all schedule services so existing imports remain unchanged:
    from apps.schedules import services
    services.get_active_semester()
"""
from apps.schedules.services.schedule import (
    apply_lesson_times,
    build_general_timetable,
    get_all_schedules,
    get_conflicts,
    get_schedules_for_group,
    get_schedules_for_teacher,
    has_conflicts,
)
from apps.schedules.services.semester import (
    get_active_semester,
    get_first_study_week_date,
    get_week_info,
    validate_semester_dates,
)
from apps.schedules.services.timetable import (
    build_timetable_context,
    build_timetable_grid,
    get_monday,
    navigate_week,
)

__all__ = [
    # semester
    'get_active_semester',
    'get_first_study_week_date',
    'get_week_info',
    'validate_semester_dates',
    # schedule
    'get_conflicts',
    'has_conflicts',
    'apply_lesson_times',
    'build_general_timetable',
    'get_schedules_for_group',
    'get_schedules_for_teacher',
    'get_all_schedules',
    # timetable
    'build_timetable_context',
    'build_timetable_grid',
    'get_monday',
    'navigate_week',
]
