import contextlib
import os
import datetime
import json
import logging
import requests
import sweetify
import time
import copy
import operator
import lxml.html as lh
import pandas as pd
import xlwt
import dateutil.relativedelta as REL
import glob


from bs4 import BeautifulSoup
from dateutil.parser import parse
from collections import Counter
# from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.core.mail import EmailMessage
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.http import FileResponse, HttpResponseNotAllowed, HttpResponseRedirect, HttpResponse, JsonResponse, HttpResponsePermanentRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, date, timedelta
from dateutil import relativedelta as rdelta
from .models import *
from prowesstics.utils import *
from django.http import HttpResponseForbidden
from prowesstics import settings

def page_not_found_view(request, exception):
    return render(request, 'dashboard/404.html', status=404)


# Create your views here.
def login_view(request):
    login_user = request.user
    if login_user.is_authenticated:
        return render(request, 'dashboard/loginpayroll.html')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user and user.is_active:
            login(request, user)
            if login_user.is_authenticated:
                print('loginpayroll')
                return render(request, 'dashboard/loginpayroll.html')
            else:
                messages.error(request, 'Account is invalid', extra_tags='alert alert-error alert-dismissible show')
                print('user_login')
                return redirect('user_login')
        else:
            msg = "Invalid Username/Password"
            return render(request, 'dashboard/login.html', {'msg': msg})

    print("############in account login ######################")
    return render(request, 'dashboard/login.html')


@login_required()
def logout_view(request):
    logout(request)
    return redirect(login_view)


def forgot_password(request):
    msg = ''
    if request.method == 'POST':
        email = request.POST.get('email')
        user_list = User.objects.filter(email=email)
        if len(user_list) > 0:
            msg = ''
            password = password_generator(user_list[0])
            user_list[0].set_password(password)
            user_list[0].save()
            send_mail_password(email, password, user_list[0].name)
            print(password)
            return redirect('user_login')
        else:
            msg = 'Invalid email id'
    return render(request, 'dashboard/forgot_password.html', {'msg': msg})


@login_required()
def change_password(request):
    role = request.user.role
    msg = ''
    if request.method == "POST":
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        print("post", password1, password2)
        if password1 != password2:
            msg = 'Passwords doesnt match'
        elif len(password1) < 8:
            msg = "Password's too short"
        else:
            # change password
            request.user.set_password(password1)
            request.user.save()
            # log in
            user = authenticate(request, username=request.user.email, password=password1)
            if user and user.is_active:
                login(request, user)
                if request.user.is_authenticated:
                    return redirect(dashboard)
    return render(request, 'dashboard/change_password.html', {'role': role, 'msg': msg})


@login_required(login_url="user_login")
def dashboard(request):
    if not request.user.admin:
        id = request.user.id
        role, leave_applied, lop, leave_pending, casual_leave, sick_leave = get_info(id)
        print(role)
        r = User.objects.filter(Q(report_to=request.user.id))

        if role == 'EMPLOYEE' and len(r) > 0:
            return redirect('latest_applications')

        if role == 'INTERN' or role == 'EMPLOYEE':
            return redirect('latest_leave')

        return redirect('latest_applications')
    else:
        return redirect('user_leave_history')


@login_required(login_url="user_login")
def latest_leave(request):
    print("#######re##########", request.user.id)

    id = request.user.id
    holiday_date = []
    print(f"id = {id}, role = {request.user.role}")
    if not request.user.admin:
        print("not admin")
        role, leave_applied, lop, leave_pending, casual_leave, sick_leave = get_info(id)

        leave_application = HolidayRequest.objects.filter(user__id=id).order_by('-id')
        user_holiday_list = HolidayRequest.objects.filter(user=request.user, year=current_year())
        for i in user_holiday_list:
            holiday_date.append(
                dict(id_=id, user_=i.user.name, type_=i.category, days_=i.no_of_days, description_=i.description,
                     start_date=i.start_date.strftime("%Y-%m-%d"),
                     end_date=i.end_date.strftime("%Y-%m-%d"), decision_=i.decision))
        print(f'holiday -------------------------------------> {holiday_date}')

        return render(request, 'dashboard/latest_leave.html',
                      {'role': role, 'leave_applied': leave_applied, 'lop': lop, 'user': request.user.name,
                       'holiday': holiday_date,
                       'leave_pending': leave_pending, 'leave_application': leave_application,
                       'casual_leave': casual_leave, 'sick_leave': sick_leave})
    return redirect('dashboard')


@login_required(login_url="user_login")
def apply_leave(request):
    id = request.user.id
    if not request.user.admin:
        msg = False
        role, leave_applied, lop, leave_pending, casual_leave, sick_leave = get_info(id)

        current_years = current_year()
        # assigning holiday
        holiday = []
        holiday_list = HolidayCalender.objects.all().order_by('date')
        x = date.today()
        holiday_list = HolidayCalender.objects.filter(date__year=x.year).order_by('date')
        i = 1
        if UserHoliday.objects.filter(user__id=id)[0].optional_leave >= 2:
            msg = True
        for h in holiday_list:
            temp_date = h.date.strftime('%b %d, %A')
            if h.optional:
                holiday.append({'sno': i, 'date': temp_date, 'raw_date': h.date, 'name': h.name})
            i += 1
        if request.user.dob:
            temp_date1 = request.user.dob
            temp_date_today = date(date.today().year, temp_date1.month, temp_date1.day)
            temp_date = temp_date_today.strftime('%b %d, %A')
            holiday.append({'sno': i, 'date': temp_date, 'raw_date': temp_date_today, 'name': 'Happy Birthday'})
            print(f'kooooooooo{holiday}')
        # POST request
        if request.method == 'POST':
            # getting data from front end
            start_date = request.POST.get('startD')
            end_date = request.POST.get('endD')
            no_of_days = request.POST.get('no-of-days')
            description = request.POST.get('description')
            leave_type = request.POST.get('leaveT')
            category = request.POST.get('category')
            optional_holiday = request.POST.get('holiday-name')

            # saving data to db
            if role == 'EMPLOYEE' or role == "INTERN":
                if category == 'optional':
                    for h in holiday:
                        if h['name'] == optional_holiday:
                            data = HolidayRequest(user_id=id, start_date=h['raw_date'], end_date=h['raw_date'],
                                                  no_of_days=1,
                                                  description=h['name'], category=category, type='full',
                                                  year=current_years)

                            # sending mail
                            try:
                                email = get_user_details(request.user.report_to).email
                                name = get_user_details(request.user.report_to).name
                                send_leave_notification(email, request.user.name, date.today(), name, h['name'])
                                data.save()
                            except:
                                data.save()
                                pass
                else:
                    data = HolidayRequest(user_id=id, start_date=start_date, end_date=end_date, no_of_days=no_of_days,
                                          description=description, category=category, type=leave_type,
                                          year=current_years)

                    # sending mail

                    try:
                        email = get_user_details(request.user.report_to).email
                        name = get_user_details(request.user.report_to).name
                        send_leave_notification(email, request.user.name, date.today(), name, description)
                        data.save()
                    except:
                        # send_leave_notification(email, request.user.name, date.today(), name, description)
                        data.save()
                        pass
            elif role == 'MANAGER':
                if category == 'optional':
                    for h in holiday:
                        if h['name'] == optional_holiday:
                            data = HolidayRequest(user_id=id, start_date=h['raw_date'], end_date=h['raw_date'],
                                                  no_of_days=1, manager_level_approval=True,
                                                  description=h['name'], category=category, type='full',
                                                  year=current_years)
                            # sending mail
                            email, name = [], []
                            user_details = User.objects.filter(role="HR")
                            for u in user_details:
                                email.append(u.email)
                                name.append(u.name)
                            send_leave_notification(email, request.user.name, date.today(), name, h['name'])
                            data.save()
                else:
                    data = HolidayRequest(user_id=id, start_date=start_date, end_date=end_date, no_of_days=no_of_days,
                                          description=description, category=category, type=leave_type,
                                          manager_level_approval=True, year=current_years)
                    # sending mail
                    email, name = [], []
                    user_details = User.objects.filter(role="HR")
                    for u in user_details:
                        email.append(u.email)
                        name.append(u.name)
                    print(email, request.user.name, date.today(), name, description,
                          "testtttttttttttttttttttttttttttttttt")
                    send_leave_notification(email, request.user.name, date.today(), name, description)
                    data.save()
            else:
                if category == 'optional':
                    for h in holiday:
                        if h['name'] == optional_holiday:
                            data = HolidayRequest(user_id=id, start_date=h['raw_date'], end_date=h['raw_date'],
                                                  no_of_days=1, manager_level_approval=True, hr_level_approval=True,
                                                  description=h['name'], category=category, type='full',
                                                  year=current_years)
                            # sending mail
                            email, name = [], []
                            user_details = User.objects.filter(role="HR").exclude(email=request.user.email)
                            for u in user_details:
                                email.append(u.email)
                                name.append(u.name)
                            send_leave_notification_hr(email, request.user.name, date.today(), name, h['name'])
                            data.save()
                else:
                    data = HolidayRequest(user_id=id, start_date=start_date, end_date=end_date, no_of_days=no_of_days,
                                          description=description, category=category, type=leave_type,
                                          manager_level_approval=True, hr_level_approval=True, year=current_years)
                    # sending mail
                    email, name = [], []
                    user_details = User.objects.filter(role="HR")
                    for u in user_details:
                        email.append(u.email)
                        name.append(u.name)
                    print(email, request.user.name, date.today(), name, description)
                    send_leave_notification_hr(email, request.user.name, date.today(), name, description)
                    data.save()
            return redirect('dashboard')
        return render(request, 'dashboard/apply_leave2.html', {'role': role, 'leave_applied': leave_applied, 'lop': lop,
                                                               'leave_pending': leave_pending,
                                                               'casual_leave': casual_leave, 'sick_leave': sick_leave,
                                                               'holiday': holiday,
                                                               'msg': msg})
    return redirect('dashboard')


def apply_leave_ajax(request):
    if request.method == "POST":
        print('dddddddd')
        id = request.POST.get('subject_id')
        hol = []
        holiday = HolidayCalender.objects.all()
        print(holiday)
        for i in holiday:
            format = datetime.datetime.strptime(str(i.date), "%Y-%m-%d").strftime("%Y-%m-%d")

            print(format)

            hol.append(format)

        print(str(hol))

        return HttpResponse(json.dumps(dict(holiday=hol)), content_type="application/json")


@login_required(login_url="user_login")
def compensation(request):
    id = request.user.id
    if not request.user.admin:
        role, leave_applied, lop, leave_pending, casual_leave, sick_leave = get_info(id)
        if request.method == 'POST':
            # getting data from front end
            start_date = request.POST.get('startD')
            end_date = request.POST.get('endD')
            no_of_days = request.POST.get('no-of-days')
            description = request.POST.get('description')
            leave_type = request.POST.get('leaveT')
            category = 'compensation'
            current_years = current_year()
            # saving data to db
            if role == 'EMPLOYEE' or role == 'INTERN':
                # if
                data = HolidayRequest(user_id=id, start_date=start_date, end_date=end_date, no_of_days=no_of_days,
                                      description=description, category=category, type=leave_type, year=current_years)
                # sending mail
                email = get_user_details(request.user.report_to).email
                name = get_user_details(request.user.report_to).name
                send_leave_notification(email, request.user.name, date.today(), name, description)
                data.save()
            elif role == 'MANAGER':
                data = HolidayRequest(user_id=id, start_date=start_date, end_date=end_date, no_of_days=no_of_days,
                                      description=description, category=category, type=leave_type,
                                      manager_level_approval=True,
                                      hr_level_approval=False, year=current_years)
                data.save()
            return redirect('dashboard')
        return render(request, 'dashboard/compensation.html', {'role': role, 'leave_applied': leave_applied, 'lop': lop,
                                                               'leave_pending': leave_pending,
                                                               'casual_leave': casual_leave, 'sick_leave': sick_leave})

    return redirect('dashboard')


