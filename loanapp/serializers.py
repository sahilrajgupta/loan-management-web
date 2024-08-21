from requests import Response
from rest_framework import serializers, status
from .models import EMI, Loan, User, Transaction
from datetime import timedelta, date
from rest_framework.response import Response

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['aadhar_id', 'name', 'email_id', 'annual_income']

class LoanSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    class Meta:
        model = Loan
        fields = ['user','loan_type', 'loan_amount', 'interest_rate', 'term_period', 'disbursement_date']

    def validate(self, data):
        user = data.get('user')
        loan_type = data.get('loan_type')
        loan_amount = data.get('loan_amount')
        interest_rate = data.get('interest_rate')
        term_period = data.get('term_period')
        disbursement_date = data.get('disbursement_date')

        if user.credit_score < 450:
            raise serializers.ValidationError('Credit score is below 450')

        if user.annual_income < 150000:
            raise serializers.ValidationError('Annual income must be at greater than 1,50,000.')

        if interest_rate < 14:
            raise serializers.ValidationError("Interest Rates cannot be less than 14%")
      
        loan_limits = {
            'Car': 750000,
            'Home': 8500000,
            'Education': 5000000,
            'Personal': 1000000,
        }

        if loan_type not in loan_limits:
            raise serializers.ValidationError('Invalid loan type.')

        if loan_amount > loan_limits[loan_type]:
            raise serializers.ValidationError(f'Loan amount exceeds the limit for {loan_type} loans.')
        
        emi = self.calculate_emi(loan_amount, disbursement_date,interest_rate,term_period)
        monthly_income = user.annual_income / 12
        max_emi = float(monthly_income)* 0.60
        if emi > max_emi:
            raise serializers.ValidationError('EMI is more than 60% of monthly income.')
        
        t_interest = (emi * term_period) - loan_amount
        if t_interest <= 10000:
            raise serializers.ValidationError('Total interest earned must be greater than Rs. 10,000.')
        data['emi'] = emi
        data['user'] = user
        data['total_amount_due'] = emi*term_period
        print(data['total_amount_due'])
        return data
    #this method is to calculate emi, taking care of to add interest of days between first installment and disbursement days
    def calculate_emi(self, loan_amount, disbursement_date, interest_rate,term_period):
        try:
            daily_ir = interest_rate / 365 / 100
            if disbursement_date.day == 1:
                first_due_date = disbursement_date
            else:
                next_month = disbursement_date.month % 12 + 1
                next_year = disbursement_date.year + (disbursement_date.month // 12)
                if next_month == 1: 
                    next_year += 1

                first_d = disbursement_date.replace(year=next_year, month=next_month, day=1)
            
            first_due_days = (first_d- disbursement_date).days
            print(f"days until first due {first_due_days}")
            first_ir = loan_amount * daily_ir * first_due_days
            i_principal = loan_amount + first_ir

            #standard emi formula
            monthly_ir= interest_rate / 100 / 12
            emi = (i_principal * monthly_ir * (1 + monthly_ir) ** term_period) / \
                ((1 + monthly_ir) ** term_period - 1)
        
            return emi
        except Exception as e:
            data = {"error_message":str(e)}  
            return Response(data, status=status.HTTP_400_BAD_REQUEST) 
    
    def get_due_dates(self, obj):
        try:
            disbursement_date = obj.disbursement_date
            term_period = obj.term_period
            e_amount = obj.emi
            emi_dues = []
            if disbursement_date.day == 1:
                f_due_date = disbursement_date
            else:
                f_due_date = (disbursement_date.replace(day=1) + timedelta(days=32)).replace(day=1)
            for i in range(term_period):
                year = f_due_date.year + (f_due_date.month + i - 1) // 12
                month = (f_due_date.month + i - 1) % 12 + 1
                due_date = date(year, month, 1)
                emi_dues.append({
                    'due_date': due_date.strftime('%Y-%m-%d'),
                    'amount_due': round(e_amount, 2)
                })
            return emi_dues
        except Exception as e:
            data = {"error_message":str(e)}  
            return Response(data, status=status.HTTP_400_BAD_REQUEST) 

    def create(self, validated_data):
        user = validated_data['user']
        loan_application = Loan.objects.create(
            user=user,
            loan_type=validated_data['loan_type'],
            loan_amount=validated_data['loan_amount'],
            interest_rate=validated_data['interest_rate'],
            term_period=validated_data['term_period'],
            disbursement_date=validated_data['disbursement_date'],
            emi = validated_data['emi'],
            total_amount_due = validated_data['total_amount_due'],
            remaining_balance = validated_data['loan_amount']
        )
        emi_datas = self.get_due_dates(loan_application)
        
        for emi_data in emi_datas:
            EMI.objects.create(loan=loan_application, **emi_data)
        return loan_application

class PaymentSerializer(serializers.Serializer):
    loan_id = serializers.UUIDField()  
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    p_date = serializers.DateField() 
    def validate(self, data):
        try:
            loan = Loan.objects.get(loan_id=data['loan_id'])
        except Loan.DoesNotExist:
            raise serializers.ValidationError("Loan does not exist.")

        p_date = data['p_date']
        c_emi = loan.emis.filter(due_date=p_date).first()
        remaining_emis = loan.emis.filter(is_paid=False)
        t_due_amount = sum([emi.amount_due for emi in remaining_emis])
        if data['amount'] == 0:
            raise serializers.ValidationError("Payment amount cannnot be Zero")
        if data['amount']>=t_due_amount:
            raise serializers.ValidationError("Amount paid cannot be greater than total remaining dues")
        if not c_emi:
            raise serializers.ValidationError("No EMI due for the specified payment date.")
        if Transaction.objects.filter(loan=loan, date=p_date).exists():
            raise serializers.ValidationError("Payment has already been made for this date.")
        
        p_emi_date = (p_date.replace(day=1) - timedelta(days=1)).replace(day=1)
        p_emi = loan.emis.filter(due_date=p_emi_date).first()

        if p_emi:
            previous_transactions = Transaction.objects.filter(loan=loan, date=p_emi.due_date)
            if not previous_transactions.exists():
                raise serializers.ValidationError(f"No payment made for the previous EMI due on {p_emi.due_date}. Please pay it first.")

        data['emi'] = c_emi  
        return data
    
    def create(self, validated_data):
        emi = validated_data['emi']
        payment_amount = validated_data['amount']
        interest_paid = emi.amount_due * (emi.loan.interest_rate / 100 / 12)  
        principal_paid = payment_amount - interest_paid  

        if payment_amount<=emi.amount_due:
            emi.amount_due -=payment_amount
            emi.is_paid = True
        else:
            emi.amount_due = 0
            emi.is_paid = True
        emi.save()  
        #here assuming payment is always made on the due date
        transaction = Transaction.objects.create(
            loan=emi.loan,
            date=emi.due_date,  
            amount_paid=validated_data['amount'],
            principal_paid=max(0, principal_paid),  
            interest_paid=max(0, interest_paid),  
            remaining_balance=emi.loan.remaining_balance - principal_paid  
        )

        emi.loan.remaining_balance -= principal_paid
        emi.loan.save()

        self.recalculate_emis(emi.loan, emi.due_date)
        return transaction
    
    #calculates emis after the payment transaction, refreshes emi object with new values
    def recalculate_emis(self, loan,payment_date):
        try:
            remaining_emis = loan.emis.filter(is_paid=False, due_date__gt=payment_date)
            remaining_balance = loan.remaining_balance
            term_period = remaining_emis.count()

            if term_period <= 0:
                return  

            monthly_interest_rate = loan.interest_rate / 100 / 12
            new_emi = (remaining_balance * monthly_interest_rate * (1 + monthly_interest_rate) ** term_period) / \
                    ((1 + monthly_interest_rate) ** term_period - 1)

            if remaining_balance<=0:
                for emi in remaining_emis:
                    emi.amount_due = 0
                    emi.is_paid = True
                    emi.save()
            else:
                for emi in remaining_emis:
                    emi.amount_due = new_emi
                    emi.save()
            return new_emi
        except Exception as e:
            data = {"error_message":str(e)}  
            return Response(data, status=status.HTTP_400_BAD_REQUEST) 

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['date', 'principal_paid', 'interest_paid', 'amount_paid']

class EMISerializer(serializers.ModelSerializer):
    class Meta:
        model = EMI
        fields = ['due_date', 'amount_due']

