# Generated by Django 4.2.4 on 2023-11-06 08:38

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lcfmv', '0006_alter_acordao_arquivo_alter_legislacao_arquivo_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='legislacao',
            name='data_dou',
            field=models.DateField(default=datetime.date(1900, 1, 1), verbose_name='Data de Publicação'),
            preserve_default=False,
        ),
    ]
