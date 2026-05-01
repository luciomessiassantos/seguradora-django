# mixins.py
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy


class AdminAccessMixin(LoginRequiredMixin, UserPassesTestMixin):

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff # type: ignore

    def handle_no_permission(self):

        if self.request.user.is_authenticated: # type: ignore
            return redirect(reverse_lazy('hero'))
        return super().handle_no_permission()


class ManagerAccessMixin(LoginRequiredMixin, UserPassesTestMixin):

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.groups.filter(name='manager').exists() # type: ignore

    def handle_no_permission(self):
        if self.request.user.is_authenticated: # type: ignore
            return redirect(reverse_lazy('hero'))
        return super().handle_no_permission()


class FinanceAccessMixin(LoginRequiredMixin, UserPassesTestMixin):

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.groups.filter(name='finance').exists() # type: ignore

    def handle_no_permission(self):
        if self.request.user.is_authenticated: # type: ignore
            return redirect(reverse_lazy('hero'))
        return super().handle_no_permission()


class CustomerAccessMixin(LoginRequiredMixin, UserPassesTestMixin):

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.groups.filter(name='customer').exists() # type: ignore

    def handle_no_permission(self):
        if self.request.user.is_authenticated: # type: ignore
            return redirect(reverse_lazy('hero'))
        return super().handle_no_permission()