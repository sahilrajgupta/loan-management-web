from django.urls import include, path
from loanapp.views import LoanView, LoanStatementView, MakePaymentView, UserRegistrationView

urlpatterns = [
    path('register-user/',UserRegistrationView.as_view(), name='-user-registration-view'),
    path('apply-loan', LoanView.as_view(), name='apply-loan'),
    path('make-payment', MakePaymentView.as_view(), name='make-payment'),
    path('get-statement/<uuid:loan_id>/',LoanStatementView.as_view(), name='get-statement')
]
