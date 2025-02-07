# Generated by Django 5.1 on 2024-08-20 19:59

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loanapp', '0011_loan_last_emi'),
    ]

    operations = [
        migrations.CreateModel(
            name='EMI',
            fields=[
                ('emi_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('due_date', models.DateField()),
                ('amount_due', models.DecimalField(decimal_places=2, max_digits=15)),
                ('is_paid', models.BooleanField(default=False)),
                ('loan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='emis', to='loanapp.loan')),
            ],
        ),
    ]
