from django.db import models
import uuid
# Create your models here.
class User(models.Model):
    aadhar_id = models.CharField(max_length=50, unique=True, primary_key=True)
    name = models.CharField(max_length=100)
    email_id = models.EmailField(unique=True)
    annual_income = models.DecimalField(max_digits=15, decimal_places=2)
    credit_score = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name


class Loan(models.Model):
    
    LOAN_TYPES = (
        ('Car', 'Car'),
        ('Home', 'Home'),
        ('Education', 'Education'),
        ('Personal', 'Personal'),
    )
    

    loan_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    loan_type = models.CharField(max_length=20, choices=LOAN_TYPES)
    loan_amount = models.DecimalField(max_digits=15, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    term_period = models.IntegerField(help_text="Loan period in months")
    disbursement_date = models.DateField()
    emi = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    last_emi = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount_due = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    remaining_balance = models.DecimalField(max_digits=15, decimal_places=2, null=True)

    def __str__(self):
        return f"{self.loan_type} Loan for {self.user.name}"
    

class EMI(models.Model):
    emi_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan = models.ForeignKey(Loan, related_name='emis', on_delete=models.CASCADE)
    due_date = models.DateField()
    amount_due = models.DecimalField(max_digits=15, decimal_places=2)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"EMI {self.emi_id} for Loan {self.loan.loan_id}"
    
class Transaction(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE)
    date = models.DateField()
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2)
    principal_paid = models.DecimalField(max_digits=15, decimal_places=2)
    interest_paid = models.DecimalField(max_digits=15, decimal_places=2)
    remaining_balance = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return f"Transaction on {self.date} for Loan {self.loan.uuid}"