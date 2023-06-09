from django.contrib import admin
from .models import Payroll, PayrollDetailStatement

# Register your models here.
admin.site.register(Payroll)
admin.site.register(PayrollDetailStatement)