@login_required(login_url="user_login")
def redeem(request):
    id = request.user.id
    name=request.user.name
    email_user = request.user.email
    today = date.today()
    # date(today.year-1, today.month, today.day)
    user_holiday = UserHoliday.objects.filter(Q(user__id=id) & Q(year=prev_year()))
    casual = user_holiday[0].casual_leave_allowed - user_holiday[0].casual_leave if user_holiday else 0
    active = 'False'
    print(today.month, today.day, current_year())
    # 4 7
    if today.month == 4 and today.day in [10,11,12]:
        active = 'True'
    if not request.user.admin:
        role, leave_applied, lop, leave_pending, casual_leave, sick_leave = get_prev_info(id)
        if request.method == "POST":
            no_of_days = request.POST.get('casual-leave')
            description = request.POST.get('description')
            # if role == "EMPLOYEE" or role == "INTERN":
            #     data = HolidayRequest(user_id=id, start_date=today, end_date=today, no_of_days=no_of_days,
            #                           description=description, category="redeem")
            #     data.save()
            # elif role == "MANAGER":
            #     data = HolidayRequest(user_id=id, start_date=today, end_date=today, no_of_days=no_of_days,
            #                           description=description, category="redeem", manager_level_approval=True)
            #     data.save()
            # else:
            #     data = HolidayRequest(user_id=id, start_date=today, end_date=today, no_of_days=no_of_days,
            #                           description=description, category="redeem",
            #                           manager_level_approval=True, hr_level_approval=True)
            #     data.save()
            category="Redeem"
            email = EmailMessage(
            subject=f"Redeem Request From the Users",
            body=(
                "<table>"
                "<tr><td>Name:</td><td>" + name + "</td></tr>"
                "<tr><td>Email:</td><td>" + email_user + "</td></tr>"
                "<tr><td><strong>No of Days:</strong></td><td>" + no_of_days + "</td></tr>"
                "<tr><td>Description:</td><td>" + description + "</td></tr>"
                "<tr><td>Category:</td><td>" + category + "</td></tr>"
                "<tr><td>Applied Date:</td><td>" + str(today) + "</td></tr>"
                "</table>"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=['jerson.antony@prowesstics.com','hr@prowesstics.com'],
            )
            email.content_subtype = "html"
            email.send()

            return redirect('dashboard')
        else:
            return render(request, 'dashboard/redeem.html',
                          {'role': role, 'active': active, 'casual': casual, 'casual_leave': casual_leave,
                           'sick_leave': sick_leave, 'leave_applied': leave_applied, 'lop': lop})
    return redirect('dashboard')


@login_required(login_url="user_login")
def latest_appications(request):
    holiday_date = []
    id = request.user.id
    page_l = request.GET.get('page_l', 1)
    page = request.GET.get('page', 1)
    user_holiday_list = HolidayRequest.objects.filter(user=request.user, year=current_year())
    for i in user_holiday_list:
        holiday_date.append(
            dict(id_=id, user_=i.user.name, type_=i.category, days_=i.no_of_days, description_=i.description,
                 start_date=i.start_date.strftime("%Y-%m-%d"),
                 end_date=i.end_date.strftime("%Y-%m-%d"), decision_=i.decision))
    print(f'holiday -------------------------------------> {holiday_date}')

    if not request.user.admin:
        role, leave_applied, lop, leave_pending, casual_leave, sick_leave = get_info(id)
        if role != "INTERN":
            if role == 'HR':
                leave_application = HolidayRequest.objects.filter(~Q(user__id=id) &
                                                                  (Q(manager_level_approval=True) | Q(
                                                                      user__report_to=id) |
                                                                   Q(user__role='MANAGER'))).order_by('-id')
                print('leave_application', leave_application)
                leave_application_self = HolidayRequest.objects.filter(user__id=id).order_by('-id')
                print(leave_application_self)

            else:
                leave_application = HolidayRequest.objects.filter(user__report_to=id).order_by('-id')
                print(leave_application)
                leave_application_self = HolidayRequest.objects.filter(user__id=id).order_by('-id')
                print(leave_application_self)

        paginator = Paginator(leave_application, 20)
        try:
            leave_application = paginator.page(page_l)
        except PageNotAnInteger:
            leave_application = paginator.page(1)
        except EmptyPage:
            leave_application = paginator.page(paginator.num_pages)

        paginator = Paginator(leave_application_self, 20)
        try:
            leave_application_self = paginator.page(page)
        except PageNotAnInteger:
            leave_application_self = paginator.page(1)
        except EmptyPage:
            leave_application_self = paginator.page(paginator.num_pages)
        return render(request, 'dashboard/latest_applications.html',
                      {'id': id, 'user': request.user.name, 'role': role, 'holiday': holiday_date,
                       'leave_applied': leave_applied,
                       'lop': lop, 'casual_leave': casual_leave,
                       'sick_leave': sick_leave,
                       'leave_pending': leave_pending,
                       'leave_application': leave_application,
                       'leave_application1': leave_application_self})
    return redirect(dashboard)


@login_required(login_url="user_login")
def rejected_applications(request):
    id = request.user.id
    if not request.user.admin:
        role, leave_applied, lop, leave_pending, casual_leave, sick_leave = get_info(id)
        if role != 'EMPLOYEE' or role != "INTERN":
            if role == 'HR':
                rejected_application = HolidayRequest.objects.filter(manager_level_approval=False).order_by('-id')
                return render(request, 'dashboard/rejected_applications.html', {'role': role,
                                                                                'rejected_application': rejected_application})
    return redirect(dashboard)


@login_required(login_url="user_login")
def user_holiday_details(request):
    id = request.user.id
    if not request.user.admin:
        role, leave_applied, lop, leave_pending, casual_leave, sick_leave = get_info(id)
        if role == 'HR':
            if request.method == "POST":
                emp_name = request.POST.get('name')
                emp_sick = request.POST.get('sick_leave')
                emp_casual = request.POST.get('casual_leave')
                emp_lop = request.POST.get('lop')
                emp_optional = request.POST.get('optional_leave')

                user_detail = UserHoliday.objects.get(user__name=emp_name, year=current_year())
                user_detail.sick_leave = float(emp_sick)
                user_detail.casual_leave = float(emp_casual)
                user_detail.lop = float(emp_lop)
                user_detail.optional_leave = float(emp_optional)
                user_detail.save()
                return redirect(rejected_applications)
            employee_id = int(request.GET.get('id')) if request.GET.get('id') is not None else 0
            print("id= ", employee_id, type(id))
            user_detail = UserHoliday.objects.filter(user__id=employee_id, year=current_year())[0]
            return render(request, 'dashboard/user_holiday_details.html', {'role': role, 'user_detail': user_detail})

    return redirect(dashboard)


@login_required(login_url="user_login")
def leave_details(request):
    id = request.user.id
    if request.user.role != 'ADMIN':
        if request.user.admin:
            role = request.user.role
        else:
            role, leave_applied, lop, leave_pending, casual_leave, sick_leave = get_info(id)
        edit_access = 'False'
        if request.method == 'GET':
            app_id = request.GET.get('id')
            application = HolidayRequest.objects.filter(id=app_id, year=current_year())[0]
            history = UserHoliday.objects.filter(user__id=application.user.id, year=current_year())[0]
            sick_remain = history.sick_leave_allowed - history.sick_leave
            casual_remain = history.casual_leave_allowed - history.casual_leave
            optional_remain = 2 - history.optional_leave
            leave_remain = dict(sick=sick_remain, casual=casual_remain, optional=optional_remain)
            # edit access False -> Delete, True -> Approve/Reject, None -> Nothing
            if role == 'MANAGER':
                edit_access = 'True'
                if application.user.name == request.user.name:
                    edit_access = 'False'
                if application.admin_level_approval is not None:
                    edit_access = 'None'
                if application.user.report_to == request.user.id:
                    edit_access = 'True'
            elif role == 'HR':
                edit_access = 'True'
                if application.admin_level_approval is not None:
                    print(f'application.admin_level_approval is {application.admin_level_approval}')
                if application.user.role == 'ADMIN':
                    edit_access = 'False'
                    print('edit access = ', edit_access)
                if application.user.name == request.user.name:
                    edit_access = 'False'
            elif role == 'EMPLOYEE':
                edit_access = "True"
                if application.user.name == request.user.name:
                    edit_access = 'False'
                if application.user.report_to == request.user.id:
                    edit_access = 'True'

            else:
                if role == 'ADMIN':
                    edit_access = 'None'
                if application.user.role == 'HR':
                    edit_access = 'True'
            return render(request, 'dashboard/leave_details.html', {'role': role, 'application': application,
                                                                    'access': edit_access, 'leave': leave_remain})
        else:
            decision = request.POST.get('decision') if request.POST.get('decision') else ''
            print("DECISIONNNNNNNNNNNNNNNNNNNN", decision)
            app_id = request.POST.get('id')
            application_approve = HolidayRequest.objects.get(id=app_id)
            user_holiday = UserHoliday.objects.get(user__id=application_approve.user.id, year=current_year())
            try:
                my_list = application_approve.leaves_sep_v.split(",")
            except AttributeError:
                my_list = None
            print(my_list, 'ooooo', app_id, application_approve.user.id)

            if request.POST.get('accept') == 'accept':
                for my in my_list:
                    print('fffffffffffffffffffffffffffffffff', my)
                    # time = Timesheet.objects.filter(user_id=application_approve.user.id,status='Leave' or 'DetailsNone',
                    #                                 date=my).delete()
                    time = Timesheet.objects.filter(
                        Q(user_id=application_approve.user.id, status='Leave ', date=my) | Q(
                            user_id=application_approve.user.id, status='DetailsNone', date=my)
                        | Q(user_id=application_approve.user.id, status='Compensation Leave', date=my)).delete()
                    print(time, 'ssssas')
                    leave_count = calculate_leave_type(application_approve, 'accept')

                print("leave_count", leave_count, application_approve.user.report_to)

                if role == 'HR':
                    print('HR')
                    if application_approve.user.role == 'MANAGER':
                        if application_approve.admin_level_approval != True:
                            application_approve.hr_level_approval = True
                            application_approve.admin_level_approval = True
                            application_approve.employee_level_approval = True
                            application_approve.decision = decision
                            # delta leave to keep track of previous leave
                            application_approve.delta_sick = leave_count['sick'] - user_holiday.sick_leave
                            application_approve.delta_casual = leave_count['casual'] - user_holiday.casual_leave
                            application_approve.delta_lop = leave_count['lop'] - user_holiday.lop
                            application_approve.delta_optional = leave_count['optional'] - user_holiday.optional_leave
                            # updating actual values
                            user_holiday.sick_leave = leave_count['sick']
                            user_holiday.casual_leave = leave_count['casual']
                            user_holiday.lop = leave_count['lop']
                            user_holiday.optional_leave = leave_count['optional']
                            user_holiday.redeem_leave = leave_count['redeem']
                            user_holiday.save()
                            application_approve.save()
                    if application_approve.user.role == 'EMPLOYEE':
                        print('hr employee')
                        if application_approve.manager_level_approval == True:
                            application_approve.hr_level_approval = True
                            application_approve.admin_level_approval = True
                            application_approve.employee_level_approval = True
                            application_approve.decision = decision
                            # delta leave to keep track of previous leave
                            application_approve.delta_sick = leave_count['sick'] - user_holiday.sick_leave
                            application_approve.delta_casual = leave_count['casual'] - user_holiday.casual_leave
                            application_approve.delta_lop = leave_count['lop'] - user_holiday.lop
                            application_approve.delta_optional = leave_count['optional'] - user_holiday.optional_leave
                            # updating actual values
                            user_holiday.sick_leave = leave_count['sick']
                            user_holiday.casual_leave = leave_count['casual']
                            user_holiday.lop = leave_count['lop']
                            user_holiday.optional_leave = leave_count['optional']
                            user_holiday.redeem_leave = leave_count['redeem']
                            user_holiday.save()
                            application_approve.save()
                elif role == 'MANAGER':
                    print('Mang')
                    if application_approve.user.role == 'EMPLOYEE':
                        if application_approve.manager_level_approval is None:
                            application_approve.manager_level_approval = True
                            application_approve.decision = decision
                            # sending mail
                            email, name = [], []
                            user_details = User.objects.filter(role="HR")
                            for u in user_details:
                                email.append(u.email)
                                name.append(u.name)
                            send_leave_notification(email, application_approve.user.name, date.today(), name, decision)
                            application_approve.save()

                    # ''' added employee to employee  leave req'''

                elif application_approve.user.role == 'EMPLOYEE' and application_approve.user.report_to == id:
                    print('toooooooo')
                    application_approve.manager_level_approval = True
                    application_approve.hr_level_approval = True
                    application_approve.admin_level_approval = True
                    application_approve.employee_level_approval = True
                    application_approve.decision = decision
                    # delta leave to keep track of previous leave
                    application_approve.delta_sick = leave_count['sick'] - user_holiday.sick_leave
                    application_approve.delta_casual = leave_count['casual'] - user_holiday.casual_leave
                    application_approve.delta_lop = leave_count['lop'] - user_holiday.lop
                    application_approve.delta_optional = leave_count['optional'] - user_holiday.optional_leave
                    # updating actual values
                    user_holiday.sick_leave = leave_count['sick']
                    user_holiday.casual_leave = leave_count['casual']
                    user_holiday.lop = leave_count['lop']
                    user_holiday.optional_leave = leave_count['optional']
                    user_holiday.redeem_leave = leave_count['redeem']
                    user_holiday.save()
                    application_approve.save()

                elif application_approve.user.role == 'INTERN':
                    print('toooooooo2')

                    if application_approve.user.report_to == id:
                        application_approve.manager_level_approval = True
                        application_approve.hr_level_approval = True
                        application_approve.admin_level_approval = True
                        application_approve.employee_level_approval = True
                        application_approve.decision = decision
                        # delta leave to keep track of previous leave
                        application_approve.delta_sick = leave_count['sick'] - user_holiday.sick_leave
                        application_approve.delta_casual = leave_count['casual'] - user_holiday.casual_leave
                        application_approve.delta_lop = leave_count['lop'] - user_holiday.lop
                        application_approve.delta_optional = leave_count['optional'] - user_holiday.optional_leave
                        # updating actual values
                        user_holiday.sick_leave = leave_count['sick']
                        user_holiday.casual_leave = leave_count['casual']
                        user_holiday.lop = leave_count['lop']
                        user_holiday.optional_leave = leave_count['optional']
                        user_holiday.redeem_leave = leave_count['redeem']
                        user_holiday.save()
                        application_approve.save()

                else:
                    print("in accept else part", leave_count)
                    if role == 'CEO':
                        if application_approve.admin_level_approval != True:
                            application_approve.admin_level_approval = True
                            application_approve.decision = decision
                            # delta leave to keep track of previous leave
                            application_approve.delta_sick = leave_count['sick'] - user_holiday.sick_leave
                            application_approve.delta_casual = leave_count['casual'] - user_holiday.casual_leave
                            application_approve.delta_lop = leave_count['lop'] - user_holiday.lop
                            application_approve.delta_optional = leave_count['optional'] - user_holiday.optional_leave
                            # updating actual values
                            user_holiday.sick_leave = leave_count['sick']
                            user_holiday.casual_leave = leave_count['casual']
                            user_holiday.lop = leave_count['lop']
                            user_holiday.optional_leave = leave_count['optional']
                            user_holiday.redeem_leave = leave_count['redeem']
                            user_holiday.save()
                            application_approve.save()
            elif request.POST.get('reject') == 'reject':
                leave_count = calculate_leave_type(application_approve, 'reject')
                print("leave_count", leave_count)
                if role == 'HR':
                    if application_approve.user.role == 'MANAGER':
                        if application_approve.admin_level_approval:
                            application_approve.hr_level_approval = False
                            application_approve.admin_level_approval = False
                            application_approve.decision = decision
                            # delta leave to keep track of previous leave
                            application_approve.delta_sick = 0
                            application_approve.delta_casual = 0
                            application_approve.delta_lop = 0
                            application_approve.delta_optional = 0
                            # updating actual values
                            user_holiday.sick_leave = leave_count['sick']
                            user_holiday.casual_leave = leave_count['casual']
                            user_holiday.lop = leave_count['lop']
                            user_holiday.optional_leave = leave_count['optional']
                            user_holiday.redeem_leave = leave_count['redeem']
                        else:
                            application_approve.hr_level_approval = False
                            application_approve.admin_level_approval = False
                            application_approve.decision = decision
                        user_holiday.save()
                        application_approve.save()
                    if application_approve.user.role == 'EMPLOYEE':
                        if application_approve.manager_level_approval:
                            if application_approve.admin_level_approval:
                                application_approve.hr_level_approval = False
                                application_approve.admin_level_approval = False
                                application_approve.decision = decision
                                # delta leave to keep track of previous leave
                                application_approve.delta_sick = 0
                                application_approve.delta_casual = 0
                                application_approve.delta_lop = 0
                                application_approve.delta_optional = 0
                                # updating actual values
                                user_holiday.sick_leave = leave_count['sick']
                                user_holiday.casual_leave = leave_count['casual']
                                user_holiday.lop = leave_count['lop']
                                user_holiday.optional_leave = leave_count['optional']
                                user_holiday.redeem_leave = leave_count['redeem']
                            else:
                                application_approve.hr_level_approval = False
                                application_approve.admin_level_approval = False
                                application_approve.decision = decision
                            user_holiday.save()
                            application_approve.save()
                elif role == 'MANAGER':
                    if application_approve.user.role == 'EMPLOYEE':
                        if application_approve.manager_level_approval is None:
                            application_approve.manager_level_approval = False
                            application_approve.decision = decision
                            # sending mail
                            email, name = [], []
                            user_details = User.objects.filter(role="HR")
                            for u in user_details:
                                email.append(u.email)
                                name.append(u.name)
                            send_leave_notification(email, application_approve.user.name, date.today(), name, decision)
                            application_approve.save()

                elif application_approve.user.role == 'EMPLOYEE' and application_approve.user.report_to == id:
                    application_approve.manager_level_approval = False
                    application_approve.hr_level_approval = False
                    application_approve.admin_level_approval = False
                    application_approve.employee_level_approval = False
                    application_approve.decision = decision
                    # delta leave to keep track of previous leave
                    application_approve.delta_sick = leave_count['sick'] - user_holiday.sick_leave
                    application_approve.delta_casual = leave_count['casual'] - user_holiday.casual_leave
                    application_approve.delta_lop = leave_count['lop'] - user_holiday.lop
                    application_approve.delta_optional = leave_count['optional'] - user_holiday.optional_leave
                    # updating actual values
                    user_holiday.sick_leave = leave_count['sick']
                    user_holiday.casual_leave = leave_count['casual']
                    user_holiday.lop = leave_count['lop']
                    user_holiday.optional_leave = leave_count['optional']
                    user_holiday.redeem_leave = leave_count['redeem']
                    user_holiday.save()
                    application_approve.save()
                elif application_approve.user.role == 'INTERN':
                    if application_approve.user.report_to == id:
                        if application_approve.admin_level_approval:
                            application_approve.manager_level_approval = False
                            application_approve.hr_level_approval = False
                            application_approve.admin_level_approval = False
                            application_approve.employee_level_approval = False
                            application_approve.decision = decision
                            # delta leave to keep track of previous leave
                            application_approve.delta_sick = 0
                            application_approve.delta_casual = 0
                            application_approve.delta_lop = 0
                            application_approve.delta_optional = 0
                            # updating actual values
                            user_holiday.sick_leave = leave_count['sick']
                            user_holiday.casual_leave = leave_count['casual']
                            user_holiday.lop = leave_count['lop']
                            user_holiday.optional_leave = leave_count['optional']
                            user_holiday.redeem_leave = leave_count['redeem']
                        else:
                            application_approve.manager_level_approval = False
                            application_approve.hr_level_approval = False
                            application_approve.admin_level_approval = False
                            application_approve.decision = decision
                        user_holiday.save()
                        application_approve.save()

                else:
                    print("in reject else part", leave_count)
                    if role == 'CEO':
                        if application_approve.admin_level_approval:
                            application_approve.admin_level_approval = False
                            application_approve.decision = decision
                            # delta leave to keep track of previous leave
                            application_approve.delta_sick = 0
                            application_approve.delta_casual = 0
                            application_approve.delta_lop = 0
                            application_approve.delta_optional = 0
                            # updating actual values
                            user_holiday.sick_leave = leave_count['sick']
                            user_holiday.casual_leave = leave_count['casual']
                            user_holiday.lop = leave_count['lop']
                            user_holiday.optional_leave = leave_count['optional']
                            user_holiday.redeem_leave = leave_count['redeem']
                            user_holiday.save()
                            application_approve.save()
                        else:
                            application_approve.admin_level_approval = False
                            application_approve.decision = decision
                            application_approve.save()

            else:
                if request.user.role == role:
                    app_id = request.POST.get('id')
                    application_delete = HolidayRequest.objects.get(id=app_id)
                    application_delete.delete()
                    print("deleted application id = ", app_id)
    return redirect('dashboard')




@login_required(login_url="user_login")
def leave_tracker(request):
    role = 'ADMIN' if request.user.admin else ''
    return render(request, 'dashboard/leave_tracker.html', {'role': role})


@login_required(login_url="user_login")
def holiday_calender(request):
    if request.user.admin:
        role = request.user.role
    else:
        role, leave_applied, lop, leave_pending, casual_leave, sick_leave = get_info(request.user.id)
    x = date.today()
    print(x.year)
    holiday = []
    holiday_list = HolidayCalender.objects.filter(date__year=x.year).order_by('date')
    print(holiday_list)
    i = 1
    for h in holiday_list:
        temp_date = h.date.strftime('%b %d, %A')
        opt = 'Optional' if h.optional else ''
        holiday.append({'sno': i, 'date': temp_date, 'name': h.name, 'opt': opt})
        i += 1
    if request.user.dob:
        temp_date = request.user.dob
        temp_date_today = date(date.today().year, temp_date.month, temp_date.day)
        temp_date = temp_date_today.strftime('%b %d, %A')
        holiday.append({'sno': i, 'date': temp_date, 'name': 'Happy Birthday', 'opt': 'Optional'})
    print(holiday)
    return render(request, 'dashboard/holiday_calender.html', {'role': role, 'holiday': holiday})



@login_required(login_url="user_login")
@csrf_exempt
def create_user(request):
    if request.user.role == 'ADMIN':
        report_to = User.objects.filter(role='MANAGER')
        report_to_1 = User.objects.all()

        if request.method == 'POST':
            username = request.POST.get('username')
            email = request.POST.get('email')
            role = request.POST.get('role')
            designation = request.POST.get('designation')
            gender = request.POST.get('gender')
            dob = request.POST.get('dob')
            doj = request.POST.get('doj')
            profile_pic = request.FILES.get('profile_pic')
            employee_id = request.POST.get('emp_id')
            print(profile_pic)
            sick = 0 if request.POST.get('sick') is None else request.POST.get('sick')
            casual = 0 if request.POST.get('casual') is None else request.POST.get('casual')
            if role == 'EMPLOYEE':
                rt = request.POST.get('report_to') if request.POST.get('report_to') else None
                if rt == 'none':
                    rt = None
            else:
                rt = request.POST.get('report_to_1') if request.POST.get('report_to_1') else None
                if rt == 'none':
                    rt = None
            print(rt, request.POST.get('report_to'))
            password = password_generator()
            if not User.objects.filter(email=email):
                # User.objects.create_user(email=email, password='password')
                if role == 'EMPLOYEE' or role == 'INTERN':
                    temp_user = User.objects.create(email=email, password=make_password(password=password),
                                                    name=username, gender=gender, role=get_role(role), report_to=rt,
                                                    designation=designation, dob=dob, doj=doj, profile_pic=profile_pic,
                                                    employee_id=employee_id)
                else:
                    temp_user = User.objects.create(email=email, password=make_password(password=password),
                                                    name=username, gender=gender, role=get_role(role),
                                                    designation=designation, dob=dob, doj=doj, profile_pic=profile_pic,
                                                    employee_id=employee_id
                                                    )
                temp_user = User.objects.filter(email=email)[0]
                temp_userid = temp_user.id
                temp_userholiday = UserHoliday(user_id=temp_userid, sick_leave_allowed=float(sick),
                                               casual_leave_allowed=float(casual), year=current_year())
                temp_userholiday.save()
                pass_save = TempUserData(user_id=temp_userid, code=password)
                pass_save.save()
                print("user created")
                send_mail_password(email, password, username)
                return redirect('modified_user')
            else:
                msg = "Email id exits"
                print(msg)
            print("ssssssssssssss", username, email, role, designation, gender, dob, doj, sick, casual)
        role = request.user.role
        return render(request, 'dashboard/create_user.html', {'role': role, 'report_to': report_to,
                                                              'report_to_1': report_to_1})
    return redirect(dashboard)


@login_required(login_url="user_login")
def modified_user(request):
    role = request.user.role
    # pg=request.user.get('pg_r')
    pg_r = request.GET.get('pg_r', None)
    print(pg_r)
    if role == 'ADMIN':
        user_list = User.objects.filter(admin=False).order_by('name')

        # paginator = Paginator(user_list, 10)
        page = request.GET.get('page')
        if pg_r is not None:
            paginator = Paginator(user_list, int(pg_r))
            print(paginator)
        else:
            paginator = Paginator(user_list, 10)
        try:
            pages = paginator.page(page)
            print(f'h1{pages}')
        except PageNotAnInteger:
            pages = paginator.page(1)
            # print(f'h2{pages}')
        except EmptyPage:
            pages = paginator.page(paginator.num_pages)
            # print(f'h3{pages}')

        return render(request, 'dashboard/modified_user.html',
                      {'role': role, 'users': pages, 'pg_r': int(pg_r) if pg_r is not None else 10})
    return redirect('dashboard')


@login_required(login_url="user_login")
def edit_user(request):
    role = request.user.role

    if role == 'ADMIN':
        report_to = User.objects.filter(role='MANAGER')
        print("id", request.GET.get('id'))
        if request.method == 'GET':
            user_id = int(request.GET.get('id'))
            report_to_1 = User.objects.filter(~Q(id=user_id))
            user = User.objects.filter(id=user_id)[0]
            holiday = UserHoliday.objects.filter(user__id=user_id)[0]
            dob = user.dob.strftime("%Y-%m-%d")
            doj = user.doj.strftime("%Y-%m-%d")
            profile_pic = user.profile_pic

            user_list = UserHoliday.objects.filter(~Q(user__id=user_id) & Q(year=current_year()))[0]
            print(user_list)
            user_details = dict(id=user.id, emp=user.employee_id, name=user.name, email=user.email, role=user.role,
                                rt=user.report_to,
                                designation=user.designation, gender=user.gender, dob=dob, doj=doj,
                                sick=holiday.sick_leave_allowed, casual=holiday.casual_leave_allowed,
                                lop=holiday.lop,
                                optional=holiday.optional_leave,
                                leave_redeem=holiday.redeem_leave, asset=user.asset,
                                per_address1=user.per_address1,
                                per_address2=user.per_address2,
                                tem_address1=user.tem_address1,
                                tem_address2=user.tem_address2,
                                per_city=user.per_city,
                                per_state=user.per_state,
                                per_country=user.per_country,
                                per_pincode=user.per_pincode,
                                same_as_per_addr=user.same_as_per_addr,
                                per_phone_number=user.per_phone_number,
                                tem_city=user.tem_city,
                                tem_state=user.tem_state,
                                tem_country=user.tem_country,
                                tem_pincode=user.tem_pincode,
                                tem_phone_number=user.tem_phone_number,
                                computer_brand=user.computer_brand,
                                computer_ram=user.computer_ram,
                                computer_processor=user.computer_processor,
                                personal_email=user.personal_email,
                                bank=user.bank_name,
                                acc_no=user.bank_account_number)
            # print(report_to,report_to_1,user_details)
            return render(request, 'dashboard/modified_page.html', {'role': role, 'user': user_details,
                                                                    'report_to': report_to, 'report_to_1': report_to_1,
                                                                    'profile_pic': profile_pic})
        else:
            id = request.POST.get('id')
            emp = request.POST.get('emp_id')
            print(id)
            username = request.POST.get('username')
            email = request.POST.get('email')
            role = request.POST.get('role')
            designation = request.POST.get('designation')
            gender = request.POST.get('gender')
            dob = request.POST.get('dob')
            doj = request.POST.get('doj')
            bank = request.POST.get('bank')
            acc_no = request.POST.get('acc_no')
            print(f'{bank}{acc_no}')
            data = User.objects.get(id=request.user.id)
            profile_pic = request.FILES.get('profile_pic')
            print(f'hhjhhhh{profile_pic}')
            sick = 0 if request.POST.get('sick') is None else request.POST.get('sick')
            casual = 0 if request.POST.get('casual') is None else request.POST.get('casual')
            lop = 0 if request.POST.get('lop') is None else request.POST.get('lop')
            oh_availed = 0 if request.POST.get('oh_availed') is None else request.POST.get('oh_availed')
            leave_redeemed = 0 if request.POST.get('leave_redeemed') is None else request.POST.get('leave_redeemed')
            rt = request.POST.get('report_to') if request.POST.get('report_to') else None
            rt1 = request.POST.get('report_to_1') if request.POST.get('report_to_1') else None
            print('POST')
            print(id, username, email, role, designation, gender, dob, doj, sick, casual, rt, profile_pic, acc_no, bank)
            user = User.objects.filter(id=id)[0]
            print(user)
            user.profile_pic = profile_pic
            print(user.profile_pic)
            user.name = username
            user.email = email
            user.role = role
            user.designation = designation
            user.gender = gender
            user.dob = dob
            user.doj = doj
            user.employee_id = emp
            user.bank_name = bank
            user.bank_account_number = acc_no

            if user.role == 'EMPLOYEE':
                try:
                    user.report_to = int(rt)
                except ValueError:
                    user.report_to = None
                    print(f'hhhhhhhhhhh{user.report_to}')
            elif user.role == 'INTERN':
                try:
                    user.report_to = int(rt)
                except ValueError:
                    user.report_to = None
                    print(f'hhhhhhhhhhh{user.report_to}')
            else:

                user.report_to = None

            user.save()
            user_holiday = UserHoliday.objects.filter(user_id=id)[0]
            user_holiday.sick_leave_allowed = sick
            user_holiday.casual_leave_allowed = casual
            user_holiday.lop = lop
            user_holiday.optional_leave = oh_availed
            user_holiday.redeem_leave = leave_redeemed

            user_holiday.save()
            return redirect('modified_user')
    return redirect('dashboard')


@login_required(login_url="user_login")
def delete_user(request):
    role = request.user.role
    if role == 'ADMIN':
        if request.method == 'GET':
            user_list = User.objects.filter(admin=False).order_by('name')
            paginator = Paginator(user_list, 10)
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
            return render(request, 'dashboard/delete_user.html', {'role': role, 'users': pages})
        else:
            id = request.POST.get('id')
            user_delete = User.objects.get(id=id)
            user_delete.delete()
            print("delete id = ", id)
            return redirect('delete_user')
    return redirect('dashboard')


def sort(value):
    # print(value)
    return value['name']


def name_and_count_from_holiday(holiday):
    name_count = {}
    for item in holiday:
        name = item['user_']
        no_days = item['no_days']
        if name not in name_count:
            name_count[name] = {'name': name, 'count': no_days}
        else:
            name_count[name]['count'] += no_days
    return list(name_count.values())


@login_required(login_url="user_login")
def user_leave_history(request):
    page = request.GET.get('page', '')
    pg_r = request.GET.get('pg_r', None)
    year_ = request.GET.get('year_', None)
    available_years = ['2021-2022', '2022-2023', '2023-2024']
    print("pg_r", pg_r)
    if request.user.admin or request.user.role == 'HR':
        role = request.user.role
        data = []
        holiday_data = []
        comp_data = []
        if year_ is not None:
            year_ = year_
        else:
            year_ = current_year()

        print(year_)
        user_list = UserHoliday.objects.filter(~Q(user__role='ADMIN') & Q(year=year_))
        print(user_list, 'user_list')
        user_holiday_list = HolidayRequest.objects.filter(year=year_)
        print(user_holiday_list)
        # print(user_holiday_list)
        for i in user_holiday_list:
            if i.category == 'compensation':
                comp_data.append(dict(user_=i.user.name, type_=i.category, description_=i.description,
                                      start_date=i.start_date.strftime("%Y-%m-%d"),
                                      end_date=i.end_date.strftime("%Y-%m-%d"), decision_=i.decision,
                                      no_days=i.no_of_days))
            elif i.category == 'compensation' or i.category == 'sick' or i.category == 'casual':
                holiday_data.append(dict(user_=i.user.name, type_=i.category, description_=i.description, user_id=i.id,
                                         start_date=i.start_date.strftime("%Y-%m-%d"),
                                         end_date=i.end_date.strftime("%Y-%m-%d"), decision_=i.decision,
                                         no_days=float(i.no_of_days)))
        print(holiday_data, 'holi')

        name_c = name_and_count_from_holiday(holiday_data)
        print('name_c', name_c)
        for user in user_list:
            applied = user.sick_leave + user.casual_leave

            applied_count = 0
            for count in name_c:
                if user.user.name in count['name']:
                    print(count['count'])
                    applied_count += count['count']
            times_deduction = applied + user.lop - applied_count

            pending = user.sick_leave_allowed + user.casual_leave_allowed - applied
            # print(pending)
            compensation_leave = len(HolidayRequest.objects.filter(user__id=user.user.id, category='compensation',
                                                                   admin_level_approval=True, year=year_))
            # print(compensation_leave)
            # applied count is added instead of applied to validate the  count of leave employees applied
            data.append(dict(id=user.user.id, name=user.user.name,
                             time_det=int(times_deduction) if (times_deduction * 10) % 10 == 0 else times_deduction,
                             applied=int(applied_count) if (applied_count * 10) % 10 == 0 else applied_count,
                             # applied =applied_count,
                             pending=int(pending) if (pending * 10) % 10 == 0 else pending,
                             lop=int(user.lop) if (user.lop * 10) % 10 == 0 else user.lop,
                             optional=int(user.optional_leave) if (user.optional_leave * 10) % 10 == 0
                             else user.optional_leave,
                             compensation=compensation_leave,
                             sick_leave_pending=user.sick_leave_allowed - user.sick_leave,
                             casual_leave_pending=user.casual_leave_allowed - user.casual_leave,
                             redeem=int(user.redeem_leave) if (
                                                                      user.redeem_leave * 10) % 10 == 0 else user.redeem_leave))
            # print(data)
            # print(applied_count, 'applied')
        d = sorted(data, key=sort)
        # print(d)

        if pg_r is not None:
            paginator = Paginator(d, int(pg_r))
        else:
            paginator = Paginator(d, 10)
        try:
            d = paginator.page(page)
        except PageNotAnInteger:
            d = paginator.page(1)
        except EmptyPage:
            d = paginator.page(paginator.num_pages)
        # print("print_data", data.has_other_pages())
        return render(request, 'dashboard/employee_leave.html',
                      {'role': role, 'users': d, 'holiday': holiday_data, 'pg_r': int(pg_r) if pg_r is not None else 10,
                       'y_': year_, 'compensation': comp_data, 'available_years': available_years})
    return redirect('dashboard')


@login_required(login_url="user_login")
def hr_leave_request(request):
    role = request.user.role
    if role == 'CEO':
        leave_application = HolidayRequest.objects.filter((Q(user__role='HR'))).order_by('-id')

        return render(request, 'dashboard/hr_leave_request.html',
                      {'role': role, 'leave_application': leave_application})
    return redirect('dashboard')


@login_required(login_url="user_login")
def my_profile(request):
    role = request.user.role
    # if role != "ADMIN" :
    if role == 'EMPLOYEE' or 'MANAGER' or 'INTERN':

        if request.method == 'GET':
            user = request.user.name
            email = request.user.email
            designation = request.user.designation
            doj = request.user.doj
            dob = request.user.dob
            photo = request.user.profile_pic

            return render(request, 'dashboard/my_profile.html',
                          {'user': user, 'email': email, 'role': designation, 'doj': doj, 'dob': dob,
                           'profile_pic': photo})


@login_required(login_url="user_login")
def organisationchart(request):
    role = request.user.role
    if role == 'MANAGER':
        print(request.user.report_to)
        report_consultant = User.objects.filter(Q(report_to=request.user.id))
        print(report_consultant)
        admin = {}
        ceo = {}
        con = {}
        user_ = []
        manager_ = []
        con['name'] = request.user.role
        con['title'] = request.user.name
        con['className'] = request.user.designation
        photo = request.user.profile_pic
        print(photo)
        if photo:
            con['avatar'] = request.build_absolute_uri(f"/media/{photo}")
        elif request.user.role == "male":
            con['avatar'] = request.build_absolute_uri(f'/static/images/men.png')
        else:
            con['avatar'] = request.build_absolute_uri(f'/static/images/women.png')

        for i in report_consultant:
            children = []
            man = {}
            man['name'] = i.role
            man['title'] = i.name
            man['className'] = i.role
            if i.profile_pic:
                man['avatar'] = f"/media/{i.profile_pic} "
            elif request.user.gender.lower() == "male":
                man['avatar'] = request.build_absolute_uri(f'/static/images/men.png')
            else:
                man['avatar'] = request.build_absolute_uri(f'/static/images/women.png')
            print(f'mAN{man}')

            for child in User.objects.filter(report_to=i.id):
                if child.profile_pic:
                    childs = request.build_absolute_uri(f"/media/{child.profile_pic}")
                elif request.user.gender.lower() == "male":
                    childs = request.build_absolute_uri(f'/static/images/men.png')
                else:
                    childs = request.build_absolute_uri(f'/static/images/women.png')
                children.append(dict(name=child.role, title=child.name, className=child.role, avatar=childs))
            if len(children) != 0:
                man.update({"children": children})
                manager_.append(man)
            else:
                manager_.append(man)

        con.update({"children": manager_})
        print(con)
        return render(request, 'dashboard/organization_chart.html', context=dict(user_org=con))

    elif role == 'CEO':
        ceo = {}
        report_consultant = User.objects.filter(role="Manager")
        r = User.objects.filter(role="Employee")
        print(r)

        manager_ = []
        user_ = []
        ceo['name'] = request.user.role
        ceo['title'] = request.user.name
        ceo['className'] = request.user.role
        photo = request.user.profile_pic
        print(photo)
        if photo:
            ceo['avatar'] = request.build_absolute_uri(f"/media/{photo}")
        elif request.user.gender.lower() == "male":
            ceo['avatar'] = request.build_absolute_uri(f'/static/images/men.png')
        else:
            ceo['avatar'] = request.build_absolute_uri(f'/static/images/women.png')
        for i in report_consultant:
            children = []
            interns = []
            emp = []
            man = {}
            man['name'] = i.role
            man['title'] = i.name
            man['className'] = i.role
            if i.profile_pic:
                man['avatar'] = f"/media/{i.profile_pic}"
            elif request.user.gender.lower() == "male":
                man['avatar'] = request.build_absolute_uri(f'/static/images/men.png')
            else:
                man['avatar'] = request.build_absolute_uri(f'/static/images/women.png')
            print(f'mAN{man}')

            for child in User.objects.filter(report_to=i.id):
                if child.profile_pic:
                    childs = f"/media/{i.profile_pic} "
                elif request.user.gender.lower() == "male":
                    childs = request.build_absolute_uri(f'/static/images/men.png')
                else:
                    childs = request.build_absolute_uri(f'/static/images/women.png')

                if User.objects.filter(report_to=child.id).count() > 0:
                    for usr in User.objects.filter(report_to=child.id):
                        get_user = User.objects.get(id=usr.id)
                        if get_user.profile_pic:
                            childs = request.build_absolute_uri(f"/media/{get_user.profile_pic} ")
                        elif request.user.gender.lower() == "male":
                            childs = request.build_absolute_uri(f'/static/images/men.png')
                        else:
                            childs = request.build_absolute_uri(f'/static/images/women.png')
                        interns.append(
                            dict(name=get_user.role, title=get_user.name, className=get_user.role, avatar=childs))
                    children.append(
                        dict(name=child.role, title=child.name, className=child.role, avatar=childs, children=interns))
                    interns = []
                else:
                    children.append(dict(name=child.role, title=child.name, className=child.role, avatar=childs))
            if len(children) != 0:
                man.update({"children": children})
                manager_.append(man)
            else:
                manager_.append(man)
        ceo.update({"children": manager_})
        print(f'printtttt{ceo}')

        print(ceo)
        return render(request, 'dashboard/organization_chart.html', context=dict(user_org=ceo))
    else:
        user_get = User.objects.get(id=request.user.id)
        print(user_get)
        report_consultant = User.objects.filter(Q(report_to=request.user.report_to) | Q(id=request.user.id))
    try:
        report_get = User.objects.get(id=request.user.report_to)
        print(report_get)
        admin = {}
        con = {}
        man = {}
        manager_ = []

        user_ = []
        con['name'] = report_get.role
        print(con['name'])
        con['title'] = report_get.name
        print(con['title'])
        con['className'] = report_get.designation
        photo = report_get.profile_pic
        if photo:
            con['avatar'] = request.build_absolute_uri(f"/media/{photo}")
        elif report_get.gender.lower() == "male":
            con['avatar'] = request.build_absolute_uri(f'/static/images/men.png')
        else:
            con['avatar'] = request.build_absolute_uri(f'/static/images/women.png')

        for i in report_consultant:
            children = []
            man = {}
            man['name'] = i.role
            man['title'] = i.name
            man['className'] = i.role
            if i.profile_pic:
                man['avatar'] = request.build_absolute_uri(f"/media/{i.profile_pic}")
            elif i.gender.lower() == "male":
                man['avatar'] = request.build_absolute_uri(f'/static/images/men.png')
            else:
                man['avatar'] = request.build_absolute_uri(f'/static/images/women.png')
            print(f'mAN{man}')

            for child in User.objects.filter(report_to=i.id):
                if child.profile_pic:
                    childs = request.build_absolute_uri(f"/media/{child.profile_pic}")
                elif child.gender.lower() == "male":
                    childs = request.build_absolute_uri(f'/static/images/men.png')
                else:
                    childs = request.build_absolute_uri(f'/static/images/women.png')
                children.append(dict(name=child.role, title=child.name, className=child.role, avatar=childs))
            if len(children) != 0:
                man.update({"children": children})
                manager_.append(man)
            else:
                manager_.append(man)

        con.update({"children": manager_})
        print(con)
        return render(request, 'dashboard/organization_chart.html', context=dict(user_org=con))


    except User.DoesNotExist:
        return HttpResponse('Invalid request')




@login_required(login_url="user_login")
def addressdetails(request):
    print(request.POST)
    if request.method == 'GET':
        user1 = request.user.name
        id = request.user.employee_id
        print(id)
        add1 = request.user.per_address1
        add2 = request.user.per_address2
        add3 = request.user.tem_address1
        add4 = request.user.tem_address2
        city = request.user.per_city
        city2 = request.user.tem_city
        state = request.user.per_state
        state2 = request.user.tem_state
        country = request.user.per_country
        country2 = request.user.tem_country
        pincode = request.user.per_pincode
        pincode2 = request.user.tem_pincode
        per_phone_number = request.user.per_phone_number
        tem_phone_number = request.user.tem_phone_number
        email = request.user.email
        asset = request.user.asset
        computer_brand = request.user.computer_brand
        computer_ram = request.user.computer_ram
        computer_processor = request.user.computer_processor
        print(asset)
        if asset == 'Company Laptop':
            company_laptop = True
        else:
            company_laptop = False

        personal_email = request.user.personal_email
        designation = request.user.designation
        doj = request.user.doj
        dob = request.user.dob

        s_address = request.user.same_as_per_addr
        profile_pic = request.user.profile_pic
        return render(request, 'dashboard/user_details.html',
                      context={'id': id, 'add1': add1, 'add2': add2, 'add3': add3, 'add4': add4, 'city': city,
                               'city2': city2,
                               'email': email, 'phone2': tem_phone_number, 'asset': asset,
                               'company_laptop': company_laptop,
                               'brand': computer_brand,
                               'ram': computer_ram, 'processor': computer_processor,
                               'state': state, 'state2': state2, 'country': country, 'country2': country2,
                               'pincode': pincode, 'pincode2': pincode2, 'profile_pic': profile_pic,
                               'phone1': per_phone_number, 'user': user1, 'personal_email': personal_email,
                               'designation': designation, 'doj': doj, 'dob': dob, 'same_as_per_addr': s_address,
                               })
    else:
        if request.method == 'POST':
            data = User.objects.get(id=request.user.id)
            # print(f'hiiiiii{data}')
            data.per_address1 = request.POST.get('add1')
            data.per_address2 = request.POST.get('add2')
            data.per_city = request.POST.get('city')
            data.per_state = request.POST.get('state')
            data.per_country = request.POST.get('country')
            data.per_pincode = request.POST.get('pincode')
            data.per_phone_number = request.POST.get('phone')
            data.tem_address1 = request.POST.get('add3')
            data.tem_address2 = request.POST.get('add4')
            data.tem_city = request.POST.get('city2')
            data.tem_state = request.POST.get('state2')
            data.tem_country = request.POST.get('country2')
            data.tem_pincode = request.POST.get('pincode2')
            data.tem_phone_number = request.POST.get('phone2')
            data.personal_email = request.POST.get('personal_email')

            data.same_as_per_addr = True if request.POST.get('same_as_pa') == 'on' else False
            data.asset = request.POST.get('asset')

            data.computer_brand = request.POST.get('brand')
            data.computer_ram = request.POST.get('ram')
            data.computer_processor = request.POST.get('processor')
            data.profile_pic = request.FILES.get('profile_pic')
            print(data.profile_pic)

            data.save()
            messages.success(request, "data stored sucessfully")
            return redirect('address')
        return render(request, 'dashboard/user_details.html')


class HelpDeskView(View):
    def get(self, request):
        return render(request, 'dashboard/help_desk.html')

    def post(self, request):
        print(request.POST)
        help_desk = HelpDesk.objects.create(user=request.user, category=request.POST.get('category'),
                                            description=request.POST.get('description'),
                                            attachment=request.FILES.get('attachment'))
        email = EmailMessage(
            subject=f"New {help_desk.category} Query from {request.user.email}",
            body=help_desk.description,

            to=["hr@prowesstics.com"],
            cc=["jerson.antony@prowesstics.com", "mohana.priya@prowesstics.com"],

        )
        email.content_subtype = "html"
        file = help_desk.attachment
        print(help_desk.attachment)
        if file == None:

            print(file)
            email.send()
        else:
            email.attach(file.name, file.read())
            email.send()

        sweetify.success(request, 'Success', text='Mail Send Successfully',
                         persistent='Ok')
        return render(request, 'dashboard/help_desk.html')


class HelpDisk_Tickets(View):
    def get(self, request):
        role = request.user.role
        if role == 'HR':
            help = HelpDesk.objects.filter(ticket_solved=False).order_by('-pk')
            paginator = Paginator(help, 10)
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

            return render(request, 'dashboard/tickets.html', {'help': pages, 'role': request.user.role})

        if role in ['EMPLOYEE', "MANAGER", 'INTERN']:
            help = HelpDesk.objects.filter(user_id=request.user.id)
            paginator = Paginator(help, 10)
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
            print(help)
            return render(request, 'dashboard/tickets.html', {'help': pages, 'role': request.user.role})


class HelpDisk_Tickets_Closed(View):
    def get(self, request):
        role = request.user.role
        if role == 'HR':
            help = HelpDesk.objects.filter(ticket_solved=True).order_by('-pk')
            paginator = Paginator(help, 10)
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

            return render(request, 'dashboard/ticket_close.html', {'help': pages, 'role': request.user.role})


class Ticket_Viewer(View):
    def get(self, request):

        role = request.user.role
        if role == 'HR':
            id = request.GET.get('id')
            request.session['id'] = id
            print(id)
            ticket = HelpDesk.objects.get(id=id)
            print(ticket, 'dddeeeee')
            x = ticket.attachment
            print(x, 'sss')
            if x == '':
                ty = None
                context = {'name': ticket.user.name, 'category': ticket.category, 'description': ticket.description,
                           'attachment': request.build_absolute_uri(f'/static/images/unattachment.png'), 'ty': ty,
                           'ticket_solved': ticket.ticket_solved}

            else:
                y = str(x).split(".")[-1]
                print(x, y)
                if y.lower() in ['pdf', 'raw', 'docx', 'pptx', 'xlsx', 'txt', 'xls']:
                    ty = True
                elif y.lower() in ['img', 'jpg', 'png', 'gif', 'jpeg']:
                    ty = False
                # print(ty, 'y')
                context = {'name': ticket.user.name, 'category': ticket.category, 'description': ticket.description,
                           'attachment': ticket.attachment.url, 'ty': ty, 'ticket_solved': ticket.ticket_solved}
                print(context, 'sssssssssd')
            return render(request, 'dashboard/ticket_viewer.html', context)

    def post(self, request):
        id = request.session['id']
        ty = None
        print(id)
        ticket = HelpDesk.objects.get(id=id)
        ticket.ticket_solved = True
        ticket.save()
        ticket = HelpDesk.objects.get(id=id)
        print(ticket, 'dddeeeee')
        x = ticket.attachment
        print(x, 'sss')
        if x == '':
            ty = None
            context = {'name': ticket.user.name, 'category': ticket.category, 'description': ticket.description,
                       'attachment': request.build_absolute_uri(f'/static/images/unattachment.png'), 'ty': ty,
                       'ticket_solved': ticket.ticket_solved}

        else:
            y = str(x).split(".")[-1]
            print(x, y)
            if y.lower() in ['pdf', 'raw', 'docx', 'pptx', 'xlsx', 'txt', 'xls']:
                ty = True
            elif y.lower() in ['img', 'jpg', 'png', 'gif', 'jpeg']:
                ty = False
            # print(ty, 'y')
            context = {'name': ticket.user.name, 'category': ticket.category, 'description': ticket.description,
                       'attachment': ticket.attachment.url, 'ty': ty, 'ticket_solved': ticket.ticket_solved}
            print(context, 'sssssssssd')
        return render(request, 'dashboard/ticket_viewer.html', context)




def monday_holiday_check(m_date):
    if m_date.weekday() == 0:
        try:
            HolidayCalender.objects.get(date=m_date)
            return True
        except HolidayCalender.DoesNotExist:
            return False


def monday_date_fun(id, todays):
    id = id

    prev_friday = todays + REL.relativedelta(weekday=REL.FR(-1))
    prev_monday = todays + REL.relativedelta(days=-1, weekday=REL.MO(-1))
    next_monday = todays + datetime.timedelta(days=-todays.weekday(), weeks=1)
    this_monday = todays - datetime.timedelta(days=todays.weekday())
    print(f'prev_monday{prev_monday} prev_friday{prev_friday}')

    today = datetime.date.today()
    date1 = today.strftime('%Y-%m-%d')
    date2 = next_monday.strftime('%Y-%m-%d')
    # sheet = Timesheet.objects.filter(user_id=id,date__gte=this_monday, date__lte=next_monday).order_by('date')

    return prev_monday, prev_friday, date1, date2


@login_required(login_url="user_login")
def timesheet(request):
    role = request.user.role
    if role == 'MANAGER' or role == 'EMPLOYEE' or role == "INTERN":
        if request.method == 'GET':
            stop_time = "13:01 PM"
            now = datetime.datetime.now().strftime("%H:%M %p")
            todays = datetime.date.today()
            yesterday = todays - datetime.timedelta(days=1)
            monday_holi = monday_holiday_check(todays)

            x = todays.isoweekday() == 2
            y = 1
            if x:
                try:
                    HolidayCalender.objects.get(date=yesterday)
                    y = 2
                    todays = yesterday
                except HolidayCalender.DoesNotExist:
                    y = 1
            if monday_holi:
                id = request.user.id

                prev_monday, prev_friday, date1, date2 = monday_date_fun(id, todays)
                task = Project.objects.all()
                sheets = Timesheet.objects.filter(Q(user_id=id, date__gte=prev_monday, date__lte=prev_friday)
                                                  | Q(user_id=id, access=True)).order_by('date')

                return render(request, 'dashboard/timesheet.html',
                              context=dict(task=task, sheets=sheets, date=date1, end=date2))
            if datetime.date.today().isoweekday() == y and now <= stop_time:
                id = request.user.id

                prev_monday, prev_friday, date1, date2 = monday_date_fun(id, todays)
                task = Project.objects.all()
                sheets = Timesheet.objects.filter(Q(user_id=id, date__gte=prev_monday, date__lte=prev_friday)
                                                  | Q(user_id=id, access=True)).order_by('date')

                return render(request, 'dashboard/timesheet.html',
                              context=dict(task=task, sheets=sheets, date=date1, end=date2))
            else:
                id = request.user.id
                today = datetime.date.today()
                date1 = today.strftime('%Y-%m-%d')
                # print(date1)
                next_monday = today + datetime.timedelta(days=-today.weekday(), weeks=1)
                this_monday = today - datetime.timedelta(days=today.weekday())
                print(f'sunday{this_monday} monday{next_monday}')
                date2 = next_monday.strftime('%Y-%m-%d')
                # print(f'{this_monday}ffffffffff{next_monday}')
                x = datetime.datetime.now() + datetime.timedelta(days=7)
                # print(x.strftime('%Y-%m-%d'))
                task = Project.objects.all()

                # sheet = Timesheet.objects.filter(user_id=id,date__gte=this_monday, date__lte=next_monday).order_by('date')
                sheets = Timesheet.objects.filter(Q(user_id=id, date__gte=this_monday, date__lte=next_monday)
                                                  | Q(user_id=id, access=True)).order_by('date')
                print(sheets)
                return render(request, 'dashboard/timesheet.html',
                              context=dict(task=task, sheets=sheets, date=date1, end=date2))

        else:
            if request.method == 'POST':
                today = datetime.date.today()
                holiday = HolidayCalender.objects.filter(date=today).exists()

                # if datetime.date.today().isoweekday() == 6 or datetime.date.today().isoweekday() == 7 or holiday:
                #     sweetify.success(request,'Holiday',text='Cannot enter for weekends days')
                # else:

                today = datetime.date.today()
                user = request.user
                # print(user)
                project = request.POST.get('project')
                # print(project)
                if project == 'Others' or project == 'none':
                    project_name = 'Others'
                else:
                    get_project = Project.objects.get(id=project)
                    # print(pro)
                    project_name = get_project.project_name
                manager = request.POST.get('manager')
                # tdate=request.POST.get('todaydate')
                stime = request.POST.get('stime')
                etime = request.POST.get('etime')
                status = request.POST.get('status')
                logged_hours = request.POST.get('logg')
                print(f'{project},{manager},{stime},{etime},{status}')
                # start_dt = datetime.datetime.strptime(stime, '%H:%M')
                # end_dt = datetime.datetime.strptime(etime, '%H:%M')
                # diff = (end_dt - start_dt)
                # a=diff.seconds / 60
                # print(diff,a)
                if Timesheet.objects.filter(date=today, user=user).exists():
                    sweetify.success(request, 'Failed', text='This Date  already exist ',
                                     persistent='Ok')
                else:
                    time = Timesheet.objects.create(user=user, project=project_name, project_manager=manager,
                                                    start_time=stime,
                                                    end_time=etime,
                                                    status=status, logged_hours=logged_hours, date=today)
                    sweetify.success(request, 'Success', text='Timesheet Added Successfully',
                                     persistent='Ok')
                return redirect('timesheet')

            return render(request, 'dashboard/timesheet.html')
    else:
        return render(request, 'account/404.html', status=404)


''' good approch for timesheet need to be tested '''




def edit_timesheet_(request):
    if request.method == 'POST':
        id = request.GET.get('id')
        print(id)
        project = request.POST.get('project')
        print(project)
        if project == 'Others' or project == 'none':
            project_name = 'Others'
        else:
            get_project = Project.objects.get(id=project)
            # print(pro)
            project_name = get_project.project_name
        manager = request.POST.get('manager')
        date = request.POST.get('todaydate')
        print(date, 'printtttt')
        stime = request.POST.get('stime')
        etime = request.POST.get('etime')
        status = request.POST.get('status')
        logged_hours = request.POST.get('logg')
        print(id, project, manager, date, stime, etime, status)
        auto = AutoDetectCasualLeave.objects.filter(user=request.user, created_date=date)

        for l in auto:
            if l.leave_type == 'casualleave':
                print('normal')
                h = UserHoliday.objects.filter(user=request.user, year=current_year())
                print(h, 'hai')
                for i in h:
                    i.casual_leave -= 1
                    i.save()
                    print(i.casual_leave_allowed)
                    AutoDetectCasualLeave.objects.filter(user=request.user, created_date=date).delete()
                    Notification.objects.filter(user=request.user, notification_type='AUTO_CASUAL',
                                                date_created=date).delete()

            elif l.leave_type == 'sickleave':
                print('normal')
                h = UserHoliday.objects.filter(user=request.user, year=current_year())
                print(h, 'hai')
                for i in h:
                    i.sick_leave -= 1
                    i.save()
                    print(i.casual_leave_allowed)
                    AutoDetectCasualLeave.objects.filter(user=request.user, created_date=date).delete()
                    Notification.objects.filter(user=request.user, notification_type='AUTO_SICK',
                                                date_created=date).delete()

            elif l.leave_type == 'lopleave':
                print('lopd')
                h = UserHoliday.objects.filter(user=request.user, year=current_year())
                print(h, 'hai')
                for i in h:
                    i.lop -= 1
                    i.save()
                    print(i.casual_leave_allowed)
                    AutoDetectCasualLeave.objects.filter(user=request.user, created_date=date).delete()
                    Notification.objects.filter(user=request.user, notification_type='LOP_TIMESHEET',
                                                date_created=date).delete()

        time = Timesheet.objects.get(id=id)
        time.project = project_name
        print(time.project)
        time.project_manager = manager
        time.date = date
        time.start_time = stime
        time.end_time = etime
        time.status = status
        time.logged_hours = logged_hours
        time.access = False
        time.save()
        Notification.objects.filter(user=request.user, notification_type='REMINDER', date_created=date).delete()

    return redirect('timesheet')


'''other approach need to be tested'''




'''get_manager is an ajax views to get a manger from project name'''


def get_manager(request):
    if request.method == "POST":
        subject_id = request.POST.get('subject_id')
        if subject_id == 'Others':
            manager = 'Others'
        else:
            subject = Project.objects.get(id=subject_id)
            manager = subject.project_manager.name
        return JsonResponse({'manager': manager})


# @csrf_exempt
def edit_timesheet_ajax(request):
    if request.method == "POST":
        id = request.POST['id']
        print(f'gggggg{id}')
        time = Timesheet.objects.get(id=id)
        print(time.project)
        try:
            if time.project == 'Others':
                project_id = 0

            else:
                project = Project.objects.get(project_name=time.project)
                project_id = project.id
        except Project.DoesNotExist:
            pass
        return HttpResponse(json.dumps(
            dict(id=id, manager=time.project_manager, p=time.project, project=project_id, stime=time.start_time,
                 etime=time.end_time, date=str(time.date), logg=time.logged_hours
                 , status=time.status)), content_type="application/json")


@login_required(login_url="user_login")
def hr_timesheet_dashboard(request):
    role = request.user.role
    pg_r = request.GET.get('pg_r', 10)

    if role == 'HR':
        user_list = User.objects.filter(admin=False).exclude(Q(role='HR') | Q(role='CEO')).order_by('name')
    elif role == 'MANAGER':
        user_list = User.objects.filter(report_to=request.user.id, admin=False).order_by('name').exclude(role='HR')
    elif role == 'EMPLOYEE':
        user_list = User.objects.filter(report_to=request.user.id, admin=False).order_by('name').exclude(role='HR')
    else:
        return render(request, 'account/404.html', status=404)

    paginator = Paginator(user_list, int(pg_r))
    pages = paginator.get_page(request.GET.get('page'))

    return render(request, 'dashboard/hr_timesheet.html', {'role': role, 'users': pages, 'pg_r': int(pg_r)})


@login_required(login_url="user_login")
def hr_timesheet_viewer(request):
    role = request.user.role
    print(role)
    id = request.GET.get('id')
    print(id)
    if role == 'HR':
        if request.method == 'GET':

            today = date.today()
            last_monday = today - datetime.timedelta(days=today.weekday())
            next_monday = today + datetime.timedelta(days=-today.weekday(), weeks=1)
            users = User.objects.filter(id=id)[0]
            page = request.GET.get('page', 1)
            from_date = request.GET.get('from')
            to_date = request.GET.get('to')
            print(f'{last_monday},{next_monday}===========')
            if page == 1:
                get_user = Timesheet.objects.filter(Q(user_id=id, date__gte=last_monday, date__lte=next_monday)
                                                    | Q(user_id=id, access=True)).order_by('date')
            else:
                get_user = Timesheet.objects.filter(user_id=id, date__gte=from_date, date__lte=to_date).order_by('date')

            print(get_user)
            dates = date_range(last_monday, next_monday)
            print(dates)
            current_week = []
            for week in get_user:
                print(week.logged_hours, 'loooooooooooooooooooooo')
                if week.date in dates:
                    current_week.append(dict(id=week.id, project=week.project, project_manager=week.project_manager
                                             , start_time=week.start_time, end_time=week.end_time, date=week.date,
                                             status=week.status, logged_hours=week.logged_hours, c_week=True,
                                             access=week.access))
                    print(f'sssssssssss{current_week}')
                else:
                    current_week.append(dict(id=week.id, project=week.project, project_manager=week.project_manager
                                             , start_time=week.start_time, end_time=week.end_time, date=week.date,
                                             status=week.status, c_week=False, access=week.access,
                                             logged_hours=week.logged_hours))
                    print(f'1111111111111111111111sssssssssss{current_week}')
            print(current_week)
            paginator = Paginator(current_week, page)
            print(paginator)

            paginator = Paginator(current_week, 10)
            try:
                pages = paginator.page(page)
                print(f'h1{pages}')
            except PageNotAnInteger:
                pages = paginator.page(1)
                # print(f'h2{pages}')
            except EmptyPage:
                pages = paginator.page(paginator.num_pages)
            print(current_week)
            return render(request, 'dashboard/hr_timesheet_viewer.html',
                          context=dict(user=pages, id=id, f=from_date, t=to_date, users=users))
        if request.method == 'POST':
            from_date = request.GET.get('from')
            to_date = request.GET.get('to')
            give_access = request.POST.get("yes")

            # revok=request.POST.get("ryes")
            timesheet_id = request.GET.get('time_id')
            users = User.objects.filter(id=id)[0]

            print(f'dddd{timesheet_id}')
            # if revok is not None:
            #     print(give_access, timesheet_id)
            #     user = Timesheet.objects.filter(id=timesheet_id).update(access=False)
            #     print(user)
            #     today = datetime.date.today()
            #     next_sunday = today - datetime.timedelta(days=today.weekday())
            #
            #     next_monday = today + datetime.timedelta(days=-today.weekday(), weeks=1)
            #
            #     get_user = Timesheet.objects.filter(Q(user_id=id, date__gte=next_sunday, date__lte=next_monday)
            #                                         | Q(access=True)).order_by('date')
            #     dates = date_range(next_sunday, next_monday)
            #     current_week = []
            #     for week in get_user:
            #         if week.date in dates:
            #             current_week.append(dict(id=week.id, project=week.project, project_manager=week.project_manager
            #                                      , start_time=week.start_time, end_time=week.end_time, date=week.date,
            #                                      status=week.status, c_week=True, access=week.access))
            #         else:
            #             current_week.append(dict(id=week.id, project=week.project, project_manager=week.project_manager
            #                                      , start_time=week.start_time, end_time=week.end_time, date=week.date,
            #                                      status=week.status, c_week=False, access=week.access))
            #     print(current_week)
            #     return render(request, 'dashboard/hr_timesheet_viewer.html', context=dict(user=current_week, id=id))

            if give_access is not None:
                print(give_access, 'ss')
                print(give_access, timesheet_id)
                user = Timesheet.objects.filter(id=timesheet_id).update(access=True)
                print(user)
                today = datetime.date.today()
                next_sunday = today - datetime.timedelta(days=today.weekday())

                next_monday = today + datetime.timedelta(days=-today.weekday(), weeks=1)

                # get_user = Timesheet.objects.filter(Q(user_id=id, date__gte=next_sunday, date__lte=next_monday)
                #                                     | Q(access=True)).order_by('date')
                get_user = Timesheet.objects.filter(Q(user_id=id, date__gte=from_date, date__lte=to_date)
                                                    | Q(access=True)).order_by('date')
                dates = date_range(next_sunday, next_monday)
                current_week = []
                for week in get_user:
                    if week.date in dates:
                        current_week.append(dict(id=week.id, project=week.project, project_manager=week.project_manager
                                                 , start_time=week.start_time, end_time=week.end_time, date=week.date,
                                                 status=week.status, c_week=True, access=week.access,
                                                 logged_hours=week.logged_hours))
                    else:
                        current_week.append(dict(id=week.id, project=week.project, project_manager=week.project_manager
                                                 , start_time=week.start_time, end_time=week.end_time, date=week.date,
                                                 status=week.status, c_week=False, access=week.access,
                                                 logged_hours=week.logged_hours))
                print(current_week)
                return render(request, 'dashboard/hr_timesheet_viewer.html',
                              context=dict(user=current_week, id=id, users=users, f=from_date, t=to_date, ))


            else:

                from_date = request.POST.get('fdate')
                to_date = request.POST.get('todate')
                users = User.objects.filter(id=id)[0]

                print(f'{from_date}{to_date}')
                # from1 = datetime.datetime.strptime(from_date, "%Y-%m-%d").strftime("%Y-%m-%d")
                # to1=  datetime.datetime.strptime(to_date, "%Y-%m-%d").strftime("%Y-%m-%d")
                # print(from1,to1)
                today = datetime.date.today()
                try:
                    get_user = Timesheet.objects.filter(user_id=id, date__gte=from_date, date__lte=to_date).order_by(
                        'date')
                except ValueError:
                    # sweetify.success(request, 'Select User', text='Select User From Timesheet-Dashboard')

                    get_user = Timesheet.objects.filter(user_id=0, date__gte=from_date, date__lte=to_date).order_by(
                        'date')
                next_sunday = today - datetime.timedelta(days=today.weekday())

                next_monday = today + datetime.timedelta(days=-today.weekday(), weeks=1)

                dates = date_range(next_sunday, next_monday)
                current_week = []
                for week in get_user:
                    if week.date in dates:
                        current_week.append(dict(id=week.id, project=week.project, project_manager=week.project_manager
                                                 , start_time=week.start_time, end_time=week.end_time, date=week.date,
                                                 status=week.status, c_week=True, access=week.access,
                                                 logged_hours=week.logged_hours))
                    else:
                        current_week.append(dict(id=week.id, project=week.project, project_manager=week.project_manager
                                                 , start_time=week.start_time, end_time=week.end_time, date=week.date,
                                                 status=week.status, c_week=False, access=week.access,
                                                 logged_hours=week.logged_hours))
                print(current_week)
                pg_r = request.GET.get('pg_r', None)
                pg_r = int(pg_r) if pg_r is not None else 10
                print(pg_r)
                page = request.GET.get('page')
                print('page', page)
                paginator = Paginator(current_week, int(pg_r))
                print(paginator)
                paginator = Paginator(current_week, 10)
                try:
                    pages = paginator.page(page)
                    print(f'h1{pages}')
                except PageNotAnInteger:
                    pages = paginator.page(1)
                    # print(f'h2{pages}')
                except EmptyPage:
                    pages = paginator.page(paginator.num_pages)
                return render(request, 'dashboard/hr_timesheet_viewer.html',
                              context=dict(id=id, user=pages, f=from_date, t=to_date, users=users))

    if role == 'MANAGER':
        if request.method == 'GET':
            page = request.GET.get('page', 1)
            from_date = request.GET.get('from')
            to_date = request.GET.get('to')
            print(page, 'sssssssssssssssssssssssssssssssssssssssssssss', from_date, to_date)
            today = datetime.date.today()

            next_monday = today + datetime.timedelta(days=-today.weekday(), weeks=1)
            next_sunday = today - datetime.timedelta(days=today.weekday())
            print(f'{today},{next_monday}===========')
            if page == 1:
                get_user = Timesheet.objects.filter(user_id=id).order_by(
                    '-date').exclude(status='DetailsNone')[0:10]
            else:
                get_user = Timesheet.objects.filter(user_id=id).order_by('date').exclude(status='DetailsNone')
            users = User.objects.filter(id=id)[0]
            # if pg_r is not None:

            paginator = Paginator(get_user, page)
            print(paginator)

            paginator = Paginator(get_user, 10)
            try:
                pages = paginator.page(page)
                print(f'h1{pages}')
            except PageNotAnInteger:
                pages = paginator.page(1)
                # print(f'h2{pages}')
            except EmptyPage:
                pages = paginator.page(paginator.num_pages)
            print(get_user)

            return render(request, 'dashboard/manager_timesheet_viewer.html',
                          context=dict(user=pages, id=id, f=from_date, t=to_date, users=users))
        if request.method == 'POST':
            from_date = request.POST.get('fdate')
            to_date = request.POST.get('todate')
            users = User.objects.filter(id=id)[0]

            # from1 = datetime.datetime.strptime(from_date, "%Y-%m-%d").strftime("%Y-%m-%d")
            # to1 = datetime.datetime.strptime(to_date, "%Y-%m-%d").strftime("%Y-%m-%d")
            # get_user1=Timesheet.objects.filter(id=id)
            try:
                get_user = Timesheet.objects.filter(user_id=id, date__gte=from_date, date__lte=to_date).order_by(
                    'date').exclude(status='DetailsNone')
                print(get_user)
            except ValueError:
                # sweetify.success(request, 'Select User', text='Select User From Timesheet-Dashboard')

                get_user = Timesheet.objects.filter(user_id=0, date__gte=from_date, date__lte=to_date).order_by(
                    'date').exclude(status='DetailsNone')

            pg_r = request.GET.get('pg_r', None)
            pg_r = int(pg_r) if pg_r is not None else 10
            print(pg_r)
            page = request.GET.get('page')
            print('page', page)
            paginator = Paginator(get_user, int(pg_r))
            print(paginator)
            paginator = Paginator(get_user, 10)
            try:
                pages = paginator.page(page)
                print(f'h1{pages}')
            except PageNotAnInteger:
                pages = paginator.page(1)
                # print(f'h2{pages}')
            except EmptyPage:
                pages = paginator.page(paginator.num_pages)
            print(get_user)
            return render(request, 'dashboard/manager_timesheet_viewer.html',
                          context=dict(id=id, user=pages, f=from_date, t=to_date, users=users))
    if role == 'EMPLOYEE':
        if request.method == 'GET':
            page = request.GET.get('page', 1)
            from_date = request.GET.get('from')
            to_date = request.GET.get('to')
            print(page, 'sssssssssssssssssssssssssssssssssssssssssssss', from_date, to_date)
            today = datetime.date.today()

            next_monday = today + datetime.timedelta(days=-today.weekday(), weeks=1)
            next_sunday = today - datetime.timedelta(days=today.weekday())
            print(f'{today},{next_monday}===========')
            if page == 1:
                get_user = Timesheet.objects.filter(user_id=id).order_by(
                    '-date').exclude(status='DetailsNone')[0:10]
            else:
                get_user = Timesheet.objects.filter(user_id=id).order_by('date').exclude(status='DetailsNone')
            users = User.objects.filter(id=id)[0]
            # if pg_r is not None:

            paginator = Paginator(get_user, page)
            print(paginator)

            paginator = Paginator(get_user, 10)
            try:
                pages = paginator.page(page)
                print(f'h1{pages}')
            except PageNotAnInteger:
                pages = paginator.page(1)
                # print(f'h2{pages}')
            except EmptyPage:
                pages = paginator.page(paginator.num_pages)
            print(get_user)

            return render(request, 'dashboard/employee_reportto.html',
                          context=dict(user=pages, id=id, f=from_date, t=to_date, users=users))
        if request.method == 'POST':
            from_date = request.POST.get('fdate')
            to_date = request.POST.get('todate')
            users = User.objects.filter(id=id)[0]
            print(from_date, to_date, 'dddddddddddddddddddddddddddddddddddddddddddddddddddddddddd')
            # from1 = datetime.datetime.strptime(from_date, "%Y-%m-%d").strftime("%Y-%m-%d")
            # to1 = datetime.datetime.strptime(to_date, "%Y-%m-%d").strftime("%Y-%m-%d")
            # get_user1=Timesheet.objects.filter(id=id)
            try:
                get_user = Timesheet.objects.filter(user_id=id, date__gte=from_date, date__lte=to_date).order_by(
                    'date').exclude(status='DetailsNone')
                print(get_user)
            except ValueError:
                # sweetify.success(request, 'Select User', text='Select User From Timesheet-Dashboard')

                get_user = Timesheet.objects.filter(user_id=0, date__gte=from_date, date__lte=to_date).order_by(
                    'date').exclude(status='DetailsNone')

            pg_r = request.GET.get('pg_r', None)
            pg_r = int(pg_r) if pg_r is not None else 10
            print(pg_r)
            page = request.GET.get('page')
            print('page', page)
            paginator = Paginator(get_user, int(pg_r))
            print(paginator)
            paginator = Paginator(get_user, 10)
            try:
                pages = paginator.page(page)
                print(f'h1{pages}')
            except PageNotAnInteger:
                pages = paginator.page(1)
                # print(f'h2{pages}')
            except EmptyPage:
                pages = paginator.page(paginator.num_pages)
            print(get_user)
            return render(request, 'dashboard/employee_reportto.html',
                          context=dict(id=id, user=pages, f=from_date, t=to_date, users=users))
    else:
        return render(request, 'account/404.html', status=404)


def export_timesheet(request):
    id = request.GET.get('id')
    if id == 'None':
        id = 0
    f_date1 = request.GET.get('from')
    t_date1 = request.GET.get('to')
    today = date.today()
    print(f_date1, t_date1, 'jeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee')
    next_sunday = today - datetime.timedelta(days=today.weekday())
    next_monday = today + datetime.timedelta(days=-today.weekday(), weeks=1)
    if f_date1 == '' or f_date1 == 'None' or t_date1 == '' or t_date1 == 'None':
        f_date = next_sunday
        t_date = next_monday
    else:

        f_date = f_date1
        t_date = t_date1
    response = HttpResponse(content_type='application/ms-excel')

    response['Content-Disposition'] = 'attachment; filename="timesheet.xls"'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Timesheet')
    # Sheet header, first row
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    columns = ['name', 'project', 'project_manager', 'start_time', 'end_time', 'logged_hours', 'date', 'status']
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)
    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()
    if f_date and t_date:
        if request.user.role == 'HR':
            rows = Timesheet.objects.filter(
                Q(user_id=id, date__gte=f_date, date__lte=t_date) | Q(user_id=id, access=True)).values_list(
                'user__name',
                'project',
                'project_manager',
                'start_time',
                'end_time',
                'logged_hours',
                'date',
                'status').order_by('date')
        else:
            rows = Timesheet.objects.filter(
                user_id=id, date__gte=f_date, date__lte=t_date).values_list('user__name',
                                                                            'project',
                                                                            'project_manager',
                                                                            'start_time',
                                                                            'end_time',
                                                                            'logged_hours',
                                                                            'date',
                                                                            'status').order_by('date')

    else:
        today = date.today()
        next_sunday = today - datetime.timedelta(days=today.weekday())
        next_monday = today + datetime.timedelta(days=-today.weekday(), weeks=1)
        rows = Timesheet.objects.filter(
            Q(user_id=id, date__gte=next_sunday, date__lte=next_monday) | Q(user_id=id, access=True)).values_list(
            'user__name', 'project', 'project_manager', 'start_time', 'end_time', 'logged_hours', 'date', 'status')
        print(rows)

    for row in rows:
        row = list(row)
        row[6] = str(row[6])
        print(row)
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)

    wb.save(response)
    return response


