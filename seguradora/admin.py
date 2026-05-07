from django.contrib import admin

from .models import Claim, Customer, CustomerProfile, Payment, Policy


class SoftDeleteModelAdmin(admin.ModelAdmin):
    readonly_fields = ('uuid', 'created_at', 'created_by', 'updated_at', 'updated_by', 'deleted_at', 'deleted_by')
    list_filter = ('is_deleted',)
    actions = ('soft_delete_selected', 'restore_selected')

    def get_queryset(self, request):
        # No admin do Django o administrador precisa enxergar ativos e deletados
        # para poder restaurar registros enviados para a lixeira lógica.
        return self.model.objects.all()

    def save_model(self, request, obj, form, change):
        previous = None

        if change and obj.pk:
            previous = self.model.objects.filter(pk=obj.pk).first()

        if not change and hasattr(obj, 'created_by') and obj.created_by is None:
            obj.created_by = request.user

        if hasattr(obj, 'updated_by'):
            obj.updated_by = request.user

        # Quando o admin marca is_deleted manualmente no formulário,
        # o Django chama save_model(), não delete_model().
        # Por isso precisamos preencher deleted_at/deleted_by aqui também.
        if hasattr(obj, 'is_deleted') and hasattr(obj, 'deleted_at') and hasattr(obj, 'deleted_by'):
            was_deleted = bool(previous and previous.is_deleted)

            if obj.is_deleted and not was_deleted:
                if obj.deleted_at is None:
                    from django.utils import timezone
                    obj.deleted_at = timezone.now()
                if request.user.is_authenticated:
                    obj.deleted_by = request.user

            elif obj.is_deleted and was_deleted:
                # Preserva auditoria antiga, mas corrige registros que já estavam
                # marcados como deletados sem deleted_at/deleted_by.
                if obj.deleted_at is None:
                    from django.utils import timezone
                    obj.deleted_at = timezone.now()
                if obj.deleted_by is None and request.user.is_authenticated:
                    obj.deleted_by = request.user

            elif not obj.is_deleted and was_deleted:
                # Desmarcar is_deleted pelo formulário equivale a restaurar.
                obj.deleted_at = None
                obj.deleted_by = None

        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        self._soft_delete_with_relations(obj, request.user)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            self._soft_delete_with_relations(obj, request.user)

    @admin.action(description='Enviar selecionados para a lixeira lógica')
    def soft_delete_selected(self, request, queryset):
        for obj in queryset:
            self._soft_delete_with_relations(obj, request.user)

    @admin.action(description='Restaurar selecionados')
    def restore_selected(self, request, queryset):
        for obj in queryset:
            obj.restore(user=request.user)

    def _soft_delete_with_relations(self, obj, user):
        if isinstance(obj, Customer):
            for policy in obj.policies.filter(is_deleted=False):
                for claim in policy.claims.filter(is_deleted=False):
                    claim.soft_delete(user=user)
                policy.soft_delete(user=user)
            obj.soft_delete(user=user)
        elif isinstance(obj, Policy):
            for claim in obj.claims.filter(is_deleted=False):
                claim.soft_delete(user=user)
            obj.soft_delete(user=user)
        else:
            obj.soft_delete(user=user)


@admin.register(Customer)
class CustomerAdmin(SoftDeleteModelAdmin):
    list_display = ('firstname', 'lastname', 'cpf_cnpj', 'status', 'risk_profile', 'is_deleted', 'deleted_at', 'deleted_by')
    search_fields = ('firstname', 'lastname', 'cpf_cnpj', 'email_address')
    list_filter = SoftDeleteModelAdmin.list_filter + ('status', 'risk_profile')


@admin.register(Policy)
class PolicyAdmin(SoftDeleteModelAdmin):
    list_display = ('code', 'customer', 'status', 'expire_date', 'premium_amount', 'is_deleted', 'deleted_at', 'deleted_by')
    search_fields = ('code', 'customer__firstname', 'customer__lastname', 'customer__cpf_cnpj')
    list_filter = SoftDeleteModelAdmin.list_filter + ('status', 'periodicity')
    autocomplete_fields = ()


@admin.register(Claim)
class ClaimAdmin(SoftDeleteModelAdmin):
    list_display = ('uuid', 'policy', 'status', 'loss_amount', 'indemnity_amount', 'is_deleted', 'deleted_at', 'deleted_by')
    search_fields = ('policy__code', 'description')
    list_filter = SoftDeleteModelAdmin.list_filter + ('status',)


@admin.register(Payment)
class PaymentAdmin(SoftDeleteModelAdmin):
    list_display = ('description', 'direction', 'origin', 'status', 'amount', 'paid_amount', 'due_date', 'is_deleted', 'deleted_at', 'deleted_by')
    search_fields = ('description', 'creditor_name')
    list_filter = SoftDeleteModelAdmin.list_filter + ('direction', 'origin', 'status')


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'cpf_cnpj')
    search_fields = ('user__username', 'cpf_cnpj')
