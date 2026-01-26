from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('personas', '0006_alter_parte_dni'),
    ]

    operations = [
        migrations.RenameField(
            model_name='nino',
            old_name='direccion',
            new_name='domicilio_principal',
        ),
        migrations.AddField(
            model_name='nino',
            name='domicilio_secundario',
            field=models.CharField(max_length=200, blank=True, null=True),
        ),
    ]
