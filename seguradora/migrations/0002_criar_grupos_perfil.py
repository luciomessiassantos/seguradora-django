from django.db import migrations
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

def criar_grupos(apps, schema_editor):

    Customer = apps.get_model('seguradora', 'Customer')
    Policy = apps.get_model('seguradora', 'Policy')
    Claim = apps.get_model('seguradora', 'Claim')
    Payment = apps.get_model('seguradora', 'Payment')


    customer_group, _ = Group.objects.get_or_create(name='customer')
    manager_group, _ = Group.objects.get_or_create(name='manager')
    finance_group, _ = Group.objects.get_or_create(name='finance')


    perms_customer = Permission.objects.filter(
        content_type__in=[
            ContentType.objects.get_for_model(Customer),
            ContentType.objects.get_for_model(Policy),
            ContentType.objects.get_for_model(Claim),
        ],
        codename__in=['view_customer', 'view_policy', 'view_claim']
    )
    customer_group.permissions.add(*perms_customer)


    perms_manager = Permission.objects.filter(
        content_type__in=[
            ContentType.objects.get_for_model(Policy),
            ContentType.objects.get_for_model(Claim),
            ContentType.objects.get_for_model(Customer),
            ContentType.objects.get_for_model(Payment),
        ],
        codename__in=[
            'add_policy', 'change_policy', 'delete_policy', 'view_policy',
            'add_claim', 'change_claim', 'delete_claim', 'view_claim',
            'view_customer',
            'view_payment',
        ]
    )
    manager_group.permissions.add(*perms_manager)


    perms_finance = Permission.objects.filter(
        content_type__in=[
            ContentType.objects.get_for_model(Payment),
            ContentType.objects.get_for_model(Policy),
            ContentType.objects.get_for_model(Claim),
            ContentType.objects.get_for_model(Customer),
        ],
        codename__in=[
            'add_payment', 'change_payment', 'delete_payment', 'view_payment',
            'view_policy', 'view_claim', 'view_customer'
        ]
    )
    finance_group.permissions.add(*perms_finance)

def remover_grupos(apps, schema_editor):
    Group.objects.filter(name__in=['customer', 'manager', 'finance']).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('seguradora', '0001_initial'),  
    ]

    operations = [
        migrations.RunPython(criar_grupos, remover_grupos),
    ]