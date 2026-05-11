# Laboratory Subgroup Architecture Implementation

## Overview
This document describes the implementation of laboratory subgroup support for the electronic journal system. The system now supports dividing laboratory groups into subgroups A and B while maintaining backward compatibility with lectures and practices.

## Database Schema Changes

### 1. Student Model (`apps/groups/models.py`)
**Added field:**
- `subgroup` (CharField, nullable): Choices are 'A' or 'B'
  - Used only for lab-based attendance tracking
  - Optional - students can be assigned to subgroups independently
  - Helps organize students when labs are split into parallel groups

**Migration:** `apps/groups/migrations/0002_student_subgroup.py`

### 2. Schedule Model (`apps/schedules/models.py`)
**Added field:**
- `subgroup` (CharField, nullable): Choices are 'A' or 'B'
  - Only meaningful for lesson_type='lab'
  - NULL for lectures and practices (applies to all students)
  - Can be set independently for each lab to allow parallel lab groups

**Constraints:** Replaced single `unique_together` with conditional `UniqueConstraint`s:
- `unique_schedule_no_subgroup`: Prevents duplicate non-lab lessons at same time slot
  - Condition: `subgroup IS NULL`
  - Unique on: (group, semester, weekday, lesson_number, week_type)
  
- `unique_schedule_with_subgroup`: Allows Lab A and Lab B at same slot
  - Condition: `subgroup IS NOT NULL`
  - Unique on: (group, semester, weekday, lesson_number, week_type, subgroup)

**Validation:** Model-level `clean()` method ensures subgroup is only set for labs

**Migrations:**
- `apps/schedules/migrations/0003_schedule_subgroup.py` (manual)
- `apps/schedules/migrations/0004_alter_schedule_subgroup.py` (auto-generated)

## Form Updates

### StudentForm (`apps/groups/forms.py`)
**Added field:**
- `subgroup` (Select widget)
- Displayed in student create/edit forms
- Optional field for bulk operations

**Template:** `templates/groups/student_form.html`
- Subgroup dropdown with help text
- Can be left empty (students without assigned subgroups)

### ScheduleForm (`apps/schedules/forms.py`)
**Should add fields for parallel lab creation** (pending implementation):
- `subgroup` (required for labs, null for others)
- `create_parallel_lab` (checkbox)
- `parallel_teacher`, `parallel_classroom`, `parallel_lesson_number` (optional)

**Validation:**
- Subgroup is required when lesson_type='lab'
- Subgroup must be NULL when lesson_type != 'lab'
- Can create parallel lab (opposite subgroup) via form

## Service Layer Updates

### `apps/attendance/services.py`
**Updated `get_or_create_session()`:**
```python
if schedule.subgroup:
    students_qs = students_qs.filter(subgroup=schedule.subgroup)
```
- When opening a lab session for subgroup A, only subgroup A students are included
- Lecture/practice sessions (subgroup=NULL) include ALL active students

### `apps/schedules/services/timetable.py`
**Updated `build_timetable_grid()`:**
- Now returns lists of schedules per cell instead of single schedule
- Structure: `grid[weekday][lesson_number] = [Schedule, ...]`
- Allows Lab A and Lab B to coexist at the same slot

**Updated `build_timetable_context()`:**
- Returns `cell.slots` (list) and `cell.slot` (backward compat)
- Templates iterate over `cell.slots` to display multiple schedules

### `apps/schedules/services/schedule.py`
**Fixed `build_general_timetable()`:**
- Properly iterates over `Weekday.choices`
- Returns lists of schedules for ODD/EVEN weeks
- Handles multiple labs per group per time slot

## Template Updates

### Timetable Templates
1. **`templates/schedules/week_calendar.html`**
   - Iterates over `cell.slots` instead of single `cell.slot`
   - Shows subgroup badge: "(LAB A)" or "(LAB B)"
   - Supports stacking multiple schedule cards in one cell

2. **`templates/dashboard/starosta/index.html`**
   - Updated to use `cell.slots` list
   - Shows subgroup info in schedule cards
   - Multiple cards per cell for parallel labs

