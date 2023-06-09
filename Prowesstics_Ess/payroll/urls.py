from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required


urlpatterns = [
    path('payroll_dashboard/', login_required(views.PayrollDashboard.as_view()), name='pay_dashboard'),
    path('payslip_hr/', login_required(views.PayslipHr.as_view()), name='pay_sliphr'),
    path('pay_slip_update/<int:pk>', login_required(views.PayslipUpdate.as_view()), name='pay_slip_update'),
    path('form16_update/', login_required(views.Form16.as_view()), name='form16_update'),
    path('pay_slip_gen/', login_required(views.PayslipGeneration.as_view()), name='pay_slip_gen'),
    path('pay_slip/', login_required(views.Payslip.as_view()), name='pay_slip'),
    path('form16/', login_required(views.ViewForm16.as_view()), name='form16'),
    path('hr_policy/', login_required(views.HrPolicy.as_view()), name='hr_policy'),
    path('allemployees/', login_required(views.AllEmployees.as_view()), name='allemployees'),
    path('download_payslip/<str:month>/<str:year>', login_required(views.DownloadPayslip.as_view()), name='download_payslip'),
    path('hrpolicy_pdf_view', views.hrpolicy_pdf_view, name='hrpolicy_pdf_view'),
]
