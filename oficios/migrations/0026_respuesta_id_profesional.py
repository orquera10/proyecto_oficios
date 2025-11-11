from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        ('oficios', '0025_alter_oficio_nro_oficio_nonunique'),
    ]

    operations = [
        migrations.AddField(
            model_name='respuesta',
            name='id_profesional',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='respuestas_como_profesional', to=settings.AUTH_USER_MODEL, verbose_name='Profesional'),
        ),
    ]
