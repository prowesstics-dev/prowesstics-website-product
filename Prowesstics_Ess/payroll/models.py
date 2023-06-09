from django.db import models
from lms.models import User


# Create your models here.

class Payroll(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    ctc = models.FloatField(default=0)
    basic_salary = models.FloatField(default=0)
    hra_allowance = models.FloatField(default=0)
    spl_allowance = models.FloatField(default=0)
    total_earnings = models.FloatField(default=0)
    employee_provident_fund = models.FloatField(default=0)
    esi = models.FloatField(default=0)
    tds = models.FloatField(default=0)
    total_deduction = models.FloatField(default=0)
    net_amt = models.FloatField(default=0)
    sal_ctc_pm = models.FloatField(default=0)
    sal_ctc_pa = models.FloatField(default=0)
    gross_salary = models.FloatField(default=0)
    net_salary = models.FloatField(default=0)
    form_16 = models.FileField(upload_to='media/', null=True)
    created_at = models.DateTimeField(auto_created=True, null=True, blank=True)
    modified_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return self.employee.name


class PayrollDetailStatement(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    ctc = models.FloatField(default=0)
    basic_salary = models.FloatField(default=0)
    hra_allowance = models.FloatField(default=0)
    conv_allowance = models.FloatField(default=0)
    other_allowance = models.FloatField(default=0)
    bonus_arrear = models.FloatField(default=0)
    spl_allowance = models.FloatField(default=0)
    total_earnings = models.FloatField(default=0)
    provident_fund = models.FloatField(default=0)
    other_deduction = models.FloatField(default=0)
    income_tax = models.FloatField(default=0)
    pro_tax = models.FloatField(default=0)
    total_deduction = models.FloatField(default=0)
    net_amt = models.FloatField(default=0)
    sal_ctc_pm = models.FloatField(default=0)
    sal_ctc_pa = models.FloatField(default=0)
    gross_salary = models.FloatField(default=0)
    net_salary = models.FloatField(default=0)
    month = models.IntegerField()
    year = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.employee.name
