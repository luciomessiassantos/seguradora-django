from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Customer)
admin.site.register(Policy)
admin.site.register(Claim)
admin.site.register(Payment)
admin.site.register(CustomerProfile)