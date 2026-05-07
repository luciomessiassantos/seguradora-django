from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView, View

from .forms import ClaimForm, CustomerForm, CustomAuthenticationForm, PaymentForm, PolicyForm
from .mixins import AdminAccessMixin, CustomerAccessMixin, FinanceAccessMixin, ManagerAccessMixin
from .models import BaseModel, Claim, Customer, Payment, Policy


class BaseSoftDeleteView(LoginRequiredMixin, DeleteView):
    model = BaseModel
    success_url = reverse_lazy('redirect')

    def get_queryset(self):
        return self.model.objects.actives()

    def post(self, request, *args, **kwargs):
        obj = get_object_or_404(self.get_queryset(), uuid=kwargs['uuid'])
        self.perform_soft_delete(obj, request.user)
        return redirect(self.get_success_url())

    def perform_soft_delete(self, obj, user):
        obj.soft_delete(user=user)


class BaseRestoreView(LoginRequiredMixin, View):
    model = BaseModel
    success_url = reverse_lazy('redirect')

    def post(self, request, *args, **kwargs):
        obj = get_object_or_404(self.model.objects.deleted(), uuid=kwargs['uuid'])
        obj.restore()
        return redirect(self.success_url)


class BaseHardDeleteView(LoginRequiredMixin, DeleteView):
    model = BaseModel
    success_url = reverse_lazy('redirect')

    def post(self, request, *args, **kwargs):
        obj = get_object_or_404(self.model.objects.all(), uuid=kwargs['uuid'])
        obj.delete()
        return redirect(self.get_success_url())


class BaseTrashView(LoginRequiredMixin, ListView):
    template_name = 'trash_list.html'
    paginate_by = 20
    model = BaseModel

    def get_queryset(self):
        return self.model.objects.deleted()


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
        user = request.user

        if user.is_superuser:
            return redirect(self.admin_page)
        if user.groups.filter(name='manager').exists():
            return redirect(self.manager)
        if user.groups.filter(name='finance').exists():
            return redirect(self.finance)
        if user.groups.filter(name='customer').exists():
            return redirect(self.customer)
        if user.is_staff:
            return redirect(self.admin_page)
        return redirect(self.login_url)


class LogOutViewPage(LogoutView):
    next_page = 'hero'


class HeroPage(TemplateView):
    template_name = 'customer/hero.html'


class SearchPolicyAjaxView(ListView):
    model = Policy
    template_name = 'customer/partials/search_results.html'
    context_object_name = 'results'

    ORDERING_MAP = {
        'mais_recente': '-created_at',
        'menos_recente': 'created_at',
        'codigo': 'code',
        '-codigo': '-code',
        'status': 'status',
        '-status': '-status',
    }

    def get_queryset(self):
        qs = Policy.objects.actives().select_related('customer')
        termo = self.request.GET.get('q', '').strip()

        if termo:
            qs = qs.filter(Q(customer__cpf_cnpj__icontains=termo) | Q(code__icontains=termo))

        status = self.request.GET.get('status')
        if status == 'ativa':
            qs = qs.filter(status='ACTIVE')
        elif status == 'inativas':
            qs = qs.filter(status__in=['INACTIVE', 'EXPIRED'])

        ordenar = self.request.GET.get('ordenar', 'mais_recente')
        return qs.order_by(self.ORDERING_MAP.get(ordenar, '-created_at'))

    def render_to_response(self, context, **response_kwargs):
        context['total_results'] = context['results'].count()
        return render(self.request, self.template_name, context)


class CustomerPage(CustomerAccessMixin, TemplateView):
    template_name = 'customer/customer_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        customer_data = None
        context['customer_not_found'] = False

        profile = getattr(user, 'customer_profile', None)
        if profile and profile.cpf_cnpj:
            customer_data = Customer.objects.actives().filter(cpf_cnpj=profile.cpf_cnpj).first()

        context['customer'] = customer_data
        context['customer_policies'] = customer_data.policies.filter(is_deleted=False) if customer_data else Policy.objects.none()
        if not customer_data:
            context['customer_not_found'] = True
        return context


class AdminDashboard(AdminAccessMixin, TemplateView):
    template_name = 'admin/admin_dashboard.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        active_customers = Customer.objects.actives()
        active_policies = Policy.objects.actives().select_related('customer')
        active_claims = Claim.objects.actives().select_related('policy', 'policy__customer')
        active_payments = Payment.objects.actives()

        context['total_customers'] = active_customers.count()
        context['total_policies'] = active_policies.count()
        context['total_claims'] = active_claims.count()
        context['total_payments'] = active_payments.count()
        context['cover_total'] = active_policies.filter(status='ACTIVE').aggregate(total=Sum('coverage_amount'))['total'] or 0

        context['customers'] = Paginator(active_customers, 10).get_page(self.request.GET.get('page_customers', 1))
        context['policies'] = Paginator(active_policies, 10).get_page(self.request.GET.get('page_policies', 1))
        context['claims'] = Paginator(active_claims, 10).get_page(self.request.GET.get('page_claims', 1))
        context['payments'] = Paginator(active_payments, 10).get_page(self.request.GET.get('page_payments', 1))
        return context


class ManagerDashboard(ManagerAccessMixin, TemplateView):
    template_name = 'manager/manager_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active_customers = Customer.objects.actives()
        active_policies = Policy.objects.actives().select_related('customer')
        active_claims = Claim.objects.actives().select_related('policy', 'policy__customer')

        context['total_customers'] = active_customers.count()
        context['total_policies'] = active_policies.count()
        context['total_claims'] = active_claims.count()
        context['customers'] = Paginator(active_customers, 10).get_page(self.request.GET.get('page_customers', 1))
        context['policies'] = Paginator(active_policies, 10).get_page(self.request.GET.get('page_policies', 1))
        context['claims'] = Paginator(active_claims, 10).get_page(self.request.GET.get('page_claims', 1))
        return context



