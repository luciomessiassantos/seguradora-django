from decimal import Decimal
import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError

# Create your models here.

class CustomerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer_profile')
    cpf_cnpj = models.CharField(
        max_length=18,
        unique=True,
        blank=True,
        null=True,
        verbose_name='CPF/CNPJ'
    )

    def clean(self):
        
        if self.cpf_cnpj and not self.user.groups.filter(name='customer').exists():
            raise ValidationError({'cpf_cnpj': 'Apenas usuários do grupo "customer" podem ter CPF/CNPJ.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Perfil de {self.user.username}'

class BaseQuerySet(models.QuerySet):

    def get_actives(self):
        return self.filter(is_deleted=False)
    
    def get_deleted(self):
        return self.filter(is_deleted=True)
    
    

    
class BaseModelManager(models.Manager):

    def get_queryset(self) -> BaseQuerySet:
        return BaseQuerySet(model=self.model, using=self.db)
    
    def actives(self):
        return self.get_queryset().get_actives()
    
    def deleted(self):
        return self.get_queryset().get_deleted()


class BaseModel(models.Model):
    pkid = models.BigAutoField(primary_key=True, editable=False)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created'
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated'
    )
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_deleted'
    )

    objects = BaseModelManager()

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['is_deleted']),
        ]

    def soft_delete(self, user=None):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.save()

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save()





class Customer(BaseModel):

    STATUS_CHOICES = [('ACTIVE', 'Active'), ('INACTIVE', 'Inactive')]
    RISK_PROFILE_CHOICES = [('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High')]

    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    cpf_cnpj = models.CharField(max_length=18, unique=True)
    income = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    age = models.PositiveIntegerField()
    address = models.TextField()

    phone_number = models.CharField(max_length=15)
    email_address = models.EmailField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    risk_profile = models.CharField(max_length=10, choices=RISK_PROFILE_CHOICES, default='MEDIUM')


    def __str__(self):
        return f"{self.firstname} {self.lastname} - {self.cpf_cnpj}"

    class Meta:
        ordering = ['-created_at']


class Policy(BaseModel):

    STATUS_CHOICES = [('ACTIVE', 'Ativa'), ('INACTIVE', 'Inativa'), ('EXPIRED', 'Expirada')]
    DEDUCTIBLE_TYPE_CHOICES = [('FIXED', 'Fixa'), ('PERCENTAGE', 'Percentual')]
    PERIODICITY_CHOICES = [('MONTHLY', 'Mensal'), ('ANNUAL', 'Anual')]


    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='policies')
    code = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    expire_date = models.DateField()

    # Franquia
    deductible_type = models.CharField(max_length=10, choices=DEDUCTIBLE_TYPE_CHOICES, null=True, blank=True)
    fixed_deductible = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    percentage_deductible = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])

    coverage_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    property = models.CharField(max_length=120)
    property_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    # Mensalidade
    premium_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    periodicity = models.CharField(max_length=10, choices=PERIODICITY_CHOICES)

    def __str__(self):
        return f"Policy {self.code} - {self.customer}"

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['code']), models.Index(fields=['status', 'expire_date'])]

    def clean(self):
        if self.deductible_type == 'FIXED' and self.fixed_deductible is None:
            raise ValidationError('Fixed deductible value required when type is FIXED.')
        if self.deductible_type == 'PERCENTAGE' and self.percentage_deductible is None:
            raise ValidationError('Percentage deductible required when type is PERCENTAGE.')


class Claim(BaseModel):

    STATUS_CHOICES = [('OPEN', 'Open'), ('PAID', 'Paid'), ('CLOSED', 'Closed'), ('REJECTED', 'Rejected')]

    policy = models.ForeignKey(Policy, on_delete=models.PROTECT, related_name='claims')
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    loss_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    indemnity_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(0)])

    def __str__(self):
        return f"Claim #{self.uuid} - Policy {self.policy.code} - {self.status}"

    class Meta:
        ordering = ['-created_at']


class Payment(BaseModel):

    DIRECTION_CHOICES = [('RECEIVABLE', 'Receivable'), ('PAYABLE', 'Payable')]
    ORIGIN_CHOICES = [('PREMIUM', 'Premium'), ('CLAIM', 'Claim'), ('OTHER', 'Other')]
    STATUS_CHOICES = [('PENDING', 'Pending'), ('PAID', 'Paid'), ('OVERDUE', 'Overdue'), ('CANCELED', 'Canceled')]

    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)  # receber ou pagar
    origin = models.CharField(max_length=10, choices=ORIGIN_CHOICES)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(0)])
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')

    creditor_name = models.CharField(max_length=200, blank=True)  # usado só quando direction = PAYABLE

    @property
    def balance(self):
        return self.amount - self.paid_amount

    def __str__(self):
        return f"{self.direction} - {self.origin} - {self.amount}"

    class Meta:
        ordering = ['due_date']
        indexes = [models.Index(fields=['due_date']), models.Index(fields=['direction', 'status'])]
