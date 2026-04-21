# usuarios/forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from .models import CustomerProfile


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

    # def clean(self):

    #     username = self.cleaned_data.get('username')
    #     password = self.cleaned_data.get('password')
        
    #     if not username or not password:
    #         raise forms.ValidationError('Por favor, preencha ambos os campos.')
        
    #     user = authenticate(self.request, username=username, password=password)
    #     if user is None:
    #         raise forms.ValidationError('Usuário ou senha inválidos. Tente novamente.')
        
    #     if not user.is_active:
    #         raise forms.ValidationError('Sua conta está desativada. Contate o suporte.')
        
    #     self.user = user
    #     return self.cleaned_data

    def clean(self):
        # 1. Obtém os dados limpos (username, password)
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        # 2. Se algum campo estiver vazio, não prossegue (validação padrão)
        if username is not None and password is not None:
            # 3. Tenta autenticar
            from django.contrib.auth import authenticate
            self.user_cache = authenticate(self.request, username=username, password=password)
            
            if self.user_cache is None:
                raise ValidationError('Usuário ou senha inválidos.', code='invalid_login')
            else:
                self.confirm_login_allowed(self.user_cache)
        
        # 4. Retorna os dados limpos (importante)
        return self.cleaned_data

        