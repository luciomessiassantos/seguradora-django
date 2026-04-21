from typing import Any

from django.http import HttpRequest
from django.http.response import HttpResponse as HttpResponse
from django.views.generic import TemplateView, ListView, UpdateView, DeleteView, DetailView, View
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin
from django.shortcuts import render, redirect
from django.db.models import Sum
from django.urls import reverse_lazy
from django.db.models import Q
from .models import *
from .forms import *

# Create your views here.

# Views de Login 

class LoginViewPage(LoginView):
    template_name = 'account/login.html'
    authentication_form = CustomAuthenticationForm
    redirect_authenticated_user = True
    success_url = reverse_lazy('redirect')

    def get_success_url(self):
        # Ignora qualquer parâmetro 'next' e vai direto para a view de transição
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

class CustomerPage(LoginRequiredMixin, TemplateView):
    template_name = 'customer/customer_dashboard.html'

# Views admin

class AdminDashboard(LoginRequiredMixin, TemplateView):
    template_name = 'admin/admin_dashboard.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs) 
        context['total_customers'] = Customer.objects.count()
        context['total_policies'] = Policy.objects.count()
        context['cover_total'] = Policy.objects.filter(status='ACTIVE').aggregate(Sum('coverage_amount'))['coverage_amount__sum']


        return context

# Views manager

class ManagerDashboard(LoginRequiredMixin, TemplateView):
    template_name = 'manager/manager_dashboard.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['total_customers'] = Customer.objects.count()
        context['total_policies'] = Policy.objects.count()
        context['total_claims'] = Claim.objects.count()
        return context

# Views finance

class FinanceDashboard(LoginRequiredMixin, TemplateView):
    template_name = 'finance/finance_dashboard.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context['total_income'] = Payment.objects.filter(direction='RECEIVABLE').filter(status='PAID').aggregate(Sum('paid_amount'))['paid_amount__sum']
        context['total_cover'] = Payment.objects.filter(direction='PAYABLE').filter(status='PAID').aggregate(Sum('paid_amount'))['paid_amount__sum']
        context['total_barred'] = Payment.objects.filter(status__in=['PENDING', 'OVERDUE']).aggregate(Sum('paid_amount'))['paid_amount__sum']

        return context
