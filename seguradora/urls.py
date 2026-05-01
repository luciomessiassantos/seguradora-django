from django.urls import path
from .views import *

urlpatterns = [
    path('', HeroPage.as_view(), name='hero'),
    path("redirect/", Redirect.as_view(), name="redirect"),
    path('login/', LoginViewPage.as_view(), name='login'),
    path('logout/', LogOutViewPage.as_view(), name='logout'),
    path('policy_search/', SearchPolicyAjaxView.as_view(), name='policy_search'),
    path('policy/<uuid:uuid>/', PolicyDetails.as_view(), name='policy_details'),
    path('secure/admin/dashboard/', AdminDashboard.as_view(), name='admin_dashboard'),
    path('customer/', CustomerPage.as_view(), name='customer_page'),
    path('manager/dashboard/', ManagerDashboard.as_view(), name='manager_dashboard'),
    path('manager/customer/register', CustomerCreateView.as_view(), name='customer_register'),
    path('manager/policy/create', PolicyCreateView.as_view(), name='policy_create'),
    path('manager/claim/create', ClaimCreateView.as_view(), name='clain_create'),
    path('finance/dashboard', FinanceDashboard.as_view(), name='finance_dashboard'),
    path('finance/payment/register', PaymentCreateView.as_view(), name='payment_register'),

    

]


# admin_page = reverse_lazy('admin_dashboard')
#     customer = reverse_lazy('customer_page')
#     manager = reverse_lazy('manager_dashboard')
#     finance = reverse_lazy('finance_dashboard')