from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('oficios', '0021_respuesta'),
    ]

    operations = [
        migrations.RenameField(
            model_name='respuesta',
            old_name='oficio',
            new_name='id_oficio',
        ),
        migrations.RenameField(
            model_name='respuesta',
            old_name='usuario',
            new_name='id_usuario',
        ),
        migrations.RenameField(
            model_name='respuesta',
            old_name='detalle',
            new_name='respuesta',
        ),
        migrations.RenameField(
            model_name='respuesta',
            old_name='archivo_pdf',
            new_name='respuesta_pdf',
        ),
        migrations.AddField(
            model_name='respuesta',
            name='id_institucion',
            field=models.ForeignKey(
                related_name='respuestas',
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='oficios.institucion',
                verbose_name='Institución',
            ),
        ),
        migrations.AddField(
            model_name='respuesta',
            name='fecha_hora',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Fecha y hora de la respuesta'),
        ),
        migrations.AddField(
            model_name='respuesta',
            name='creacion',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='Creación'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='respuesta',
            name='modificacion',
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now, verbose_name='Modificación'),
            preserve_default=False,
        ),
        migrations.AlterModelOptions(
            name='respuesta',
            options={'ordering': ['-fecha_hora', '-creacion'], 'verbose_name': 'Respuesta', 'verbose_name_plural': 'Respuestas'},
        ),
    ]

