from datetime import timedelta
from django.contrib.auth.models import User
from loanapp.models import EMI, Loan, Transaction
from loanapp.serializers import EMISerializer, LoanSerializer, PaymentSerializer, TransactionSerializer, UserSerializer
from rest_framework import generics, status
from rest_framework.response import Response
from .tasks import credit_score_calculator

class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserSerializer
    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            credit_score_calculator.delay(user.aadhar_id)
            return Response ({"unique_user_id":user.aadhar_id}, status=status.HTTP_201_CREATED)
        except Exception as e:   
            data = {"error_message":str(e)}  
            return Response(data, status=status.HTTP_400_BAD_REQUEST) 

class LoanView(generics.CreateAPIView):
    serializer_class = LoanSerializer
    def post(self, request):
        try:
            serializer = self.get_serializer(data=request.data)
            print(request.data)
            serializer.is_valid(raise_exception=True)
            loan_application = serializer.save()
            due_dates = EMISerializer(EMI.objects.filter(loan=loan_application), many=True).data
            return Response({
                'error': None,
                'loan_id': loan_application.loan_id,
                'due_dates': due_dates
            }, status=status.HTTP_200_OK)
        except Exception as e:   
            data = {"error_message":str(e)}  
            return Response(data, status=status.HTTP_400_BAD_REQUEST) 

class MakePaymentView(generics.CreateAPIView):
    serializer_class = PaymentSerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            transact = serializer.save()
            return Response({
                "error": None,
                "status":"payment received"
            }, status=status.HTTP_200_OK)
        except Exception as e:   
            data = {"error_message":str(e)}  
            return Response(data, status=status.HTTP_400_BAD_REQUEST) 


class LoanStatementView(generics.RetrieveAPIView):
    def get(self, request, loan_id):
        # loan_id = request.query_params.get('loan_id')
        try:
            if not loan_id:
                return Response({"error": "Loan ID is required."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                loan = Loan.objects.get(loan_id=loan_id)
            except Loan.DoesNotExist:
                return Response({"error": "Loan does not exist or is closed."}, status=status.HTTP_400_BAD_REQUEST)

            transactions_history = Transaction.objects.filter(loan=loan).order_by('date')

            upcoming_emis = EMI.objects.filter(loan=loan, is_paid=False).order_by('due_date')

            data = {
                "loan_id": loan_id,
                "transactions_history": TransactionSerializer(transactions_history, many=True).data,
                "upcoming_emis": EMISerializer(upcoming_emis, many=True).data
            }

            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            data = {"error_message":str(e)}  
            return Response(data, status=status.HTTP_400_BAD_REQUEST) 