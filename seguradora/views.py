from django.views.generic import TemplateView, ListView, UpdateView, DeleteView, DetailView
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render
from django.db.models import Q
from .models import *

# Create your views here.

# Views de Login 

# class LoginViewPage(LoginView):

# class LogOutViewPage(LogoutView):
    


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
