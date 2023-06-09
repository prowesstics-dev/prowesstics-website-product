import datetime

from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponse, Http404
from django.shortcuts import render
import os
# from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.views import View
from weasyprint import HTML, CSS
from django.contrib.auth.decorators import login_required
from PyPDF2 import PdfFileWriter, PdfFileReader
from lms.models import User
from .models import *
import sweetify


# Create your views here.
class PayrollDashboard(View):
    def get(self, request):
        user = []
        if Payroll.objects.filter(employee_id=request.user.id).exists():
            get_emp_payroll = Payroll.objects.get(employee_id=request.user.id)
            user.append(dict(name=request.user.name, doj=request.user.doj, designation=request.user.designation,
                             ctc=get_emp_payroll.ctc,
                             last_appraisal='-'))
        else:
            user.append(
                dict(name=request.user.name, doj=request.user.doj, designation=request.user.designation, ctc='-',
                     last_appraisal='-'))
        return render(request, 'payroll/employee.html', context=dict(user=user))


class PayslipHr(View):
    def get(self, request):
        if request.user.role == 'HR':
            get_user = User.objects.filter(admin=False).all()
            user = []
            for usr in get_user:
                if Payroll.objects.filter(employee_id=usr.id).exists():
                    get_emp_payroll = Payroll.objects.get(employee_id=usr.id)
                    user.append(dict(email=usr.email, id=usr.id, designation=usr.designation, ctc=get_emp_payroll.ctc,emp=usr.employee_id))
                else:
                    user.append(dict(email=usr.email, id=usr.id, designation=usr.designation, ctc='-',emp=usr.employee_id))
            paginator = Paginator(user, 50)
            page = request.GET.get('page')
            try:
                pages = paginator.page(page)
                print(f'h1{pages}')
            except PageNotAnInteger:
                pages = paginator.page(1)
                print(f'h2{pages}')
            except EmptyPage:
                pages = paginator.page(paginator.num_pages)
                print(f'h3{pages}')
            return render(request, 'payroll/payslipsupdate.html', context=dict(user=pages))
        else:
            raise Http404


class PayslipUpdate(View):
    def get(self, request, pk):
        if request.user.role == 'HR':
            get_user = User.objects.get(id=pk)
            print(get_user)
            if Payroll.objects.filter(employee_id=get_user.id).exists():
                context = dict(name=get_user.name, id=get_user.id,
                               payroll=Payroll.objects.filter(employee_id=get_user.id))
                return render(request, 'payroll/payslipsupdate1.html', context=context)
            else:
                context = dict(name=get_user.name, id=get_user.id)
                return render(request, 'payroll/payslipsupdate1.html', context=context)
        else:
            raise Http404

    def post(self, request, pk):
        if request.user.role == 'HR':
            ctc = request.POST.get('ctc')
            if ctc == None or ctc == '0':
                sweetify.error(request, 'Error', text=f'Ctc required', persistent='Ok')
                return redirect('pay_sliphr')
            emp_id = request.POST.get('emp_id')
            base_salary = request.POST.get('base_salary')
            hra_allowance = request.POST.get('hra_allowance')
            spl_allowance = request.POST.get('spl_allowance')
            total_earnings = request.POST.get('total_earnings')
            epf = request.POST.get('employee_provident_fund')
            esi = request.POST.get('esi')
            tds = request.POST.get('tds')
            total_deduction = request.POST.get('total_deduction')
            sal_pm = request.POST.get('sal_ctc_pm')
            gross_salary = request.POST.get('gross_salary')
            net_salary = request.POST.get('net_salary')
            print(sal_pm)
            if not Payroll.objects.filter(employee_id=emp_id).exists():
                create_payroll = Payroll.objects.create(employee_id=emp_id, ctc=ctc, basic_salary=base_salary,
                                                        hra_allowance=hra_allowance,
                                                        spl_allowance=spl_allowance, total_earnings=total_earnings,
                                                        total_deduction=total_deduction,employee_provident_fund=epf,
                                                        esi=esi,tds=tds,
                                                        sal_ctc_pm=sal_pm, sal_ctc_pa=round(int(sal_pm) * 12),
                                                        gross_salary=gross_salary,
                                                        net_salary=net_salary)
            else:
                Payroll.objects.filter(employee_id=emp_id).update(ctc=ctc, basic_salary=base_salary,
                                                                  hra_allowance=hra_allowance,employee_provident_fund=epf,
                                                                  esi=esi,tds=tds,
                                                                  spl_allowance=spl_allowance,
                                                                  total_earnings=total_earnings,
                                                                  total_deduction=total_deduction,
                                                                  sal_ctc_pm=sal_pm, sal_ctc_pa=round(float(sal_pm) * 12),
                                                                  gross_salary=gross_salary,
                                                                  net_salary=net_salary)
            return redirect('pay_sliphr')
        else:
            raise Http404


