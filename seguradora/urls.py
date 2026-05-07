from django.urls import path

from .views import (
    AdminDashboard,
    ClaimCreateView,
    ClaimSoftDeleteView,
    ClaimUpdateView,
    CustomerCreateView,
    CustomerPage,
    CustomerSoftDeleteView,
    CustomerUpdateView,
    FinanceDashboard,
    HeroPage,
    LoginViewPage,
    LogOutViewPage,
    ManagerDashboard,
    PaymentCreateView,
    PaymentSoftDeleteView,
    PaymentUpdateView,
    PolicyCreateView,
    PolicyDetails,
    PolicySoftDeleteView,
    PolicyUpdateView,
    Redirect,
    SearchPolicyAjaxView,
)

urlpatterns = [
    path('', HeroPage.as_view(), name='hero'),
    path('redirect/', Redirect.as_view(), name='redirect'),
    path('login/', LoginViewPage.as_view(), name='login'),
    path('logout/', LogOutViewPage.as_view(), name='logout'),

    path('policy_search/', SearchPolicyAjaxView.as_view(), name='policy_search'),
    path('policy/<uuid:uuid>/', PolicyDetails.as_view(), name='policy_details'),

    path('secure/admin/dashboard/', AdminDashboard.as_view(), name='admin_dashboard'),
    path('customer/', CustomerPage.as_view(), name='customer_page'),
    path('manager/', ManagerDashboard.as_view(), name='manager_dashboard'),
    path('finance/', FinanceDashboard.as_view(), name='finance_dashboard'),

    path('manager/customer/register/', CustomerCreateView.as_view(), name='customer_register'),
    path('manager/policy/create/', PolicyCreateView.as_view(), name='policy_create'),
    path('manager/claim/create/', ClaimCreateView.as_view(), name='claim_create'),
    path('finance/payment/register/', PaymentCreateView.as_view(), name='payment_register'),

    path('manager/customer/edit/<uuid:uuid>/', CustomerUpdateView.as_view(), name='customer_edit'),
    path('manager/policy/edit/<uuid:uuid>/', PolicyUpdateView.as_view(), name='policy_edit'),
    path('manager/claim/edit/<uuid:uuid>/', ClaimUpdateView.as_view(), name='claim_edit'),
    path('finance/payment/edit/<uuid:uuid>/', PaymentUpdateView.as_view(), name='payment_edit'),

    path('manager/customer/delete/<uuid:uuid>/', CustomerSoftDeleteView.as_view(), name='customer_delete'),
    path('manager/policy/delete/<uuid:uuid>/', PolicySoftDeleteView.as_view(), name='policy_delete'),
    path('manager/claim/delete/<uuid:uuid>/', ClaimSoftDeleteView.as_view(), name='claim_delete'),
    path('finance/payment/delete/<uuid:uuid>/', PaymentSoftDeleteView.as_view(), name='payment_delete'),
]
