from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('oficios', '0029_institucion_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='oficio',
            name='validado_coord',
            field=models.BooleanField(default=False, verbose_name='Validado por coordinación'),
        ),
        migrations.AddField(
            model_name='oficio',
            name='validado_director',
            field=models.BooleanField(default=False, verbose_name='Validado por director'),
        ),
    ]
