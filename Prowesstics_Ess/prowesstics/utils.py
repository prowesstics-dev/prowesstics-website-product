
import datetime
import string

from lms.models import HolidayRequest, UserHoliday, TempUserData, User
import random
import threading
import array
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string


# def current_year_old(today=None):
#     if today is None:
#         today = datetime.date.today()
#     mm = today.month
#     yy = today.year
#     year = ''
#     if mm <= 3:
#         year = str(yy - 1) + '-' + str(yy)
#     else:
#         year = str(yy) + '-' + str(yy + 1)
#     return year

def current_year(today=None):
    today = today or datetime.date.today()
    year = today.year if today.month > 3 else today.year - 1
    return f"{year}-{year+1}"

def prev_year(today=None):
    today = today or datetime.date.today()
    year = today.year - 1
    return f"{year}-{year+1}"



# def get_info(id):
#     # role
#     u = User.objects.filter(id=id)
#     role = u[0].role
#     '''
#     for _u in u:
#         if _u.role == 'HR':
#             role = "HR"
#         elif _u.role == 'MANAGER':
#             role = "MANAGER"
#         elif _u.role == 'EMPLOYEE':
#             role = "EMPLOYEE"
#         else:
#             role = "ADMIN"
#     '''
#     # leave applied
#     leave_applied = len(HolidayRequest.objects.filter(user__id=id))
#
#     user_holiday = UserHoliday.objects.filter(user__id=id, year=current_year())[0]
#     # sick_leave allowed & taken
#     sick_allowed = user_holiday.sick_leave_allowed
#     sick_leave = int(user_holiday.sick_leave)
#     # casual_leave allowed & taken
#     casual_allowed = user_holiday.casual_leave_allowed
#     casual_leave = int(user_holiday.casual_leave)
#     # total leave allowed & taken
#     total_allowed = casual_allowed + sick_allowed
#     total_allowed = int(total_allowed) if (total_allowed * 10) % 10 == 0 else total_allowed
#     total_leave = sick_leave + casual_leave
#     total_leave = int(total_leave) if (total_leave * 10) % 10 == 0 else total_leave
#     # remaining leave
#     remaining_leave = total_allowed - total_leave
#
#     # lop
#     lop = user_holiday.lop
#     lop = int(lop) if (lop * 10) % 10 == 0 else lop
#
#     # # leave pending
#     # if role == "EMPLOYEE":
#     #     leave_pending = len(
#     #         HolidayRequest.objects.filter(user__id=id, hr_level_approval=True, manager_level_approval=True))
#     # elif role == "MANAGER":
#     #     leave_pending = len(HolidayRequest.objects.filter(user__id=id, hr_level_approval=True))
#     # else:
#     #     leave_pending = 0
#     print(role)
#     return role, total_leave, lop, remaining_leave, int(casual_allowed - casual_leave), int(sick_allowed - sick_leave)
#
def get_info(id):
    # role
    u = User.objects.get(id=id)
    role = u.role
    user_holiday = UserHoliday.objects.get(user__id=id, year=current_year())

    # sick_leave allowed & taken
    sick_allowed = user_holiday.sick_leave_allowed
    sick_leave = float(user_holiday.sick_leave)

    # casual_leave allowed & taken
    casual_allowed = user_holiday.casual_leave_allowed
    casual_leave = float(user_holiday.casual_leave)

    # total leave allowed & taken
    total_allowed = casual_allowed + sick_allowed
    total_leave = sick_leave + casual_leave

    # remaining leave
    remaining_leave = total_allowed - total_leave

    # lop
    lop = user_holiday.lop
    lop = float(lop) if (lop * 10) % 10 == 0 else lop

    return role, total_leave, lop, remaining_leave, float(casual_allowed - casual_leave), float(
        sick_allowed - sick_leave)