class Form16(View):
    def get(self, request):
        if request.user.role == 'HR':
            get_user = User.objects.all()

            user = []
            for usr in get_user:
                if Payroll.objects.filter(employee_id=usr.id).exists():
                    get_emp_payroll = Payroll.objects.get(employee_id=usr.id)
                    user.append(dict(email=usr.email, id=usr.id, designation=usr.designation, ctc=get_emp_payroll.ctc,emp=usr.employee_id))
                else:
                    user.append(dict(email=usr.email, id=usr.id, designation=usr.designation, ctc='-',emp=usr.employee_id))
            print(user )
            paginator = Paginator(user, 50)
            page = request.GET.get('page')
            try:
                pages = paginator.page(page)
                print(f'h1{pages}')
            except PageNotAnInteger:
                pages = paginator.page(1)
                print(f'h2{pages}')
            except EmptyPage:
                pages = paginator.page(paginator.num_pages)
                print(f'h3{pages}')

            return render(request, 'payroll/form16_update.html', context=dict(user=pages))
        else:
            raise Http404

    def post(self, request):
        if request.user.role == 'HR':
            year = request.POST.get('year')
            if year != "":
                print(request.FILES)
                form = request.FILES.get('form16')
                emp_id = request.user.id
                fss = FileSystemStorage()
                name = f"form16_{emp_id}_{year}"
                try:
                    if fss.get_available_name(name=name):
                        os.remove(os.path.join('media', f"{name}.pdf"))
                        file = fss.save(f"{name}.pdf", form)
                except:
                    file = fss.save(f"{name}.pdf", form)
                # file_url = fss.url(file)
                # update_form = Payroll.objects.filter(employee_id=emp_id).update(form_16=form)
                return redirect('form16_update')
            else:
                sweetify.error(request, 'Error', text=f'Please enter year', persistent='Ok')
                return redirect('form16_update')
        else:
            raise Http404


class PayslipGeneration(View):
    def get(self, request):
        if request.user.role == 'HR':
            get_user = User.objects.all()
            user = []
            for usr in get_user:
                if Payroll.objects.filter(employee_id=usr.id).exists():
                    get_emp_payroll = Payroll.objects.get(employee_id=usr.id)
                    user.append(dict(email=usr.email, id=usr.id, designation=usr.designation, ctc=get_emp_payroll.ctc,emp=usr.employee_id))
                else:
                    user.append(dict(email=usr.email, id=usr.id, designation=usr.designation, ctc='-',emp=usr.employee_id))
            paginator = Paginator(user, 50)
            page = request.GET.get('page')
            try:
                pages = paginator.page(page)
                print(f'h1{pages}')
            except PageNotAnInteger:
                pages = paginator.page(1)
                print(f'h2{pages}')
            except EmptyPage:
                pages = paginator.page(paginator.num_pages)
                print(f'h3{pages}')
            return render(request, 'payroll/pay_slip_gen.html', context=dict(user=pages))
        else:
            raise Http404

    def post(self, request):
        if request.user.role == 'HR':
            year = request.POST.get('year')
            month = request.POST.get('month')
            emp_id = request.POST.get('emp_id')
            if Payroll.objects.filter(employee_id=int(emp_id)).exists():
                get_emp_payroll = Payroll.objects.get(employee_id=int(emp_id))
                if not PayrollDetailStatement.objects.filter(employee_id=int(emp_id), month=int(month),
                                                             year=int(year)).exists():
                    PayrollDetailStatement.objects.create(employee_id=emp_id, ctc=get_emp_payroll.ctc,
                                                          basic_salary=get_emp_payroll.basic_salary,
                                                          hra_allowance=get_emp_payroll.hra_allowance,
                                                          conv_allowance=get_emp_payroll.conv_allowance,
                                                          other_allowance=get_emp_payroll.other_allowance,
                                                          bonus_arrear=get_emp_payroll.bonus_arrear,
                                                          spl_allowance=get_emp_payroll.spl_allowance,
                                                          total_earnings=get_emp_payroll.total_earnings,
                                                          provident_fund=get_emp_payroll.provident_fund,
                                                          other_deduction=get_emp_payroll.other_deduction,
                                                          income_tax=get_emp_payroll.income_tax,
                                                          pro_tax=get_emp_payroll.pro_tax,
                                                          total_deduction=get_emp_payroll.total_deduction,
                                                          net_amt=get_emp_payroll.net_amt,
                                                          sal_ctc_pm=get_emp_payroll.sal_ctc_pm,
                                                          sal_ctc_pa=get_emp_payroll.sal_ctc_pa,
                                                          gross_salary=get_emp_payroll.gross_salary,
                                                          net_salary=get_emp_payroll.net_salary, month=int(month),
                                                          year=int(year))
                    sweetify.success(request, 'Success', text=f'Payroll  generated successfully', persistent='Ok')
                else:
                    sweetify.error(request, 'Error', text=f'Payroll alreay generated for {month}-{year}',
                                   persistent='Ok')

                return redirect('pay_slip_gen')
            else:
                sweetify.error(request, 'Error', text=f'Update PaySlip to generate payroll', persistent='Ok')
                return redirect('pay_slip_gen')
        else:
            raise Http404


