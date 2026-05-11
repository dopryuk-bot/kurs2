from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedules', '0002_schedule_classroom'),
    ]

    operations = [
        migrations.AddField(
            model_name='schedule',
            name='subgroup',
            field=models.CharField(
                blank=True,
                choices=[('A', 'А'), ('B', 'Б')],
                help_text='Лише для лабораторних. NULL — вся група.',
                max_length=1,
                null=True,
                verbose_name='підгрупа',
            ),
        ),
        migrations.AlterUniqueTogether(
            name='schedule',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='schedule',
            constraint=models.UniqueConstraint(
                condition=models.Q(subgroup__isnull=True),
                fields=['group', 'semester', 'weekday', 'lesson_number', 'week_type'],
                name='unique_schedule_no_subgroup',
            ),
        ),
        migrations.AddConstraint(
            model_name='schedule',
            constraint=models.UniqueConstraint(
                condition=models.Q(subgroup__isnull=False),
                fields=['group', 'semester', 'weekday', 'lesson_number', 'week_type', 'subgroup'],
                name='unique_schedule_with_subgroup',
            ),
        ),
    ]