def get_prev_info(id):
    today = datetime.date.today()
    if today.month == 4 and today.day in [10,11,12]:
        u = User.objects.get(id=id)
        role = u.role
        user_holiday = UserHoliday.objects.get(user__id=id, year=prev_year())

        # sick_leave allowed & taken
        sick_allowed = user_holiday.sick_leave_allowed
        sick_leave = float(user_holiday.sick_leave)

        # casual_leave allowed & taken
        casual_allowed = user_holiday.casual_leave_allowed
        casual_leave = float(user_holiday.casual_leave)

        # total leave allowed & taken
        total_allowed = casual_allowed + sick_allowed
        total_leave = sick_leave + casual_leave

        # remaining leave
        remaining_leave = total_allowed - total_leave

        # lop
        lop = user_holiday.lop
        return role, total_leave, lop, remaining_leave, float(casual_allowed - casual_leave), float(
            sick_allowed - sick_leave)
    else:
        u = User.objects.get(id=id)
        role = u.role
        user_holiday = UserHoliday.objects.get(user__id=id, year=current_year())

        # sick_leave allowed & taken
        sick_allowed = user_holiday.sick_leave_allowed
        sick_leave = float(user_holiday.sick_leave)

        # casual_leave allowed & taken
        casual_allowed = user_holiday.casual_leave_allowed
        casual_leave = float(user_holiday.casual_leave)

        # total leave allowed & taken
        total_allowed = casual_allowed + sick_allowed
        total_leave = sick_leave + casual_leave

        # remaining leave
        remaining_leave = total_allowed - total_leave

        # lop
        lop = user_holiday.lop
        lop = float(lop) if (lop * 10) % 10 == 0 else lop

        return role, total_leave, lop, remaining_leave, float(casual_allowed - casual_leave), float(
            sick_allowed - sick_leave)


# def get_role(role):
#     if role.upper() == 'HR':
#         return 'HR'
#     elif role.upper() == 'MANAGER':
#         return 'MANAGER'
#     elif role.upper() == 'EMPLOYEE':
#         return 'EMPLOYEE'
#     else:
#         return role

def password_generator(userdetails=None):
    MAX_LEN = 12
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for _ in range(MAX_LEN))

    if userdetails:
        pass_save = TempUserData.objects.get(user__id=userdetails.id)
        pass_save.code = password
        pass_save.save()

    return password

def get_role(role):
    return role.upper() if role.upper() in ['HR', 'MANAGER', 'EMPLOYEE'] else role

# def password_generator(userdetails=None):
#     MAX_LEN = 12
#     DIGITS = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
#     LOCASE_CHARACTERS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h',
#                          'i', 'j', 'k', 'm', 'n', 'o', 'p', 'q',
#                          'r', 's', 't', 'u', 'v', 'w', 'x', 'y',
#                          'z']
#
#     UPCASE_CHARACTERS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
#                          'I', 'J', 'K', 'M', 'N', 'O', 'p', 'Q',
#                          'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y',
#                          'Z']
#
#     SYMBOLS = ['@', '#', '$', '%', '=', ':', '?', '.', '/', '|', '~', '>',
#                '*', '(', ')', '<']
#
#     # combines all the character arrays above to form one array
#     COMBINED_LIST = DIGITS + UPCASE_CHARACTERS + LOCASE_CHARACTERS + SYMBOLS
#
#     # randomly select at least one character from each character set above
#     rand_digit = random.choice(DIGITS)
#     rand_upper = random.choice(UPCASE_CHARACTERS)
#     rand_lower = random.choice(LOCASE_CHARACTERS)
#     rand_symbol = random.choice(SYMBOLS)
#
#     temp_pass = rand_digit + rand_upper + rand_lower + rand_symbol
#
#     for x in range(MAX_LEN - 4):
#         temp_pass = temp_pass + random.choice(COMBINED_LIST)
#
#         temp_pass_list = array.array('u', temp_pass)
#         random.shuffle(temp_pass_list)
#
#     password = ""
#     for x in temp_pass_list:
#         password = password + x
#
#     if userdetails:
#         pass_save = TempUserData.objects.get(user__id=userdetails.id)
#         pass_save.code = password
#         pass_save.save()
#
#     return password




