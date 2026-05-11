from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedules', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='schedule',
            name='classroom',
            field=models.CharField(blank=True, max_length=50, verbose_name='аудиторія'),
        ),
    ]