@login_required(login_url="user_login")
def notification_user(request):
    role = request.user.role
    print(role)
    if role == 'HR' or role == 'CEO':
        return render(request, 'account/404.html', status=404)
    else:
        if request.method == 'GET':
            user = request.user
            notify = Notification.objects.filter(user_id=user.id).order_by('-message')[0:10]

            for i in notify:
                if i.seen == False:
                    i.seen = True
                    i.save()

            return render(request, 'dashboard/notification.html', context=dict(notify=notify))


def last_day_of_month(date):
    if date.month == 12:
        return date.replace(day=31)
    return date.replace(month=date.month + 1, day=1) - datetime.timedelta(days=1)


@login_required(login_url="user_login")
def dashboard_charts(request):
    if request.method == 'GET':
        y_axis = []
        x_axis = []
        data = []
        today = datetime.datetime.today()
        id = request.user.id
        first_day = today.replace(day=1)
        last_day = last_day_of_month(today)
        print(first_day, last_day)
        first_day = today.replace(day=1)
        last_day = last_day_of_month(today)
        next_monday = today + datetime.timedelta(days=-today.weekday(), weeks=1)
        this_monday = today - datetime.timedelta(days=today.weekday())
        week_times = Timesheet.objects.filter(user=request.user, date__gte=first_day, date__lte=last_day).order_by(
            'date')
        user_holiday = UserHoliday.objects.get(user_id=id, year=current_year())
        role, leave_applied, lop, leave_pending, casual_leave, sick_leave = get_info(id)
        data = [casual_leave, sick_leave, user_holiday.casual_leave_allowed - casual_leave,
                user_holiday.sick_leave_allowed - sick_leave]
        # This looping is used to remove negative value from data ,because chart don't accept negative int.
        leave = [int(x) for x in data]
        leaves = [(i > 0) * i for i in leave]
        for i in week_times:
            format = datetime.datetime.strptime(str(i.date), "%Y-%m-%d").strftime("%d-%b-%Y")
            y_axis.append(i.logged_hours)
            x_axis.append(format)
        print(x_axis, y_axis, request.user)
        print('casual', casual_leave, 'sick', sick_leave, 'casual taken', leave_applied, 'si', leave_pending)

        return render(request, 'dashboard/charts-dash.html', {'y': y_axis, 'x': x_axis, 'leave': leaves})
    if request.method == 'POST':
        from_date = request.POST.get('fdate')
        to_date = request.POST.get('todate')
        print(from_date, to_date, 'testinggggggggg')
        y_axis = []
        x_axis = []
        data = []
        today = datetime.datetime.today()
        id = request.user.id
        first_day = today.replace(day=1)
        last_day = last_day_of_month(today)
        print(first_day, last_day)

        week_times = Timesheet.objects.filter(user=request.user, date__gte=from_date, date__lte=to_date).order_by(
            'date')
        user_holiday = UserHoliday.objects.get(user_id=id, year=current_year())
        role, leave_applied, lop, leave_pending, casual_leave, sick_leave = get_info(id)
        data = [casual_leave, sick_leave, user_holiday.casual_leave_allowed - casual_leave,
                user_holiday.sick_leave_allowed - sick_leave]
        # This looping is used to remove negative value from data ,because chart don't accept negative int.
        leave = [int(x) for x in data]
        leaves = [(i > 0) * i for i in leave]

        for i in week_times:
            format = datetime.datetime.strptime(str(i.date), "%Y-%m-%d").strftime("%d-%b-%Y")
            y_axis.append(i.logged_hours)
            x_axis.append(format)
        print(x_axis, y_axis, request.user)

        return render(request, 'dashboard/charts-dash.html', {'y': y_axis, 'x': x_axis, 'leave': leaves})