def calculate_leave_type(application, action, year=None):
    id = application.user.id
    print(id)
    if year is None:
        year = current_year()
    if application.category == 'redeem':
        today = datetime.date.today()
        year = current_year(datetime.date(today.year - 1, today.month, today.day))
    user_leave_data = UserHoliday.objects.filter(user__id=id, year=year)[0]
    print(user_leave_data)
    no_of_leave = application.no_of_days
    sick_leave_allowed = user_leave_data.sick_leave_allowed
    casual_leave_allowed = user_leave_data.casual_leave_allowed
    sick_leave = user_leave_data.sick_leave
    casual_leave = user_leave_data.casual_leave
    optional_leave = user_leave_data.optional_leave
    redeem = user_leave_data.redeem_leave
    lop = user_leave_data.lop
    if action == 'accept':
        if application.category == 'sick':
            sick_leave += no_of_leave
            if sick_leave > sick_leave_allowed:
                temp = sick_leave - sick_leave_allowed
                sick_leave = sick_leave_allowed
                casual_leave += temp
            if casual_leave > casual_leave_allowed:
                temp = casual_leave - casual_leave_allowed
                casual_leave = casual_leave_allowed
                lop += temp
        elif application.category == 'casual':
            casual_leave += no_of_leave
            if casual_leave > casual_leave_allowed:
                temp = casual_leave - casual_leave_allowed
                casual_leave = casual_leave_allowed
                sick_leave += temp
            if sick_leave > sick_leave_allowed:
                temp = sick_leave - sick_leave_allowed
                sick_leave = sick_leave_allowed
                lop += temp
        elif application.category == 'redeem':
            redeem += casual_leave
            casual_leave = 0
        else:
            optional_leave += 1
    elif action == 'reject':
        sick_leave = sick_leave - application.delta_sick
        casual_leave = casual_leave - application.delta_casual
        optional_leave = optional_leave - application.delta_optional
        lop = lop - application.delta_lop
        if application.category == 'redeem':
            casual_leave += redeem
            redeem = 0
    return dict(sick=sick_leave, casual=casual_leave, optional=optional_leave, lop=lop, redeem=redeem)


def get_user_details(id):
    user_details = User.objects.filter(id=id)
    return user_details[0]


class EmailThread(threading.Thread):
    def __init__(self, email, password, user_name):
        self.email = email
        self.password = password
        self.user_name = user_name
        threading.Thread.__init__(self)

    def run(self):
        print("thread run in here")
        message = render_to_string('passwordmail.html', {
            'login': "http://127.0.0.1:8000/profile/login",
            'password': self.password,
            'name': self.user_name,
            'email': self.email
        })
        '''
        mail_subject = 'Global Solutions - Your account password'
        email = EmailMessage(subject=mail_subject, body=message, to=[self.email],
                             from_email='hr <admin@prowesstics.com>')
        email.content_subtype = "html"
        s = email.send()
        '''
        s = send_mail(
            'Prowesstics account login password ',
            f'hi {self.user_name}, your login password is {self.password}',
            'admin@prowesstics.com',
            [self.email],
            html_message=message,
            fail_silently=False,
        )
        print('s= ', s, self.email, self.password, self.user_name)


def send_mail_password(email, password, user_name):
    EmailThread(email, password, user_name).start()


class EmailThread1(threading.Thread):
    def __init__(self, email, applicant, date, user_name, reason):
        self.email = email
        self.applicant = applicant
        self.date = date
        self.user_name = user_name
        self.reason = reason
        threading.Thread.__init__(self)

    def run(self):
        print("thread run in here")

        message = render_to_string('leavemail.html', {
            'login': "http://127.0.0.1:8000/profile/login",
            'date': self.date,
            'name': self.user_name,
            'applicant': self.applicant,
            'reason': self.reason
        })
        s = send_mail(
            'Leave Application - Waiting for your Approval',
            f'hi {self.user_name}, your have a leave request',
            'admin@prowesstics.com',
            [self.email],
            html_message=message,
            fail_silently=False,
        )
        print('s= ', s, self.email, self.user_name)


def send_leave_notification(email, applicant, date, user_name, reason):
    if type(email) == str and type(user_name) == str:
        EmailThread1(email, applicant, date, user_name, reason).start()
    elif type(email) == list and type(user_name) == list:
        for mail, name in zip(email, user_name):
            EmailThread1(mail, applicant, date, name, reason).start()


