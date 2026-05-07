from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy


class AdminAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (user.is_staff or user.is_superuser)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return redirect(reverse_lazy('hero'))
        return super().handle_no_permission()


class ManagerAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (
            user.is_superuser or user.is_staff or user.groups.filter(name='manager').exists()
        )

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return redirect(reverse_lazy('hero'))
        return super().handle_no_permission()


class FinanceAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (
            user.is_superuser or user.is_staff or user.groups.filter(name='finance').exists()
        )

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return redirect(reverse_lazy('hero'))
        return super().handle_no_permission()


class CustomerAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.groups.filter(name='customer').exists()

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return redirect(reverse_lazy('hero'))
        return super().handle_no_permission()
