from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='subgroup',
            field=models.CharField(
                blank=True,
                choices=[('A', 'А'), ('B', 'Б')],
                help_text='Використовується для розподілу на лабораторні роботи',
                max_length=1,
                null=True,
                verbose_name='підгрупа',
            ),
        ),
    ]