class Payslip(View):
    def get(self, request):
        month = request.GET.get('month')
        year = request.GET.get('year')
        d = datetime.datetime.now()
        current_month = int(d.strftime("%#m"))
        previous_month = current_month - 1
        if not PayrollDetailStatement.objects.filter(employee_id=request.user.id).exists():
            sweetify.error(request, 'Error', text=f'Payroll not processed', persistent='Ok')
            return redirect('pay_dashboard')
        if month is not None and year is not None:
            if PayrollDetailStatement.objects.filter(month=month).exists():
                get_user = User.objects.get(id=request.user.id)
                get_emp_payroll = PayrollDetailStatement.objects.get(employee_id=request.user.id, month=month,
                                                                     year=year)
                datetime_object = datetime.datetime.strptime(str(get_emp_payroll.month), "%m")
                month_name = datetime_object.strftime("%b")
                context = dict(employee_id=get_user.employee_id, employee_name=get_user.name,bank=get_user.bank_name,
                               acc_no=get_user.bank_account_number,
                               employee_designation=get_user.designation, ctc=get_emp_payroll.ctc,
                               basic_salary=round(get_emp_payroll.basic_salary * 12),
                               hra_allowance=round(get_emp_payroll.hra_allowance * 12),
                               conv_allowance=round(get_emp_payroll.conv_allowance * 12),
                               other_allowance=round(get_emp_payroll.other_allowance * 12),
                               bonus_arrear=round(get_emp_payroll.bonus_arrear * 12),
                               spl_allowance=round(get_emp_payroll.spl_allowance * 12),
                               total_earnings=round(get_emp_payroll.total_earnings * 12),
                               provident_fund=round(get_emp_payroll.provident_fund * 12),
                               other_deduction=round(get_emp_payroll.other_deduction * 12),
                               income_tax=round(get_emp_payroll.income_tax * 12),
                               pro_tax=round(get_emp_payroll.pro_tax * 12),
                               total_deduction=round(get_emp_payroll.total_deduction * 12),
                               net_amt=round(get_emp_payroll.net_amt * 12),
                               sal_ctc_pm=round(get_emp_payroll.sal_ctc_pm),
                               sal_ctc_pa=round(get_emp_payroll.sal_ctc_pa),
                               gross_salary=get_emp_payroll.gross_salary,
                               net_salary=get_emp_payroll.net_salary, month=month_name,
                               year=get_emp_payroll.year, m_basic_salary=round(get_emp_payroll.basic_salary),
                               m_hra_allowance=round(get_emp_payroll.hra_allowance),
                               m_conv_allowance=round(get_emp_payroll.conv_allowance),
                               m_other_allowance=round(get_emp_payroll.other_allowance),
                               m_bonus_arrear=round(get_emp_payroll.bonus_arrear),
                               m_spl_allowance=round(get_emp_payroll.spl_allowance),
                               m_total_earnings=round(get_emp_payroll.total_earnings),
                               m_provident_fund=round(get_emp_payroll.provident_fund),
                               m_other_deduction=round(get_emp_payroll.other_deduction),
                               m_income_tax=round(get_emp_payroll.income_tax),
                               m_pro_tax=round(get_emp_payroll.pro_tax),
                               m_total_deduction=round(get_emp_payroll.total_deduction),
                               m_net_amt=round(get_emp_payroll.net_amt))
                return render(request, 'payroll/payslips.html', context=dict(payslip=context))
        if PayrollDetailStatement.objects.filter(employee_id=request.user.id, month=current_month).exists():
            get_user = User.objects.get(id=request.user.id)
            get_emp_payroll = PayrollDetailStatement.objects.get(employee_id=request.user.id, month=current_month)
            datetime_object = datetime.datetime.strptime(str(get_emp_payroll.month), "%m")
            month_name = datetime_object.strftime("%b")
            month_name_no = current_month
            context = dict(employee_id=get_user.employee_id, employee_name=get_user.name,
                           bank=get_user.bank_name,
                           acc_no=get_user.bank_account_number,
                           employee_designation=get_user.designation, ctc=get_emp_payroll.ctc,
                           basic_salary=round(get_emp_payroll.basic_salary * 12),
                           hra_allowance=round(get_emp_payroll.hra_allowance * 12),
                           conv_allowance=round(get_emp_payroll.conv_allowance * 12),
                           other_allowance=round(get_emp_payroll.other_allowance * 12),
                           bonus_arrear=round(get_emp_payroll.bonus_arrear * 12),
                           spl_allowance=round(get_emp_payroll.spl_allowance * 12),
                           total_earnings=round(get_emp_payroll.total_earnings * 12),
                           provident_fund=round(get_emp_payroll.provident_fund * 12),
                           other_deduction=round(get_emp_payroll.other_deduction * 12),
                           income_tax=round(get_emp_payroll.income_tax * 12),
                           pro_tax=round(get_emp_payroll.pro_tax * 12),
                           total_deduction=round(get_emp_payroll.total_deduction * 12),
                           net_amt=round(get_emp_payroll.net_amt * 12),
                           sal_ctc_pm=round(get_emp_payroll.sal_ctc_pm),
                           sal_ctc_pa=round(get_emp_payroll.sal_ctc_pa),
                           gross_salary=get_emp_payroll.gross_salary,
                           net_salary=get_emp_payroll.net_salary, month=month_name,month_name_no=month_name_no,
                           year=get_emp_payroll.year, m_basic_salary=round(get_emp_payroll.basic_salary),
                           m_hra_allowance=round(get_emp_payroll.hra_allowance),
                           m_conv_allowance=round(get_emp_payroll.conv_allowance),
                           m_other_allowance=round(get_emp_payroll.other_allowance),
                           m_bonus_arrear=round(get_emp_payroll.bonus_arrear),
                           m_spl_allowance=round(get_emp_payroll.spl_allowance),
                           m_total_earnings=round(get_emp_payroll.total_earnings),
                           m_provident_fund=round(get_emp_payroll.provident_fund),
                           m_other_deduction=round(get_emp_payroll.other_deduction),
                           m_income_tax=round(get_emp_payroll.income_tax),
                           m_pro_tax=round(get_emp_payroll.pro_tax),
                           m_total_deduction=round(get_emp_payroll.total_deduction),
                           m_net_amt=round(get_emp_payroll.net_amt))
            return render(request, 'payroll/payslips.html', context=dict(payslip=context))
        else:
            if PayrollDetailStatement.objects.filter(employee_id=request.user.id, month=previous_month).exists():
                get_user = User.objects.get(id=request.user.id)
                get_emp_payroll = PayrollDetailStatement.objects.get(employee_id=request.user.id, month=previous_month)
                datetime_object = datetime.datetime.strptime(str(get_emp_payroll.month), "%m")
                month_name = datetime_object.strftime("%b")
                month_name_no = previous_month
                context = dict(employee_id=get_user.employee_id, employee_name=get_user.name,
                               bank=get_user.bank_name,
                               acc_no=get_user.bank_account_number,
                               employee_designation=get_user.designation, ctc=get_emp_payroll.ctc,
                               basic_salary=round(get_emp_payroll.basic_salary * 12),
                               hra_allowance=round(get_emp_payroll.hra_allowance * 12),
                               conv_allowance=round(get_emp_payroll.conv_allowance * 12),
                               other_allowance=round(get_emp_payroll.other_allowance * 12),
                               bonus_arrear=round(get_emp_payroll.bonus_arrear * 12),
                               spl_allowance=round(get_emp_payroll.spl_allowance * 12),
                               total_earnings=round(get_emp_payroll.total_earnings * 12),
                               provident_fund=round(get_emp_payroll.provident_fund * 12),
                               other_deduction=round(get_emp_payroll.other_deduction * 12),
                               income_tax=round(get_emp_payroll.income_tax * 12),
                               pro_tax=round(get_emp_payroll.pro_tax * 12),
                               total_deduction=round(get_emp_payroll.total_deduction * 12),
                               net_amt=round(get_emp_payroll.net_amt * 12),
                               sal_ctc_pm=round(get_emp_payroll.sal_ctc_pm),
                               sal_ctc_pa=round(get_emp_payroll.sal_ctc_pm * 12),
                               gross_salary=get_emp_payroll.gross_salary,
                               net_salary=get_emp_payroll.net_salary, month=month_name,month_name_no = month_name_no,
                               year=get_emp_payroll.year, m_basic_salary=round(get_emp_payroll.basic_salary),
                               m_hra_allowance=round(get_emp_payroll.hra_allowance),
                               m_conv_allowance=round(get_emp_payroll.conv_allowance),
                               m_other_allowance=round(get_emp_payroll.other_allowance),
                               m_bonus_arrear=round(get_emp_payroll.bonus_arrear),
                               m_spl_allowance=round(get_emp_payroll.spl_allowance),
                               m_total_earnings=round(get_emp_payroll.total_earnings),
                               m_provident_fund=round(get_emp_payroll.provident_fund),
                               m_other_deduction=round(get_emp_payroll.other_deduction),
                               m_income_tax=round(get_emp_payroll.income_tax),
                               m_pro_tax=round(get_emp_payroll.pro_tax),
                               m_total_deduction=round(get_emp_payroll.total_deduction),
                               m_net_amt=round(get_emp_payroll.net_amt))
                return render(request, 'payroll/payslips.html', context=dict(payslip=context))
        return render(request, 'payroll/payslips.html')


