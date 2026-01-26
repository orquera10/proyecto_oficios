from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('oficios', '0028_categoriajuzgado_alter_caratula_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='institucion',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True, verbose_name='Email'),
        ),
    ]
