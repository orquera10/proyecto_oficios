from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        ('oficios', '0025_alter_oficio_nro_oficio_nonunique'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuarioperfil',
            name='id_institucion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='perfiles', to='oficios.institucion', verbose_name='Institucion'),
        ),
    ]
