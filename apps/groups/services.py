from django.db.models import Count, Q

from apps.groups.models import Group, Student


def get_groups_overview():
    """All groups with active student count and prefetched starostas."""
    return (
        Group.objects.annotate(
            active_student_count=Count('students', filter=Q(students__is_active=True)),
        )
        .prefetch_related('starostas__user')
        .order_by('course', 'name')
    )


def bulk_create_students(group: Group, names: list[str]) -> tuple[int, list[str]]:
    """
    Creates students for the group from a list of full names.
    Skips duplicates (case-insensitive). Returns (created_count, skipped_names).
    """
    existing_lower = {
        n.lower()
        for n in Student.objects.filter(group=group).values_list('full_name', flat=True)
    }
    created = 0
    skipped: list[str] = []
    for name in names:
        if name.lower() in existing_lower:
            skipped.append(name)
        else:
            Student.objects.create(full_name=name, group=group)
            existing_lower.add(name.lower())
            created += 1
    return created, skipped
