import json
from datetime import date

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.attendance import services
from apps.attendance.models import AttendanceStatus
from apps.schedules.models import Schedule
from core.decorators import role_required


def _check_starosta_group_access(user, schedule: Schedule) -> None:
    """Raises PermissionDenied if a starosta tries to access another group's session."""
    if user.role != 'starosta':
        return
    try:
        if user.starosta_profile.group_id != schedule.group_id:
            raise PermissionDenied
    except AttributeError:
        raise PermissionDenied


def _check_teacher_schedule_access(user, schedule: Schedule) -> None:
    """Raises PermissionDenied if a teacher tries to access another teacher's session."""
    if user.role != 'teacher':
        return
    if schedule.teacher_id != user.id:
        raise PermissionDenied


@login_required
@role_required('starosta', 'teacher', 'admin')
def session_view(request, schedule_id, lesson_date):
    """Renders the attendance sheet for a specific lesson on a specific date."""
    schedule = get_object_or_404(
        Schedule.objects.select_related('subject', 'group', 'teacher'),
        pk=schedule_id,
    )
    _check_starosta_group_access(request.user, schedule)
    _check_teacher_schedule_access(request.user, schedule)

    records, created = services.get_or_create_session(schedule, lesson_date, request.user)
    summary = services.get_session_summary(schedule, lesson_date)
    update_url = reverse('attendance:update_status', args=[schedule_id, lesson_date])

    return render(request, 'attendance/session.html', {
        'schedule': schedule,
        'lesson_date': lesson_date,
        'records': records,
        'summary': summary,
        'statuses': AttendanceStatus.choices,
        'created': created,
        'update_url': update_url,
    })


@login_required
@role_required('starosta', 'teacher', 'admin')
@require_POST
def update_status_ajax(request, schedule_id, lesson_date):
    """AJAX endpoint: update a single student's attendance status."""
    try:
        body = json.loads(request.body)
        student_id = int(body['student_id'])
        status = body['status']
    except (KeyError, ValueError, json.JSONDecodeError):
        return JsonResponse({'error': 'Невірний формат запиту'}, status=400)

    schedule = get_object_or_404(Schedule, pk=schedule_id)
    _check_starosta_group_access(request.user, schedule)
    _check_teacher_schedule_access(request.user, schedule)

    try:
        record = services.update_attendance_status(
            schedule=schedule,
            lesson_date=lesson_date,
            student_id=student_id,
            status=status,
            updated_by=request.user,
        )
    except ValueError as exc:
        return JsonResponse({'error': str(exc)}, status=400)

    return JsonResponse({
        'success': True,
        'student_id': record.student_id,
        'status': record.status,
        'status_display': record.get_status_display(),
    })


@login_required
@role_required('starosta', 'teacher', 'admin')
def history_view(request):
    """Shows recent attendance sessions for the starosta's group or teacher's lessons."""
    user = request.user
    sessions = []

    if user.role == 'starosta':
        try:
            group = user.starosta_profile.group
            sessions = services.get_recent_sessions(group, limit=20)
        except AttributeError:
            pass
    elif user.role == 'teacher':
        sessions = services.get_teacher_recent_sessions(user, limit=20)

    return render(request, 'attendance/history.html', {
        'sessions': sessions,
    })
