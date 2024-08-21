
from celery import shared_task
from .models import User
import csv
from rest_framework import status
from rest_framework.response import Response
@shared_task
def credit_score_calculator(user_uuid):
    try:
        user = User.objects.get(aadhar_id=user_uuid)
        csv_file_path = '/Users/apple/Downloads/transactions_data_backend__1_.csv'  
    
        balance = 0
        with open(csv_file_path, newline='') as csvfile:
            reader_csv = csv.DictReader(csvfile)
            for row in reader_csv:
                if row['user'] == user.aadhar_id:
                    if row['transaction_type'] == 'CREDIT':
                        balance += int(row['amount'])
                    elif row['transaction_type'] == 'DEBIT':
                        balance -= int(row['amount'])
                    print(f"Transaction Type: {row['transaction_type']}, Amount: {row['amount']} Total Balance :{balance}")

        print(balance)
        if balance >= 1000000:
            credit_score = 900
        elif balance <= 100000:
            credit_score = 300
        else:
            credit_score = 300 + (balance - 100000) // 15000 * 10

        
        user.credit_score = int(credit_score)
        user.save()

    except User.DoesNotExist:
        data = (f"User with UUID {user_uuid} does not exist.")
        return Response(data, status=status.HTTP_400_BAD_REQUEST) 