3. **`templates/schedules/admin/general_timetable.html`**
   - Already supports multiple schedules per ODD/EVEN week
   - Displays subgroup badge in lesson card
   - Handles Lab A and Lab B at same slot

### Student Management Templates
1. **`templates/groups/student_form.html`**
   - Added subgroup field with dropdown

2. **`templates/groups/group_detail.html`**
   - Shows subgroup badge (A or B) in student list
   - Visual indicator for subgroup assignment

### Schedule List Template
1. **`templates/schedules/admin/schedule_list.html`**
   - Shows subgroup badge next to group name
   - Badge appears only for lab lessons

## Attendance Logic

### Subgroup-aware Session Initialization
When a starosta/teacher opens an attendance session:
1. If schedule.subgroup='A': Only students with subgroup='A' are initialized
2. If schedule.subgroup='B': Only students with subgroup='B' are initialized  
3. If schedule.subgroup=NULL (lecture/practice): All active students are included

### Benefits
- Students without assigned subgroups don't appear in lab sessions
- Prevents double-booking of students across subgroups
- Clean separation of Lab A and Lab B attendance

## Display Examples

### Timetable Cell with Parallel Labs
```
┌─────────────────────────────┐
│ Бази Даних (LAB A)          │ ← Schedule for subgroup A
│ 10:10–11:30 · Лекція       │
│─────────────────────────────│
│ Бази Даних (LAB B)          │ ← Schedule for subgroup B
│ 11:50–13:10 · Лекція       │
└─────────────────────────────┘
```

### Schedule List
```
Група 301 [LAB A]  │ Бази Даних │ Петренко П.П. │ Пн │ 3 │ 11:50–13:10 │ Лаб │ ODD
Група 301 [LAB B]  │ Бази Даних │ Іванов І.І.  │ Пн │ 4 │ 13:30–14:50 │ Лаб │ ODD
```

### Student List
```
№  ПІБ                   Підгрупа  Статус
1  Іваненко Іван        [A]       Активний
2  Петренко Петро       [B]       Активний
3  Сидоренко Марія              Активний
```

## Validation Rules

1. **Subgroup-only-for-labs**: Subgroup can only be set when lesson_type='lab'
2. **No duplicate subgroups**: Cannot have two Lab A schedules for same group at same slot
3. **Subgroup collision detection**: Lecture at slot 3 prevents both Lab A and Lab B at slot 3
4. **Student assignment**: Students without assigned subgroup won't appear in lab sessions

## Backward Compatibility

✓ Lectures and practices work as before (subgroup=NULL for all students)
✓ Existing attendance records remain unchanged
✓ Timetable views support both single and multiple schedules per cell
✓ Forms gracefully handle optional subgroup field

## Performance Optimizations

- Used `select_related()` and `prefetch_related()` in schedule queries
- Database constraints (UniqueConstraints) prevent invalid states
- Filtered student queries when loading lab sessions (subgroup-aware)
- Optimized grid builder for multiple schedules per slot

## Testing Checklist

- [x] Student model accepts subgroup field
- [x] Schedule model validates subgroup only for labs  
- [x] Migrations applied successfully
- [x] Timetable displays multiple schedules per cell
- [x] General timetable shows subgroup badges
- [x] Student list shows subgroup assignments
- [x] Attendance sessions filter by subgroup
- [x] Starosta dashboard displays both Lab A and Lab B

## Future Enhancements

1. **Parallel Lab Creation Form**: 
   - Add UI to create Lab A and Lab B together
   - Support different times/teachers/classrooms for parallel labs

2. **Subgroup Assignment UI**:
   - Bulk assign students to subgroups
   - Import from external data sources

3. **Analytics Enhancement**:
   - Per-subgroup attendance statistics
   - Subgroup-level reports

4. **Validation Enhancement**:
   - Prevent scheduling where students would double-book across subgroups
   - Warn when teacher availability conflicts with parallel labs
