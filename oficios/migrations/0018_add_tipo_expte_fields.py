from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oficios', '0017_alter_movimientooficio_estado_anterior_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='oficio',
            name='tipo',
            field=models.CharField(choices=[('MPA', 'MPA'), ('Judicial', 'Judicial')], default='MPA', max_length=20, verbose_name='Tipo de Oficio'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='oficio',
            name='expte',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Expediente'),
        ),
    ]