class DownloadPayslip(View):
    def get(self, request, month, year):
        get_user = User.objects.get(id=request.user.id)
        datetime_object = datetime.datetime.strptime(month, "%b")
        month_name = datetime_object.strftime("%m")
        get_emp_payroll = PayrollDetailStatement.objects.get(employee_id=request.user.id, month=month_name, year=year)
        datetime_object = datetime.datetime.strptime(str(get_emp_payroll.month), "%m")
        month_name = datetime_object.strftime("%b")
        emp_name = get_user.name
        print(emp_name)
        html_template = render_to_string('payroll/payslip_pdf.html',
                                         context=dict(payslip=
                                                      dict(employee_id=get_user.employee_id,
                                                           bank=get_user.bank_name,
                                                           acc_no=get_user.bank_account_number,
                                                           employee_name=get_user.name,
                                                           employee_designation=get_user.designation,
                                                           ctc=get_emp_payroll.ctc,
                                                           basic_salary=round(get_emp_payroll.basic_salary * 12),
                                                           hra_allowance=round(get_emp_payroll.hra_allowance * 12),
                                                           conv_allowance=round(get_emp_payroll.conv_allowance * 12),
                                                           other_allowance=round(get_emp_payroll.other_allowance * 12),
                                                           bonus_arrear=round(get_emp_payroll.bonus_arrear * 12),
                                                           spl_allowance=round(get_emp_payroll.spl_allowance * 12),
                                                           total_earnings=round(get_emp_payroll.total_earnings * 12),
                                                           provident_fund=round(get_emp_payroll.provident_fund * 12),
                                                           other_deduction=round(get_emp_payroll.other_deduction * 12),
                                                           income_tax=round(get_emp_payroll.income_tax * 12),
                                                           pro_tax=round(get_emp_payroll.pro_tax * 12),
                                                           total_deduction=round(get_emp_payroll.total_deduction * 12),
                                                           net_amt=round(get_emp_payroll.net_amt * 12),
                                                           sal_ctc_pm=round(get_emp_payroll.sal_ctc_pm),
                                                           sal_ctc_pa=round(get_emp_payroll.sal_ctc_pa),
                                                           gross_salary=get_emp_payroll.gross_salary,
                                                           net_salary=get_emp_payroll.net_salary, month=month_name,
                                                           year=get_emp_payroll.year,
                                                           m_basic_salary=round(get_emp_payroll.basic_salary),
                                                           m_hra_allowance=round(get_emp_payroll.hra_allowance),
                                                           m_conv_allowance=round(get_emp_payroll.conv_allowance),
                                                           m_other_allowance=round(get_emp_payroll.other_allowance),
                                                           m_bonus_arrear=round(get_emp_payroll.bonus_arrear),
                                                           m_spl_allowance=round(get_emp_payroll.spl_allowance),
                                                           m_total_earnings=round(get_emp_payroll.total_earnings),
                                                           m_provident_fund=round(get_emp_payroll.provident_fund),
                                                           m_other_deduction=round(get_emp_payroll.other_deduction),
                                                           m_income_tax=round(get_emp_payroll.income_tax),
                                                           m_pro_tax=round(get_emp_payroll.pro_tax),
                                                           m_total_deduction=round(get_emp_payroll.total_deduction),
                                                           m_net_amt=round(get_emp_payroll.net_amt))))

        pdf_file = HTML(string=html_template, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[
            CSS(
                r'/home/imran06/prowesstics_lms/static/new_dashboard/css/bootstrap/css/bootstrap.min.css',
            )], presentational_hints=True, target=f'/home/imran06/prowesstics_lms/temp/{emp_name}_{month}')
        out = PdfFileWriter()
        file = PdfFileReader(f"/home/imran06/prowesstics_lms/temp/{emp_name}_{month}")
        num = file.numPages
        for idx in range(num):
            page = file.getPage(idx)
            out.addPage(page)
        password = get_user.dob
        day = password.day
        month = password.month
        if len(str(password.day)) < 2:
            day = f"0{password.day}"
        if len(str(password.month)) < 2:
            month = f"0{password.month}"
        password = f"{day}{month}{password.year}"
        print(password)
        out.encrypt(password)
        with open(f"/home/imran06/prowesstics_lms/temp/{emp_name}_{month}_enc.pdf", "wb") as f:
            out.write(f)
        path = f"/home/imran06/prowesstics_lms/temp/{emp_name}_{month}"
        if os.path.isfile(path):
            os.remove(path)
        with open(f"/home/imran06/prowesstics_lms/temp/{emp_name}_{month}_enc.pdf", 'rb') as pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            path = f"/home/imran06/prowesstics_lms/temp/{emp_name}_{month}_enc.pdf"
            if os.path.isfile(path):
                os.remove(path)
            response['Content-Disposition'] = 'attachment; filename="payslip-{}.pdf"'.format(month)
            return response