@login_required(login_url="user_login")
def check_timesheet_date(request):
    if request.user.role == 'ADMIN':
        user_holiday_ = False
        start = datetime.datetime.now()
        user = User.objects.filter(admin=False).exclude(Q(role='HR') | Q(role='CEO'))
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        for i in user:
            print(i.id, '--------------------------------------')
            Timesheet.objects.filter(user_id=i.id, access=True).update(access=False)
            holiday = HolidayCalender.objects.filter(date=yesterday).exclude(optional=True).exists()
            time = Timesheet.objects.filter(user_id=i.id, date=yesterday).exists()
            user_holiday = HolidayRequest.objects.filter(user_id=i.id, year=current_year(),
                                                         start_date__month=yesterday.month)
            week = weekend(yesterday)
            for holi in user_holiday:
                print(holi.leaves_sep_v, 'saaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
                if holi.leaves_sep_v is None:
                    user_holiday_ = True
                    pass
                # if halfday leave is applied we need to skip the leave functionality
                elif holi.type == 'half':
                    print(f'halfday leave is available for {i}')
                    user_holiday_ = False
                    pass
                else:
                    leaves = holi.leaves_sep_v
                    my_list = leaves.split(",")
                    print(holi.category, 'holicategory', holi.leaves_sep_v)

                    print('iffffffffffff')
                    if str(yesterday) in my_list and holi.hr_level_approval and holi.manager_level_approval:
                        user_holiday_ = True
                    else:
                        if i.role == 'MANAGER':
                            if str(yesterday) in my_list and not holi.hr_level_approval and holi.manager_level_approval:
                                project_name = 'Others'
                                manager = 'None'
                                stime = 'None'
                                etime = 'None'
                                status = 'Leave '

                                times_leave = Timesheet.objects.create(user_id=i.id, project=project_name,
                                                                       project_manager=manager,
                                                                       start_time=stime,
                                                                       end_time=etime,
                                                                       status=status, date=yesterday)
                                print(times_leave)
                                user_holiday_ = True
                        else:
                            if str(yesterday) in my_list and not holi.hr_level_approval and not holi.manager_level_approval:
                                project_name = 'Others'
                                manager = 'None'
                                stime = 'None'
                                etime = 'None'
                                status = 'Leave '

                                times_leave = Timesheet.objects.create(user_id=i.id, project=project_name,
                                                                       project_manager=manager,
                                                                       start_time=stime,
                                                                       end_time=etime,
                                                                       status=status, date=yesterday)
                                print(times_leave)
                                user_holiday_ = True

            if user_holiday_ or holiday or time or week:
                print('pass')
                pass

            else:
                project_name = 'Others'
                manager = 'None'
                stime = 'None'
                etime = 'None'
                status = 'DetailsNone'

                times = Timesheet.objects.create(user_id=i.id, project=project_name, project_manager=manager,
                                                 start_time=stime,
                                                 end_time=etime,
                                                 status=status, date=yesterday)
                Notification.objects.create(user_id=i.id, notification_type='REMINDER',
                                            message=f' Fill Your Daily Timesheet details for {yesterday} ',
                                            date_created=yesterday)
                print(times, 'tytytyty')
            user_holiday_ = False

        end = datetime.datetime.now()

        Log_Schedulder.objects.create(name=f'Daily Timesheet Logs {yesterday} ', start_time=start, end_time=end)
        return HttpResponse('Daily unfilled  Timesheet Data filled')
    else:
        return render(request, 'dashboard/404.html', status=404)



@login_required(login_url="user_login")
def casual_leave_timesheet(request):
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    t = None
    d = datetime.date.today().isoweekday()
    try:
        x = HolidayCalender.objects.get(date=today)
        if x.date.isoweekday() == 1:
            t = 2
        t = t

        if d == t:
            pass
        else:
            print('Today is not monday ')
            return render(request, 'dashboard/404.html', status=404)


    except HolidayCalender.DoesNotExist:
        try:
            x = HolidayCalender.objects.get(date=yesterday)

            if x.date.isoweekday() == 1:
                t = 2
            t = t
            if d == t:
                print('casual leave run on Tuesday ')
                start = datetime.datetime.now()

                # today = datetime.date.today()
                yesterday = today - datetime.timedelta(days=1)
                next_monday = yesterday - datetime.timedelta(days=yesterday.weekday())
                next_sunday = yesterday - datetime.timedelta(days=-yesterday.weekday(), weeks=1)
                get_user = Timesheet.objects.filter(date__gte=next_sunday, date__lte=next_monday)

                print(get_user)
                dates = date_range2(next_sunday, next_monday)
                for i in get_user:
                    ''' approve is to check whether  approval is given by either Hr or Manager ,if so it return False 
                    and code will pass  to else condition and no leave will be detected  ,if it return True then  code 
                    will execute and leave will be detucted'''
                    approve = LeaveApproval(i.date, i.user.id)
                    # print(i.user,'================================================>', approved)
                    print(i.status, i.date, dates)
                    if str(i.date) in dates:
                        if i.status == 'DetailsNone' and approve.approval():
                            with contextlib.suppress(UserHoliday.DoesNotExist):
                                holiday = UserHoliday.objects.get(user_id=i.user_id, year=current_year())
                                print(holiday)
                                x = i.date
                                if not HolidayCalender.objects.filter(date=i.date).exists() and not weekend(x):
                                    if holiday.casual_leave >= 9 and holiday.sick_leave >= 9:
                                        holiday.lop += 1
                                        Notification.objects.create(user_id=i.user_id,
                                                                    notification_type='LOP_TIMESHEET',
                                                                    message=f'leave have been detected {i.date}',
                                                                    date_created=i.date)

                                        holiday.save()
                                        AutoDetectCasualLeave.objects.create(user_id=i.user_id, created_date=i.date,
                                                                             year=current_year(), casual_logs=1,
                                                                             leave_type='lopleave')
                                    elif holiday.casual_leave >= 9:
                                        holiday.sick_leave += 1
                                        Notification.objects.create(user_id=i.user_id, notification_type='AUTO_SICK',
                                                                    message=f'leave have been detected {i.date}',
                                                                    date_created=i.date)

                                        holiday.save()
                                        AutoDetectCasualLeave.objects.create(user_id=i.user_id, created_date=i.date,
                                                                             year=current_year(), casual_logs=1,
                                                                             leave_type='sickleave')

                                    else:
                                        holiday.casual_leave += 1
                                        Notification.objects.create(user_id=i.user_id, notification_type='AUTO_CASUAL',
                                                                    message=f'leave have been detected {i.date}',
                                                                    date_created=i.date)

                                        holiday.save()

                                        AutoDetectCasualLeave.objects.create(user_id=i.user_id, created_date=i.date,
                                                                             year=current_year(), casual_logs=1,
                                                                             leave_type='casualleave')

                                    # Notification.objects.create(user_id=i.user_id, notification_type='AUTO_CASUAL',
                                    #                             message=f'leave have beeen detected {i.date}')


                        else:
                            print(f'No leave will be deducted {i.user} ')
                end = datetime.datetime.now()

                Log_Schedulder.objects.create(name=f'Casual Logs {today} ', start_time=start, end_time=end)
                return HttpResponse('log created')
            else:
                return render(request, 'dashboard/404.html', status=404)

        except HolidayCalender.DoesNotExist:
            y = datetime.date.today().isoweekday()
            if y == 1:
                print('casual leave ')
                start = datetime.datetime.now()

                today = datetime.date.today()
                yesterday = today - datetime.timedelta(days=1)
                next_monday = today - datetime.timedelta(days=today.weekday())
                next_sunday = today - datetime.timedelta(days=-today.weekday(), weeks=1)
                get_user = Timesheet.objects.filter(date__gte=next_sunday, date__lte=next_monday)

                print('get_user', get_user)
                dates = date_range2(next_sunday, next_monday)
                for i in get_user:
                    ''' approve is to check whether  approval is given by either Hr or Manager ,if so it return False 
                    and code will pass  to else condition and no leave will be detected  ,if it return True then  code 
                    will execute and leave will be detucted'''
                    approve = LeaveApproval(i.date, i.user.id)
                    # print(i.user,'================================================>', approved)
                    print(i.status, i.date, dates)
                    if str(i.date) in dates:
                        if i.status == 'DetailsNone' and approve.approval():
                            with contextlib.suppress(UserHoliday.DoesNotExist):
                                holiday = UserHoliday.objects.get(user_id=i.user_id, year=current_year())
                                print(holiday)
                                x = i.date
                                if not HolidayCalender.objects.filter(date=i.date).exists() and not weekend(x):
                                    if holiday.casual_leave >= 9 and holiday.sick_leave >= 9:
                                        holiday.lop += 1
                                        Notification.objects.create(user_id=i.user_id,
                                                                    notification_type='LOP_TIMESHEET',
                                                                    message=f'leave have been detected {i.date}',
                                                                    date_created=i.date)

                                        holiday.save()
                                        AutoDetectCasualLeave.objects.create(user_id=i.user_id, created_date=i.date,
                                                                             year=current_year(), casual_logs=1,
                                                                             leave_type='lopleave')
                                    elif holiday.casual_leave >= 9:
                                        holiday.sick_leave += 1
                                        Notification.objects.create(user_id=i.user_id, notification_type='AUTO_SICK',
                                                                    message=f'leave have been detected {i.date}',
                                                                    date_created=i.date)

                                        holiday.save()
                                        AutoDetectCasualLeave.objects.create(user_id=i.user_id, created_date=i.date,
                                                                             year=current_year(), casual_logs=1,
                                                                             leave_type='sickleave')

                                    else:
                                        holiday.casual_leave += 1
                                        Notification.objects.create(user_id=i.user_id, notification_type='AUTO_CASUAL',
                                                                    message=f'leave have been detected {i.date}',
                                                                    date_created=i.date)

                                        holiday.save()

                                        AutoDetectCasualLeave.objects.create(user_id=i.user_id, created_date=i.date,
                                                                             year=current_year(), casual_logs=1,
                                                                             leave_type='casualleave')

                                    # Notification.objects.create(user_id=i.user_id, notification_type='AUTO_CASUAL',
                                    #                             message=f'leave have beeen detected {i.date}')


                        else:
                            print(f'No leave will be deducted {i.user} ')
                end = datetime.datetime.now()

                Log_Schedulder.objects.create(name=f'Casual Logs {today} ', start_time=start, end_time=end)
                return HttpResponse('log created dfddd')
            else:
                return render(request, 'dashboard/404.html', status=404)
    else:
        return render(request, 'dashboard/404.html', status=404)


class Myskills(View):
    def get(self, request):
        id = request.user.id
        skill, primary, secondary, pk, primar, second = '', '', None, None, None, None
        try:
            skill = Skill_Sets.objects.get(user_id=request.user.id)
            primary = skill.primary_skill
            secondary = skill.secondary_skil
            pk = skill.pk
            primar, second, pk = skill.primary_skill.split(","), skill.secondary_skil.split(","), skill.pk

        except Skill_Sets.DoesNotExist:
            pass

        return render(request, 'dashboard/my_skillset.html',
                      {'skill': skill, 'primar': primar, 'second': second, 'primary': primary, 'secondary': secondary,
                       'ids': pk})

    def post(self, request):
        id = request.user.id
        primary = request.POST.get('primary')
        secondary = request.POST.get('secondary')
        print(primary, secondary)
        skills = Skill_Sets.objects.filter(user=request.user).exists()
        print('skills', skills)
        if not skills:
            skill = Skill_Sets(user=request.user, primary_skill=primary, secondary_skil=secondary)
            skill.save()
        skill = Skill_Sets.objects.get(user_id=request.user.id)
        primar, second, pk = skill.primary_skill.split(","), skill.secondary_skil.split(","), skill.pk
        # print( skill.primary_skill ,secondary,';;;;;;;;;;;;;;;;;;;;;;')
        return render(request, 'dashboard/my_skillset.html',
                      {'skill': skill, 'primar': primar, 'second': second, 'primary': primary, 'secondary': secondary,
                       'ids': pk})


def my_skill_edit(request):
    if request.method == "POST":
        id = request.GET.get('id')
        primary = request.POST.get('primary_')
        secondary = request.POST.get('secondary_')

        s = Skill_Sets.objects.get(pk=id)
        print(s)
        s.primary_skill = primary
        s.secondary_skil = secondary
        s.save()
        return redirect('my-skill')
    return None




def Convert(a):
    it = iter(a)
    res_dct = dict(zip(it, it))
    return res_dct


class My_Skill_Admin(View):

    def get(self, request):
        if request.user.role == 'CEO' or request.user.role == 'HR':
            user_skill, primary, secondary = [], [], []
            user = User.objects.all()
            for i in user:
                try:
                    skill = Skill_Sets.objects.get(user_id=i.id)
                    if skill.primary_skill is not None:
                        primary.append(skill.primary_skill.split(','))
                        user_skill.append(skill.user.name)
                        user_skill.append(skill.primary_skill.split(','))
                    else:
                        pass
                except Skill_Sets.DoesNotExist:
                    pass
            user_skill_dict = Convert(user_skill)
            new_primary = [element.strip().upper() for innerList in primary for element in innerList]
            str_list = list(filter(None, new_primary))
            skill_count = dict(Counter(str_list))
            sorted_d = dict(sorted(skill_count.items(), key=operator.itemgetter(1), reverse=True))
            keys, values = zip(*sorted_d.items())
            x_axix = list(keys)
            y_axis = list(values)
            all_skill = list(set(str_list))
            # print(all_skill)
            # print(str_list)
            user_skill_dict_copy = copy.deepcopy(user_skill_dict)
            user_skill_dict_copy_upper = {key: [ele.strip().upper() for ele in user_skill_dict_copy[key]] for key in
                                          user_skill_dict_copy}
            skill_tab = {}
            for k in all_skill:
                skill_tab[k] = []
                for l, m in user_skill_dict_copy_upper.items():
                    if k in m:
                        skill_tab[k].append(l)
                        m.remove(k)
            # print(user_skill_dict_copy_upper)
            js_data = json.dumps(skill_tab)
            pa = list(sorted_d.items())
            print(pa, 'aa')
            page_l = request.GET.get('page_l', 1)
            paginator = Paginator(pa, 10)
            try:
                skill_counts = paginator.page(page_l)
            except PageNotAnInteger:
                skill_counts = paginator.page(1)
            except EmptyPage:
                skill_counts = paginator.page(paginator.num_pages)
            print(skill_counts)

            return render(request, 'dashboard/primary_skill_admin.html',
                          {'y': y_axis, 'x': x_axix, 'skill_set': skill_counts, 'skillu': js_data})
        else:
            return render(request, 'dashboard/404.html', status=404)


class Secondary_Skill_Admin(View):
    def get(self, request):
        if request.user.role == 'CEO' or request.user.role == 'HR':
            user_skill, secondary = [], []
            user = User.objects.all()
            for i in user:
                try:
                    skill = Skill_Sets.objects.get(user_id=i.id)
                    if skill.secondary_skil is not None:
                        secondary.append(skill.secondary_skil.split(','))
                        user_skill.append(skill.user.name)
                        user_skill.append(skill.secondary_skil.split(','))
                    else:
                        pass
                except Skill_Sets.DoesNotExist:
                    pass
            user_skill_dict = Convert(user_skill)
            new_secondary = [element.strip().upper() for innerList in secondary for element in innerList]
            str_list = list(filter(None, new_secondary))
            skill_count = dict(Counter(str_list))
            sorted_d = dict(sorted(skill_count.items(), key=operator.itemgetter(1), reverse=True))
            # print(skill_count)
            keys, values = zip(*skill_count.items())
            x_axix = list(keys)
            y_axis = list(values)
            all_skill = list(set(str_list))
            # print(all_skill)
            # print(str_list)
            user_skill_dict_copy = copy.deepcopy(user_skill_dict)
            user_skill_dict_copy_upper = {key: [ele.strip().upper() for ele in user_skill_dict_copy[key]] for key in
                                          user_skill_dict_copy}
            skill_tab = {}
            for k in all_skill:
                skill_tab[k] = []
                for l, m in user_skill_dict_copy_upper.items():
                    if k in m:
                        skill_tab[k].append(l)
                        m.remove(k)
            # print(user_skill_dict_copy_upper)
            js_data = json.dumps(skill_tab)
            pa = list(sorted_d.items())
            page_l = request.GET.get('page_l', 1)
            paginator = Paginator(pa, 10)
            try:
                skill_counts = paginator.page(page_l)
            except PageNotAnInteger:
                skill_counts = paginator.page(1)
            except EmptyPage:
                skill_counts = paginator.page(paginator.num_pages)
            print(skill_counts)
            return render(request, 'dashboard/Secondary_skill_admin.html',
                          {'y': y_axis, 'x': x_axix, 'skill_set': skill_counts, 'skillu': js_data})
        else:
            return render(request, 'dashboard/404.html', status=404)


class Hr_Skill_Table(View):
    def get(self, request):
        if request.user.role == 'HR':
            name, primary, secondary, sk = {}, {}, [], []
            user = User.objects.all()
            user_list = []
            for i in user:
                try:
                    user_lists = [i.name, i.employee_id, str(i.skill_sets_set.get().update_date)]
                    user_list.append(user_lists)
                    skill = Skill_Sets.objects.get(user_id=i.id)
                    x, y = skill.primary_skill, skill.secondary_skil
                    if x or y is not None:

                        user_name = {f'{skill.user.name}': {'primary': f'{skill.primary_skill}',
                                                            'secondary': f'{skill.secondary_skil}'}}
                        sk.append(user_name)
                    else:
                        pass
                except Skill_Sets.DoesNotExist and Skill_Sets.DoesNotExist:
                    user_lists = [i.name, i.employee_id, 'Skills Not Filled ']
                    user_list.append(user_lists)

            m = json.dumps(sk)
            print(m)
            print(user_list)
            page_l = request.GET.get('page_l', 1)
            paginator = Paginator(user_list, 10)
            try:
                users = paginator.page(page_l)
            except PageNotAnInteger:
                users = paginator.page(1)
            except EmptyPage:
                users = paginator.page(paginator.num_pages)
            return render(request, 'dashboard/hr_skill_table.html', {'name': m, 'skills': users})
        else:
            return render(request, 'dashboard/404.html', status=404)


def announcement_admin(request):
    if request.method == 'POST':
        print(request)
        title = request.POST.get('title')
        description = request.POST.get('description')
        times = request.POST.get('time')
        print('title',times)
        announcement = Notification_From_Admin.objects.create(title=title, description=description, time=times)
        announcement.save()
        sweetify.success(request, 'Success', text='New Announcement Created',
                         persistent='Ok')

    return render(request, 'dashboard/announcement.html')


def training_page(request):
    files = Upload_Training_Document.objects.all()
    context = {'files': files}
    return render(request, 'dashboard/training.html', context)

def training_download_file(request, file_name):
    file_obj = get_object_or_404(Upload_Training_Document, name=file_name)
    file_path = file_obj.training_file.path
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-powerpoint")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    return HttpResponse("Failed")

def upload_training(request):
    if request.user.role != "ADMIN":
        return HttpResponseForbidden()

    if request.method == 'POST' and request.FILES.getlist('file'):
        for uploaded_file in request.FILES.getlist('file'):
            original_name = uploaded_file.name
            modified_name = original_name.title().replace('_', ' ')
            filename, file_extension = os.path.splitext(modified_name)

            if file_extension:
                modified_name = filename

            try:
                print('modified_name',modified_name,'training_file',uploaded_file)
                document = Upload_Training_Document(name=modified_name, training_file=uploaded_file)
                document.save()
            except Exception as e:
                print(f"Error saving file: {e}")

        return redirect('upload_training')

    uploaded_files = Upload_Training_Document.objects.all()

    context = {'uploaded_files': uploaded_files}
    return render(request, 'dashboard/training_update.html', context)



def delete_file(request, file_id):
    document = get_object_or_404(Upload_Training_Document, id=file_id)
    document_name = document.name.replace('_', ' ').title()

    if os.path.isfile(document.training_file.path):
        os.remove(document.training_file.path)

    document.delete()

    messages.success(request, f"{document_name} has been deleted.")

    return redirect('upload_training')


@login_required(login_url="user_login")
def leave_policy(request):
    role = request.user.role
    return render(request, 'dashboard/leave_policy.html', {'role': role})


import os
from django.http import FileResponse

def hr_pdf_view(request):
    static_dir = settings.STATICFILES_DIRS[0]
    training_dir = os.path.join(static_dir, 'leave_policy')
    recent_files = sorted(glob.glob(os.path.join(training_dir, '*')), key=os.path.getctime, reverse=True)[:1]
    if os.path.splitext(recent_files[0])[1] == '.pdf':
        file = open(recent_files[0], 'rb')
    else:
        file = open(convert_word_to_pdf(recent_files[0]), 'rb')
    response = FileResponse(file)
    return response


def hr_policy_pdf_view(request):
    static_dir = settings.STATICFILES_DIRS[0]
    training_dir = os.path.join(static_dir, 'hr_policy')
    recent_files = sorted(glob.glob(os.path.join(training_dir, '*')), key=os.path.getctime, reverse=True)[:1]
    if os.path.splitext(recent_files[0])[1] == '.pdf':
        file = open(recent_files[0], 'rb')
    else:
        file = open(convert_word_to_pdf(recent_files[0]), 'rb')
    response = FileResponse(file)
    return response


from docx2pdf import convert

def convert_word_to_pdf(word_file_path):
    pdf_file_path = os.path.splitext(word_file_path)[0] + '.pdf'
    convert(word_file_path, pdf_file_path)
    return pdf_file_path

def hr_pdf_update(request):
    if request.method == 'POST' and request.FILES.get('leave_policy'):
        print('hello')
        leave_policy = request.FILES.get('leave_policy')
        subdirectory = 'leave_policy'
        # folder_path = os.path.join('static', subdirectory)
        static_dir = settings.STATICFILES_DIRS[0]
        folder_path = os.path.join(static_dir, subdirectory)

        print(static_dir)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        folder_pa = os.path.join(folder_path,leave_policy.name)
        with open(folder_pa, 'wb+') as destination:
            for chunk in leave_policy.chunks():
                destination.write(chunk)
        sweetify.success(request, 'Success', text='Leave Policy Updated',
                         persistent='Ok')

    return render(request, 'dashboard/leave_policy_update.html')


def hr_policy_pdf_update(request):
    if request.method == "POST" and request.FILES.get('hr_policy'):
        print('sssssssss')
        hr_policy = request.FILES.get('hr_policy')
        subdirectory = 'hr_policy'
        # folder = os.path.join('static', subdirectory)
        static_dir = settings.STATICFILES_DIRS[0]
        folder_path = os.path.join( static_dir, subdirectory)
        print(folder_path)
        if not os.path.exists(folder_path):
            print('dir created ')
            os.makedirs(folder_path)
        print('folder_pa',folder_path)
        folder_pa = os.path.join(folder_path,hr_policy.name)
        print(folder_path)
        with open(folder_pa, 'wb+') as destination:
            for chunk in hr_policy.chunks():
                destination.write(chunk)
        sweetify.success(request, 'Success', text='HR Policy Updated',
                         persistent='Ok')

    return render(request, 'dashboard/hr_policy_update.html')

class Add_holiday(View):

    def get(self, request):
        return render(request, 'dashboard/add_holiday.html')

    def post(self, request):
        holiday_name = request.POST.getlist('holiday_name')
        holiday_date = request.POST.getlist('holiday_date')
        optional = request.POST.getlist('optional')


        for i in range(len(holiday_name)):
            HolidayCalender.objects.create(name=holiday_name[i], date=holiday_date[i], optional=bool(int(optional[i])))

        return redirect('holiday_calender')


class Modify_holiday(View):

    def get(self, request):
        x = date.today()
        print(x.year)
        holiday = []
        holiday_list = HolidayCalender.objects.filter(date__year=x.year).order_by('date')
        print(holiday_list)
        i = 1
        for h in holiday_list:
            temp_date = h.date.strftime('%Y-%m-%d')
            opt = 'Optional' if h.optional else ''
            holiday.append({'sno': h.id, 'date': temp_date, 'name': h.name, 'opt': opt})
            i += 1

        return render(request, 'dashboard/modify_holiday.html', {'holiday': holiday})


def delete_holiday(request, id):
    if request.method == 'POST':
        print(id,'id')
        HolidayCalender.objects.filter(pk=id).delete()
        return JsonResponse({'status': 'ok'})
    else:
        return JsonResponse({'status': 'error'})


def modify_or_delete_holiday(request, id):
    if request.method == 'POST':
        obj = get_object_or_404(HolidayCalender, pk=id)
        old_data = {
            'name': obj.name,
            'date': obj.date,
            'optional': obj.optional,
        }

        new_data = {
            'name': request.POST['holiday_name'],
            'date': datetime.datetime.strptime(request.POST['holiday_date'], '%Y-%m-%d').date(),
            'optional': True if request.POST['optional'] == '1' else False,
        }
        if new_data == old_data:
            return JsonResponse({'status': 'error'})
        else:
            HolidayCalender.objects.filter(pk=id).update(name=request.POST['holiday_name'], date=request.POST['holiday_date'], optional=new_data['optional'])

            return JsonResponse({'status': 'ok'})

def upload_logo(request):
    if request.method == 'POST':
        logo_file = request.FILES.get('logo')
        if logo_file:
            filename = logo_file.name
            static_dir = settings.STATICFILES_DIRS[0]
            logo_dir = os.path.join(static_dir, 'Logo')
            os.makedirs(logo_dir, exist_ok=True)
            file_path = os.path.join(logo_dir, filename)
            with open(file_path, 'wb+') as destination:
                for chunk in logo_file.chunks():
                    destination.write(chunk)
            
            for file in os.listdir(logo_dir):
                if file != filename:
                    os.remove(os.path.join(logo_dir, file))
                    
            return redirect('logo_list')
        else:
            return redirect('upload_logo')
    else:
        return render(request, 'dashboard/upload_logo.html')

def delete_logo_file(request, filename):
    if request.method == 'POST':
        static_dir = settings.STATICFILES_DIRS[0]
        file_path = os.path.join(static_dir, 'Logo', filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return redirect('logo_list')
        else:
            return HttpResponse("The file does not exist")
    else:
        return HttpResponseNotAllowed(['POST'])
    

def logo_list(request):
    static_dir = settings.STATICFILES_DIRS[0]
    logo_dir = os.path.join(static_dir, 'Logo')
    files = []
    for filename in os.listdir(logo_dir):
        file_path = os.path.join(logo_dir, filename)
        if os.path.isfile(file_path):
            file_size = os.path.getsize(file_path)
            files.append({
                'name': filename,
                'url': f'/static/Logo/{filename}',
                'size': file_size
            })
    context = {'files': files}
    return render(request, 'dashboard/upload_logo.html', context)

