# usuarios/forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from .models import *

class CustomerUserCreationForm(UserCreationForm):
    cpf_cnpj = forms.CharField(max_length=18, required=False, label='CPF/CNPJ')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'cpf_cnpj')

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            
            if user.groups.filter(name='customers').exists():
                profile = user.customer_profile
                profile.cpf_cnpj = self.cleaned_data.get('cpf_cnpj')
                profile.save()
        return user

class CustomerUserChangeForm(UserChangeForm):
    cpf_cnpj = forms.CharField(max_length=18, required=False, label='CPF/CNPJ')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'cpf_cnpj')

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            if user.groups.filter(name='customers').exists():
                profile = user.customer_profile
                profile.cpf_cnpj = self.cleaned_data.get('cpf_cnpj')
                profile.save()
        return user



class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label='Nome de usuário',
        widget=forms.TextInput(attrs={
            'class': 'form-control input bg-background border-foreground text-black w-full', 
            'placeholder': 'Digite seu nome de usuário'
        })
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control input bg-background border-foreground text-black w-full', 
            'placeholder': 'Digite sua senha'
        })
    )

    def clean(self):
        
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        
        if username is not None and password is not None:
            
            from django.contrib.auth import authenticate
            self.user_cache = authenticate(self.request, username=username, password=password)
            
            if self.user_cache is None:
                raise ValidationError('Usuário ou senha inválidos.', code='invalid_login')
            else:
                self.confirm_login_allowed(self.user_cache)
        
        
        return self.cleaned_data


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'firstname', 'lastname', 'cpf_cnpj', 'income', 'age',
            'address', 'phone_number', 'email_address', 'status', 'risk_profile'
        ]
        widgets = {
            'firstname': forms.TextInput(attrs={
                'class': 'input input-bordered border-foreground text-sm w-9/10 bg-background text-black',
                'placeholder': 'Nome'
            }),
            'lastname': forms.TextInput(attrs={
                'class': 'input input-bordered border-foreground text-sm w-9/10 bg-background text-black',
                'placeholder': 'Sobrenome'
            }),
            'cpf_cnpj': forms.TextInput(attrs={
                'class': 'input input-bordered border-foreground text-sm w-9/10 bg-background text-black',
                'placeholder': 'CPF ou CNPJ (apenas números)'
            }),
            'income': forms.NumberInput(attrs={
                'class': 'input input-bordered border-foreground text-sm w-9/10 bg-background text-black',
                'placeholder': 'Renda mensal'
            }),
            'age': forms.NumberInput(attrs={
                'class': 'input input-bordered  border-foreground text-sm w-9/10 bg-background text-black',
                'placeholder': 'Idade'
            }),
            'address': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered  border-foreground text-sm w-9/10 bg-background text-black',
                'rows': 3,
                'placeholder': 'Endereço completo'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'input input-bordered  border-foreground text-sm w-9/10 bg-background text-black',
                'placeholder': '(XX) XXXXX-XXXX'
            }),
            'email_address': forms.EmailInput(attrs={
                'class': 'input input-bordered  border-foreground text-sm w-9/10 bg-background text-black',
                'placeholder': 'email@exemplo.com'
            }),
            'status': forms.Select(attrs={
                'class': 'select select-bordered  border-foreground text-sm w-9/10 bg-background text-black'
            }),
            'risk_profile': forms.Select(attrs={
                'class': 'select select-bordered  border-foreground text-sm w-9/10 bg-background text-black'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['firstname'].label = 'Nome'
        self.fields['lastname'].label = 'Sobrenome'
        self.fields['cpf_cnpj'].label = 'CPF/CNPJ'
        self.fields['income'].label = 'Renda mensal'
        self.fields['age'].label = 'Idade'
        self.fields['address'].label = 'Endereço'
        self.fields['phone_number'].label = 'Telefone'
        self.fields['email_address'].label = 'E-mail'
        self.fields['status'].label = 'Status'
        self.fields['risk_profile'].label = 'Perfil de risco'

    def clean_cpf_cnpj(self):
        value = self.cleaned_data['cpf_cnpj']
        cleaned = ''.join(filter(str.isdigit, value))
        if len(cleaned) not in (11, 14):
            raise forms.ValidationError('CPF deve ter 11 dígitos, CNPJ 14 dígitos.')
        return cleaned

    def clean_age(self):
        age = self.cleaned_data['age']
        if age < 18:
            raise forms.ValidationError('Cliente deve ter no mínimo 18 anos.')
        return age




class PolicyForm(forms.ModelForm):
    class Meta:
        model = Policy
        fields = [
            'customer', 'code', 'status', 'expire_date',
            'deductible_type', 'fixed_deductible', 'percentage_deductible',
            'coverage_amount', 'property', 'property_value',
            'premium_amount', 'periodicity'
        ]
        widgets = {
            'customer': forms.Select(attrs={
                'class': 'select select-bordered border-foreground w-full bg-background text-black'
            }),
            'code': forms.TextInput(attrs={
                'class': 'input input-bordered border-foreground w-full bg-background text-black',
                'placeholder': 'POL-000-2025'
            }),
            'status': forms.Select(attrs={
                'class': 'select select-bordered border-foreground w-full bg-background text-black'
            }),
            'expire_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'input input-bordered border-foreground w-full bg-background text-black'
            }),
            'deductible_type': forms.Select(attrs={
                'class': 'select select-bordered border-foreground w-full bg-background text-black'
            }),
            'fixed_deductible': forms.NumberInput(attrs={
                'class': 'input input-bordered border-foreground w-full bg-background text-black',
                'placeholder': 'Valor fixo da franquia'
            }),
            'percentage_deductible': forms.NumberInput(attrs={
                'class': 'input input-bordered border-foreground w-full bg-background text-black',
                'placeholder': 'Percentual (%)'
            }),
            'coverage_amount': forms.NumberInput(attrs={
                'class': 'input input-bordered border-foreground w-full bg-background text-black',
                'placeholder': 'Valor coberto'
            }),
            'property': forms.TextInput(attrs={
                'class': 'input input-bordered border-foreground w-full bg-background text-black',
                'placeholder': 'Ex: Casa, Carro, etc.'
            }),
            'property_value': forms.NumberInput(attrs={
                'class': 'input input-bordered border-foreground w-full bg-background text-black',
                'placeholder': 'Valor do bem'
            }),
            'premium_amount': forms.NumberInput(attrs={
                'class': 'input input-bordered border-foreground w-full bg-background text-black',
                'placeholder': 'Prêmio'
            }),
            'periodicity': forms.Select(attrs={
                'class': 'select select-bordered border-foreground w-full bg-background text-black'
            }),
        }

    # __init__ deve estar fora do Meta, com indentação correta
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].label = 'Cliente'
        self.fields['code'].label = 'Código da apólice'
        self.fields['status'].label = 'Status'
        self.fields['expire_date'].label = 'Data de vencimento'
        self.fields['deductible_type'].label = 'Tipo de franquia'
        self.fields['fixed_deductible'].label = 'Valor fixo da franquia'
        self.fields['percentage_deductible'].label = 'Percentual da franquia'
        self.fields['coverage_amount'].label = 'Valor coberto'
        self.fields['property'].label = 'Bem segurado'
        self.fields['property_value'].label = 'Valor do bem'
        self.fields['premium_amount'].label = 'Valor do prêmio'
        self.fields['periodicity'].label = 'Periodicidade'

    def clean(self):
        cleaned_data = super().clean()
        deductible_type = cleaned_data.get('deductible_type')
        fixed = cleaned_data.get('fixed_deductible')
        percent = cleaned_data.get('percentage_deductible')

        if deductible_type == 'FIXED' and not fixed:
            self.add_error('fixed_deductible', 'Franquia fixa requer um valor.')
        if deductible_type == 'PERCENTAGE' and not percent:
            self.add_error('percentage_deductible', 'Franquia percentual requer um valor.')
        return cleaned_data

