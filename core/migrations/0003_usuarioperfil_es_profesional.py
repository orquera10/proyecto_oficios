from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_usuarioperfil_id_institucion'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuarioperfil',
            name='es_profesional',
            field=models.BooleanField(default=False, verbose_name='Es profesional'),
        ),
    ]