class ViewForm16(View):
    def get(self, request):
        emp_id = request.user.id
        year = request.GET.get('year')
        try:
            year = year if year is not None else datetime.date.today().year
            print(year)
            name = f"form16_{emp_id}_{year}.pdf"
            # get_request_user = request.user.id
            # get_form16 = Payroll.objects.get(employee_id=get_request_user) name = f"form16_{emp_id}_{year}.pdf"
            full_url = f"{request.scheme}://{request.META['HTTP_HOST']}/media/{name}"
            print(full_url)
            return render(request, 'payroll/form16.html', context=dict(form16=full_url, year=year))
        except:
            sweetify.error(request, 'Error', text=f'Form 16 not uploaded', persistent='Ok')
            return redirect('pay_dashboard')


class HrPolicy(View):
    def get(self, request):
        return render(request, 'payroll/hr_policy.html')
    
from django.conf import settings   
from django.http import FileResponse

def hrpolicy_pdf_view(request):
    # Find the latest PDF file in the 'hr_policy' folder
    static_dir = settings.STATICFILES_DIRS[0]
    training_dir = os.path.join(static_dir, 'hr_policy')
    files = os.listdir(training_dir)
    pdf_files = [f for f in files if f.endswith('.pdf')]
    latest_file = max(pdf_files, key=lambda f: os.path.getmtime(os.path.join(training_dir, f)))

    # Fetch the latest PDF file from the backend
    pdf_file = open(os.path.join(training_dir, latest_file), 'rb')
    response = FileResponse(pdf_file)
    return response



class AllEmployees(View):
    def get(self, request):
        if request.user.role == 'CEO':
            get_user = User.objects.all()
            user = []
            for usr in get_user:
                if Payroll.objects.filter(employee_id=usr.id).exists():
                    get_emp_payroll = Payroll.objects.get(employee_id=usr.id)
                    user.append(dict(email=usr.email, id=usr.id, designation=usr.designation, ctc=get_emp_payroll.ctc))
                else:
                    user.append(dict(email=usr.email, id=usr.id, designation=usr.designation, ctc='-'))
            return render(request, 'payroll/allemployees.html', context=dict(user=user))
        else:
            raise Http404
