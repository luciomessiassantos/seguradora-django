from django.urls import path
from .views import *

urlpatterns = [
    path('', HeroPage.as_view(), name='hero'),
    path("redirect/", Redirect.as_view(), name="redirect"),
    path('login/', LoginViewPage.as_view(), name='login'),
    path('logout/', LogOutViewPage.as_view(), name='logout'),
    path('policy_search/', SearchPolicyAjaxView.as_view(), name='policy_search'),
    
    path('secure/admin/dashboard/', AdminDashboard.as_view(), name='admin_dashboard'),
    path('customer/', CustomerPage.as_view(), name='customer_page'),
    path('manager/dashboard/', ManagerDashboard.as_view(), name='manager_dashboard'),
    path('finance/dashboard', FinanceDashboard.as_view(), name='finance_dashboard')

]


# admin_page = reverse_lazy('admin_dashboard')
#     customer = reverse_lazy('customer_page')
#     manager = reverse_lazy('manager_dashboard')
#     finance = reverse_lazy('finance_dashboard')