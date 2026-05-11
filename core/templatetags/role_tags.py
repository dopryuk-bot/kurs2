from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def has_role(context, *roles):
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return False
    return request.user.role in roles


@register.filter(name='dict_get')
def dict_get(d, key):
    """Allows dict[key] access in templates: {{ mydict|dict_get:key }}"""
    if isinstance(d, dict):
        return d.get(key)
    return None


@register.filter
def status_badge(status):
    badge_map = {
        'PRESENT': 'bg-success',
        'ABSENT': 'bg-danger',
        'EXCUSED': 'bg-warning text-dark',
        'LATE': 'bg-info text-dark',
    }
    return badge_map.get(status, 'bg-secondary')


@register.filter
def weekday_name(weekday_int):
    names = ['Понеділок', 'Вівторок', 'Середа', 'Четвер', 'П\'ятниця', 'Субота']
    try:
        return names[int(weekday_int)]
    except (IndexError, ValueError, TypeError):
        return ''


@register.filter
def lesson_type_color(lesson_type):
    colors = {
        'lecture': 'primary',
        'lab': 'success',
        'practice': 'warning',
    }
    return colors.get(lesson_type, 'secondary')


@register.filter
def week_type_badge(week_type):
    badges = {
        'ODD': 'badge bg-info text-dark',
        'EVEN': 'badge bg-warning text-dark',
    }
    return badges.get(week_type, 'badge bg-secondary')