# class EmailThread3(threading.Thread):
#     def __init__(self,email, applicant, date, user_name, reason):
#         self.email = email
#         self.applicant = applicant
#         self.date = date
#         self.user_name = user_name
#         self.reason = reason
#         threading.Thread.__init__(self)
#
#     def run(self):
#         print("thread run in here")
#
#         message = render_to_string('leavemail.html', {
#             'login': "http://127.0.0.1:8000/profile/login",
#             'date': self.date,
#             'name': self.user_name,
#             'applicant': self.applicant,
#             'reason': self.reason
#         })
#         s = send_mail(
#             'Leave Application - Waiting for your Approval',
#             f'hi {self.user_name}, your have a leave request',
#             'carokee739@gmail.com',
#             [ 'carokee739@gmail.com'],
#             html_message=message,
#             fail_silently=False,
#         )
#         print('s= ', s, self.email, self.user_name)
#
#
# def send_leave_notification2(email, applicant, date, user_name, reason):
#     if type(email) == str and type(user_name) == str:
#         EmailThread3(email, applicant, date, user_name, reason).start()
#     elif type(email) == list and type(user_name) == list:
#         for mail, name in zip(email, user_name):
#             EmailThread3(mail, applicant, date, name, reason).start()

class EmailThreadhr(threading.Thread):
    def __init__(self, email, applicant, date, user_name, reason):
        self.email = email
        self.applicant = applicant
        self.date = date
        self.user_name = user_name
        self.reason = reason
        threading.Thread.__init__(self)

    def run(self):
        print("thread run in here")

        message = render_to_string('leavemail.html', {
            'login': "http://127.0.0.1:8000/profile/login",
            'date': self.date,
            'name': self.user_name,
            'applicant': self.applicant,
            'reason': self.reason
        })
        s = send_mail(
            'Leave Application - Waiting for your Approval',
            f'hi {self.user_name}, your have a leave request',
            'admin@prowesstics.com',
            [self.email, 'hr@prowesstics.com'],
            html_message=message,
            fail_silently=False,

        )
        print('s= ', s, self.email, self.user_name)


def send_leave_notification_hr(email, applicant, date, user_name, reason):
    if type(email) == str and type(user_name) == str:
        EmailThreadhr(email, applicant, date, user_name, reason).start()
    elif type(email) == list and type(user_name) == list:
        for mail, name in zip(email, user_name):
            EmailThreadhr(mail, applicant, date, name, reason).start()


class EmailThread2(threading.Thread):
    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        print("thread run in here")
        self.email.send()


def send_helpdesk(email):
    EmailThread2(email).start()


class EmailThread3(threading.Thread):
    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        print("thread run in here")
        self.email.send()


def contact_home(email):
    EmailThread3(email).start()


'''Time sheeet Functions'''


def date_range(start, end):
    delta = end - start  # as timedelta
    days = [start + datetime.timedelta(days=i) for i in range(delta.days + 1)]
    return days


def date_range2(start, end):
    delta = end - start  # as timedelta
    days = [str(start + datetime.timedelta(days=i)) for i in range(delta.days + 1)]
    return days


import datetime


def weekend(x):
    x_date = x
    no = x_date.weekday()
    if no < 5:
        return False
    else:  # 5 Sat, 6 Sun
        return True


def find_no_days(start, end):
    r = end + datetime.timedelta(1)

    x = [start + datetime.timedelta(days=x) for x in range((r - start).days)]
    return x


class LeaveApproval:
    def __init__(self,date,id):
        self.date =date
        self.id =id
    def approval(self):

        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        user_holiday = HolidayRequest.objects.filter(user_id=(self.id), year=current_year(),
                                                     start_date__month=yesterday.month)
        if user_holiday is not None:
            for holi in user_holiday:
                print('==================================================>', user_holiday, )
                leaves = holi.leaves_sep_v
                my_list = leaves.split(",")
                if str(self.date) in my_list and (holi.hr_level_approval or holi.manager_level_approval):
                    approved = False
                    return approved
                return True
        return True
