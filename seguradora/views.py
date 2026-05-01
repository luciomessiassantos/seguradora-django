from typing import Any
from django.http import HttpRequest
from django.http.response import HttpResponse as HttpResponse
from django.views.generic import TemplateView, ListView, UpdateView, DeleteView, DetailView, View, CreateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.db.models import Q, Sum
from .models import *
from .forms import *
from .mixins import *
# Create your views here.

# Views base para a criação das views de soft delete, restore, hard_delete e a lixeira de cada 
# Model
#

class BaseSoftDeleteView(LoginRequiredMixin, DeleteView):

    model = BaseModel

    def post(self, request, *args, **kwargs):
        obj = get_object_or_404(self.model, uuid=kwargs['uuid'])
        obj.soft_delete(user=request.user) 


        return redirect(self.success_url)

class BaseRestoreView(LoginRequiredMixin, View):

    model = BaseModel

    def post(self, request, *args, **kwargs):
        obj = get_object_or_404(self.model, uuid=kwargs['uuid'])
        obj.restore()

        return redirect(self.success_url)

class BaseHardDeleteView(LoginRequiredMixin, DeleteView):
    model = BaseModel

    def post(self, request, *args, **kwargs):
        obj = get_object_or_404(self.model, uuid=kwargs['uuid'])
        obj.delete() 
        return redirect(self.success_url)


class BaseTrashView(LoginRequiredMixin, ListView):
    template_name = 'trash_list.html'
    paginate_by = 20
    model = BaseModel

    def get_queryset(self):
        return self.model.objects.deleted()


# Views de Login 

class LoginViewPage(LoginView):
    template_name = 'account/login.html'
    authentication_form = CustomAuthenticationForm
    redirect_authenticated_user = True
    success_url = reverse_lazy('redirect')

    def get_success_url(self):
        
        return reverse_lazy('redirect')

class Redirect(LoginRequiredMixin, View):

    login_url = 'login'

    admin_page = reverse_lazy('admin_dashboard')
    customer = reverse_lazy('customer_page')
    manager = reverse_lazy('manager_dashboard')
    finance = reverse_lazy('finance_dashboard')

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        user_group = request.user.groups

        if request.user.is_staff:
            return redirect(self.admin_page)
        
        if user_group.filter(name='customer'):
            return redirect(self.customer)
        
        if user_group.filter(name='manager'):
            return redirect(self.manager)
        
        if user_group.filter(name='finance'):
            return redirect(self.finance)


        return super().dispatch(request, *args, **kwargs)


class LogOutViewPage(LogoutView):
    next_page = 'hero'


# Views do cliente customer_group

class HeroPage(TemplateView):
    template_name = 'customer/hero.html'

class SearchPolicyAjaxView(ListView):
    model = Policy
    template_name = 'customer/partials/search_results.html'  
    context_object_name = 'results'

    def get_queryset(self):
        qs = Policy.objects.select_related('customer').all()
        termo = self.request.GET.get('q', '').strip()
        
        if termo:
            qs = qs.filter(
                Q(customer__cpf_cnpj__icontains=termo) |
                Q(code__icontains=termo)
            )
        
        status = self.request.GET.get('status')
        if status == 'ativa':
            qs = qs.filter(status='ACTIVE')
        elif status == 'inativas':
            qs = qs.filter(status__in=['INACTIVE', 'EXPIRED'])
        
        ordenar = self.request.GET.get('ordenar', '-created_at')  
        if ordenar == 'mais_recente':
            qs = qs.order_by('-created_at')
        elif ordenar == 'menos_recente':
            qs = qs.order_by('created_at')
        else:
            qs = qs.order_by(ordenar)  
        return qs

    def render_to_response(self, context, **response_kwargs):
        context['total_results'] = len(context['results'])
        return render(self.request, self.template_name, context)

