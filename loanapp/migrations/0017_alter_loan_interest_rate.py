# Generated by Django 5.1 on 2024-08-21 19:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loanapp', '0016_alter_loan_interest_rate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='loan',
            name='interest_rate',
            field=models.DecimalField(decimal_places=2, max_digits=5),
        ),
    ]
