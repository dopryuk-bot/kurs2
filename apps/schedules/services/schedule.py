"""
Schedule CRUD and conflict detection services.
"""
from django.db.models import Q

from apps.schedules.constants import LESSON_TIMES
from apps.schedules.models import LessonType, Schedule, Semester, WeekType, Weekday


def get_conflicts(
    semester: Semester,
    weekday: int,
    lesson_number: int,
    week_type: str,
    teacher_id: int,
    group_id: int,
    lesson_type: str,
    subgroup: str | None = None,
    exclude_pk: int | None = None,
) -> dict[str, list]:
    """
    Detects scheduling conflicts for a lesson slot.
    Returns dict with 'teacher' and 'group' conflict lists.
    Each conflict is a Schedule instance.
    """
    base_qs = Schedule.objects.filter(
        semester=semester,
        weekday=weekday,
        lesson_number=lesson_number,
        week_type=week_type,
    ).select_related('subject', 'group', 'teacher')

    if exclude_pk:
        base_qs = base_qs.exclude(pk=exclude_pk)

    teacher_conflicts = list(base_qs.filter(teacher_id=teacher_id))

    group_qs = base_qs.filter(group_id=group_id)
    if lesson_type == LessonType.LAB:
        if subgroup:
            group_conflicts = list(group_qs.filter(
                Q(lesson_type__in=[LessonType.LECTURE, LessonType.PRACTICE])
                | Q(subgroup=subgroup)
            ))
        else:
            group_conflicts = list(group_qs)
    else:
        group_conflicts = list(group_qs)

    return {
        'teacher': teacher_conflicts,
        'group': group_conflicts,
    }


def has_conflicts(
    semester: Semester,
    weekday: int,
    lesson_number: int,
    week_type: str,
    teacher_id: int,
    group_id: int,
    lesson_type: str,
    subgroup: str | None = None,
    exclude_pk: int | None = None,
) -> bool:
    conflicts = get_conflicts(
        semester, weekday, lesson_number, week_type,
        teacher_id, group_id, lesson_type, subgroup, exclude_pk
    )
    return bool(conflicts['teacher'] or conflicts['group'])


def apply_lesson_times(schedule: Schedule) -> Schedule:
    """
    Sets start_time and end_time from LESSON_TIMES based on lesson_number.
    Does not save — caller is responsible.
    """
    if schedule.lesson_number in LESSON_TIMES:
        start, end = LESSON_TIMES[schedule.lesson_number]
        schedule.start_time = start
        schedule.end_time = end
    return schedule


def get_schedules_for_group(group, semester: Semester, week_type: str):
    return (
        Schedule.objects.filter(
            group=group,
            semester=semester,
            week_type=week_type,
        )
        .select_related('subject', 'teacher', 'teacher__teacher_profile')
        .order_by('weekday', 'lesson_number')
    )


def get_schedules_for_teacher(teacher, semester: Semester, week_type: str):
    return (
        Schedule.objects.filter(
            teacher=teacher,
            semester=semester,
            week_type=week_type,
        )
        .select_related('subject', 'group')
        .order_by('weekday', 'lesson_number')
    )


def build_general_timetable(semester: Semester, weekday_filter: int | None = None) -> dict:
    """
    Builds the general (all-groups) timetable for a semester.

    Returns:
        groups  — ordered list of Group objects
        sections — one per weekday that has lessons:
            {weekday_value, weekday_label, rows: [
                {lesson_number, start_time, end_time, cells: [
                    {group, ODD: list[Schedule], EVEN: list[Schedule]}
                ]}
            ]}
    """
    from apps.groups.models import Group

    groups = list(Group.objects.order_by('course', 'name'))

    qs = (
        Schedule.objects.filter(semester=semester)
        .select_related('subject', 'teacher', 'group')
        .order_by('weekday', 'lesson_number', 'subgroup')
    )
    if weekday_filter is not None:
        qs = qs.filter(weekday=weekday_filter)

    data: dict = {}
    for s in qs:
        data.setdefault(s.weekday, {}).setdefault(s.lesson_number, {}).setdefault(s.week_type, {}).setdefault(s.group_id, []).append(s)

    sections = []
    for weekday_val, weekday_label in Weekday.choices:
        wd_data = data.get(weekday_val, {})
        rows = []
        for ln in range(1, 9):
            ln_data = wd_data.get(ln, {})
            odd_schedules = ln_data.get(WeekType.ODD, {})
            even_schedules = ln_data.get(WeekType.EVEN, {})
            if not odd_schedules and not even_schedules:
                continue
            start, end = LESSON_TIMES.get(ln, (None, None))
            cells = [
                {
                    'group': g,
                    'ODD': odd_schedules.get(g.id, []),
                    'EVEN': even_schedules.get(g.id, []),
                }
                for g in groups
            ]
            rows.append({'lesson_number': ln, 'start_time': start, 'end_time': end, 'cells': cells})

        if rows:
            sections.append({'weekday_value': weekday_val, 'weekday_label': weekday_label, 'rows': rows})

    return {'groups': groups, 'sections': sections}


def get_all_schedules(semester: Semester, filters: dict | None = None):
    qs = (
        Schedule.objects.filter(semester=semester)
        .select_related('subject', 'teacher', 'group')
        .order_by('group__name', 'weekday', 'lesson_number', 'week_type', 'subgroup')
    )
    if filters:
        if filters.get('group'):
            qs = qs.filter(group_id=filters['group'])
        if filters.get('teacher'):
            qs = qs.filter(teacher_id=filters['teacher'])
        if filters.get('subject'):
            qs = qs.filter(subject_id=filters['subject'])
        if filters.get('week_type'):
            qs = qs.filter(week_type=filters['week_type'])
        if filters.get('weekday') is not None:
            qs = qs.filter(weekday=filters['weekday'])
    return qs
