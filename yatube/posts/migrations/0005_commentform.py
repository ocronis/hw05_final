# Generated by Django 2.2.16 on 2023-02-25 20:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0004_comment'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommentForm',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(help_text='Текст нового комментария', verbose_name='Текст')),
            ],
        ),
    ]
