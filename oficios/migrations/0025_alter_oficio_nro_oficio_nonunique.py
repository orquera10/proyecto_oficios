from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oficios', '0024_movimientooficio_archivo_pdf'),
    ]

    operations = [
        migrations.AlterField(
            model_name='oficio',
            name='nro_oficio',
            field=models.CharField(max_length=50, verbose_name='Numero de Oficio', blank=True, null=True),
        ),
    ]