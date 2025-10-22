from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oficios', '0018_add_tipo_expte_fields'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='oficio',
            name='tipo',
        ),
    ]