class RoleAwareSuccessUrlMixin:
    admin_success_url = reverse_lazy('admin_dashboard')

    def get_success_url(self):
        user = self.request.user
        if user.is_authenticated and (user.is_superuser or user.is_staff):
            return self.admin_success_url
        return super().get_success_url()


class RoleAwareCancelUrlMixin(RoleAwareSuccessUrlMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = self.get_success_url()
        return context

class AuditCreateMixin:
    def form_valid(self, form):
        if hasattr(form.instance, 'created_by') and not form.instance.created_by:
            form.instance.created_by = self.request.user
        if hasattr(form.instance, 'updated_by'):
            form.instance.updated_by = self.request.user
        return super().form_valid(form)


class AuditUpdateMixin:
    def form_valid(self, form):
        if hasattr(form.instance, 'updated_by'):
            form.instance.updated_by = self.request.user
        return super().form_valid(form)


class PolicyCreateView(RoleAwareCancelUrlMixin, AuditCreateMixin, ManagerAccessMixin, CreateView):
    model = Policy
    form_class = PolicyForm
    template_name = 'manager/create_policy.html'
    success_url = reverse_lazy('manager_dashboard')


class CustomerCreateView(RoleAwareCancelUrlMixin, AuditCreateMixin, ManagerAccessMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'manager/register_customer.html'
    success_url = reverse_lazy('manager_dashboard')


class ClaimCreateView(RoleAwareCancelUrlMixin, AuditCreateMixin, ManagerAccessMixin, CreateView):
    model = Claim
    form_class = ClaimForm
    template_name = 'manager/create_claim.html'
    success_url = reverse_lazy('manager_dashboard')


class FinanceDashboard(FinanceAccessMixin, ListView):
    template_name = 'finance/finance_dashboard.html'
    model = Payment
    context_object_name = 'payments'
    paginate_by = 5

    def get_queryset(self):
        return Payment.objects.actives()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        active_payments = Payment.objects.actives()
        context['total_income'] = active_payments.filter(direction='RECEIVABLE', status='PAID').aggregate(total=Sum('paid_amount'))['total'] or 0
        context['total_cover'] = active_payments.filter(direction='PAYABLE', status='PAID').aggregate(total=Sum('paid_amount'))['total'] or 0
        context['total_barred'] = active_payments.filter(status__in=['PENDING', 'OVERDUE']).aggregate(total=Sum('amount'))['total'] or 0
        return context


class PaymentCreateView(RoleAwareCancelUrlMixin, AuditCreateMixin, FinanceAccessMixin, CreateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'finance/register_payment.html'
    success_url = reverse_lazy('finance_dashboard')


class PolicyDetails(DetailView):
    template_name = 'details/policy_details.html'
    model = Policy
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'
    context_object_name = 'policy'

    def get_queryset(self):
        return Policy.objects.actives().select_related('customer')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['is_manager_or_staff'] = user.is_authenticated and (
            user.is_staff or user.is_superuser or user.groups.filter(name='manager').exists()
        )
        return context


class CustomerUpdateView(RoleAwareCancelUrlMixin, AuditUpdateMixin, ManagerAccessMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'manager/register_customer.html'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'
    success_url = reverse_lazy('manager_dashboard')

    def get_queryset(self):
        return Customer.objects.actives()


class PolicyUpdateView(RoleAwareCancelUrlMixin, AuditUpdateMixin, ManagerAccessMixin, UpdateView):
    model = Policy
    form_class = PolicyForm
    template_name = 'manager/create_policy.html'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'
    success_url = reverse_lazy('manager_dashboard')

    def get_queryset(self):
        return Policy.objects.actives()


class ClaimUpdateView(RoleAwareCancelUrlMixin, AuditUpdateMixin, ManagerAccessMixin, UpdateView):
    model = Claim
    form_class = ClaimForm
    template_name = 'manager/create_claim.html'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'
    success_url = reverse_lazy('manager_dashboard')

    def get_queryset(self):
        return Claim.objects.actives()


class PaymentUpdateView(RoleAwareCancelUrlMixin, AuditUpdateMixin, FinanceAccessMixin, UpdateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'finance/register_payment.html'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'
    success_url = reverse_lazy('finance_dashboard')

    def get_queryset(self):
        return Payment.objects.actives()


class CustomerSoftDeleteView(RoleAwareSuccessUrlMixin, ManagerAccessMixin, BaseSoftDeleteView):
    model = Customer
    success_url = reverse_lazy('manager_dashboard')

    def perform_soft_delete(self, obj, user):
        for policy in obj.policies.filter(is_deleted=False):
            for claim in policy.claims.filter(is_deleted=False):
                claim.soft_delete(user=user)
            policy.soft_delete(user=user)
        obj.soft_delete(user=user)


class PolicySoftDeleteView(RoleAwareSuccessUrlMixin, ManagerAccessMixin, BaseSoftDeleteView):
    model = Policy
    success_url = reverse_lazy('manager_dashboard')

    def perform_soft_delete(self, obj, user):
        for claim in obj.claims.filter(is_deleted=False):
            claim.soft_delete(user=user)
        obj.soft_delete(user=user)


class ClaimSoftDeleteView(RoleAwareSuccessUrlMixin, ManagerAccessMixin, BaseSoftDeleteView):
    model = Claim
    success_url = reverse_lazy('manager_dashboard')


class PaymentSoftDeleteView(RoleAwareSuccessUrlMixin, FinanceAccessMixin, BaseSoftDeleteView):
    model = Payment
    success_url = reverse_lazy('finance_dashboard')