class CustomerPage(CustomerAccessMixin, TemplateView):
    template_name = 'customer/customer_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        customer_data = None
        
        if user.groups.filter(name='customer').exists() and hasattr(user, 'customer_profile'):
            cpf_cnpj = user.customer_profile.cpf_cnpj # type: ignore
            print(f"CPF/CNPJ do perfil: '{cpf_cnpj}'")
            if cpf_cnpj:
                try:
                    customer_data = Customer.objects.get(cpf_cnpj=cpf_cnpj)
                except Customer.DoesNotExist:
                    print("Not exist profile, for some reason")
                    customer_data = None

        context['customer'] = customer_data
        context['customer_policies'] = customer_data.policies.all() # type: ignore

        return context


# Views admin

class AdminDashboard(AdminAccessMixin, TemplateView):
    template_name = 'admin/admin_dashboard.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs) 
        context['total_customers'] = Customer.objects.count()
        context['total_policies'] = Policy.objects.count()
        context['cover_total'] = Policy.objects.filter(status='ACTIVE').aggregate(Sum('coverage_amount'))['coverage_amount__sum']


        return context

# Views manager

from django.core.paginator import Paginator
from django.views.generic import ListView
from .models import Customer, Policy, Claim
from .mixins import ManagerAccessMixin

class ManagerDashboard(ManagerAccessMixin, TemplateView):
    template_name = 'manager/manager_dashboard.html'

    # Não defina paginate_by aqui – faremos manualmente

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)


        context['total_customers'] = Customer.objects.count()
        context['total_policies'] = Policy.objects.count()
        context['total_claims'] = Claim.objects.count()


        customers_qs = Customer.objects.all()
        customers_paginator = Paginator(customers_qs, 10)  
        page_customers = self.request.GET.get('page_customers', 1)
        context['customers'] = customers_paginator.get_page(page_customers)


        policies_qs = Policy.objects.all()
        policies_paginator = Paginator(policies_qs, 10)
        page_policies = self.request.GET.get('page_policies', 1)
        context['policies'] = policies_paginator.get_page(page_policies)


        claims_qs = Claim.objects.all()
        claims_paginator = Paginator(claims_qs, 10)
        page_claims = self.request.GET.get('page_claims', 1)
        context['claims'] = claims_paginator.get_page(page_claims)

        return context
    
class PolicyCreateView(ManagerAccessMixin, CreateView):
    model = Policy
    form_class = PolicyForm
    template_name = 'manager/create_policy.html'
    success_url = reverse_lazy('manager_dashboard')

class CustomerCreateView(ManagerAccessMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'manager/register_customer.html'
    success_url = reverse_lazy('manager_dashboard')

class ClaimCreateView(ManagerAccessMixin, CreateView):
    model = Claim
    form_class = ClaimForm
    template_name = 'manager/create_claim.html'
    success_url = reverse_lazy('manager_dashboard')


# Views finance

class FinanceDashboard(FinanceAccessMixin, ListView):
    template_name = 'finance/finance_dashboard.html'
    model = Payment
    context_object_name = 'payments'
    paginate_by = 5

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context['total_income'] = Payment.objects.filter(direction='RECEIVABLE').filter(status='PAID').aggregate(Sum('paid_amount'))['paid_amount__sum']
        context['total_cover'] = Payment.objects.filter(direction='PAYABLE').filter(status='PAID').aggregate(Sum('paid_amount'))['paid_amount__sum']
        context['total_barred'] = Payment.objects.filter(status__in=['PENDING', 'OVERDUE']).aggregate(Sum('paid_amount'))['paid_amount__sum']

        
        return context

class PaymentCreateView(FinanceAccessMixin, CreateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'finance/register_payment.html'
    success_url = reverse_lazy('finance_dashboard')


# Details Views

class PolicyDetails(DetailView):
    template_name = 'details/policy_details.html'
    model = Policy
    slug_field = 'uuid'         
    slug_url_kwarg = 'uuid'
    context_object_name = 'policy'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        is_manager_or_staff = user.is_staff or user.groups.filter(name='manager').exists()
        context['is_manager_or_staff'] = is_manager_or_staff
        return context