class ClaimForm(forms.ModelForm):
    class Meta:
        model = Claim
        fields = ['policy', 'description', 'loss_amount', 'indemnity_amount', 'status']
        widgets = {
            'policy': forms.Select(attrs={
                'class': 'select select-bordered border-foreground w-full bg-background text-black'
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered border-foreground w-full bg-background text-black',
                'rows': 4,
                'placeholder': 'Descreva o sinistro...'
            }),
            'loss_amount': forms.NumberInput(attrs={
                'class': 'input input-bordered border-foreground w-full bg-background text-black',
                'placeholder': 'Valor do prejuízo'
            }),
            'indemnity_amount': forms.NumberInput(attrs={
                'class': 'input input-bordered border-foreground w-full bg-background text-black',
                'placeholder': 'Valor indenizado'
            }),
            'status': forms.Select(attrs={
                'class': 'select select-bordered border-foreground w-full bg-background text-black'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['policy'].label = 'Apólice'
        self.fields['description'].label = 'Descrição'
        self.fields['loss_amount'].label = 'Valor do prejuízo'
        self.fields['indemnity_amount'].label = 'Valor indenizado'
        self.fields['status'].label = 'Status'

    def clean_indemnity_amount(self):
        indemnity = self.cleaned_data.get('indemnity_amount')
        loss = self.cleaned_data.get('loss_amount')
        if indemnity and loss and indemnity > loss:
            raise forms.ValidationError('Indenização não pode exceder o valor do prejuízo.')
        return indemnity


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = [
            'direction', 'origin', 'description', 'amount',
            'paid_amount', 'due_date', 'paid_date', 'status', 'creditor_name'
        ]
        widgets = {
            'direction': forms.Select(attrs={
                'class': 'select select-bordered border-foreground w-full bg-background text-black'
            }),
            'origin': forms.Select(attrs={
                'class': 'select select-bordered border-foreground w-full bg-background text-black'
            }),
            'description': forms.TextInput(attrs={
                'class': 'input input-bordered border-foreground w-full bg-background text-black',
                'placeholder': 'Descrição do pagamento'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'input input-bordered border-foreground w-full bg-background text-black',
                'placeholder': 'Valor total'
            }),
            'paid_amount': forms.NumberInput(attrs={
                'class': 'input input-bordered border-foreground w-full bg-background text-black',
                'placeholder': 'Valor já pago'
            }),
            'due_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'input input-bordered border-foreground w-full bg-background text-black'
            }),
            'paid_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'input input-bordered border-foreground w-full bg-background text-black'
            }),
            'status': forms.Select(attrs={
                'class': 'select select-bordered border-foreground w-full bg-background text-black'
            }),
            'creditor_name': forms.TextInput(attrs={
                'class': 'input input-bordered border-foreground w-full bg-background text-black',
                'placeholder': 'Nome do credor (se aplicável)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['direction'].label = 'Direção (Receber/Pagar)'
        self.fields['origin'].label = 'Origem'
        self.fields['description'].label = 'Descrição'
        self.fields['amount'].label = 'Valor total'
        self.fields['paid_amount'].label = 'Valor pago'
        self.fields['due_date'].label = 'Data de vencimento'
        self.fields['paid_date'].label = 'Data de pagamento'
        self.fields['status'].label = 'Status'
        self.fields['creditor_name'].label = 'Credor'

    def clean(self):
        cleaned_data = super().clean()
        direction = cleaned_data.get('direction')
        creditor = cleaned_data.get('creditor_name')
        if direction == 'PAYABLE' and not creditor:
            self.add_error('creditor_name', 'Para pagamentos a pagar, informe o credor.')
        return cleaned_data
    

