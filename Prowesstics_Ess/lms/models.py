from django.db import models

# Create your models here.
from django.core.mail import send_mail
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser
from django.db.models import signals
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.base_user import BaseUserManager

from datetime import datetime
from ckeditor_uploader.fields import RichTextUploadingField
from django.contrib.postgres.fields import ArrayField
from django.conf import settings
import os


# from prowesstics.utils import find_no_days


class UserManager(BaseUserManager):
    def create_user(self, email, password=None):
        if not email:
            raise ValueError('Enter an user email')
        email = self.normalize_email(email)
        user = self.model(email=email)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        user = self.create_user(email, password)
        user.admin = True
        user.is_superuser = True
        user.is_staff = True
        user.role = "ADMIN"
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    HR = "HR"
    MANAGER = "MANAGER"
    EMPLOYEE = "EMPLOYEE"
    ADMIN = "ADMIN"
    CEO = "CEO"
    INTERN = "INTERN"
    USER_TYPE_CHOICES = (
        (HR, 'HR'),
        (MANAGER, 'MANAGER'),
        (EMPLOYEE, 'EMPLOYEE'),
        (ADMIN, 'ADMIN'),
        (CEO, 'CEO'),
        (INTERN, 'INTERN')
    )

    # user_id = models.IntegerField()
    name = models.CharField(max_length=200, blank=True, null=True)
    email = models.CharField(max_length=200, blank=True, null=True, unique=True)
    password = models.CharField(max_length=128, null=True)
    role = models.CharField(max_length=100, choices=USER_TYPE_CHOICES, null=True)
    designation = models.CharField(max_length=200, blank=True, null=True)
    gender = models.CharField(max_length=200, null=True)
    dob = models.DateField(null=True)
    doj = models.DateField(null=True)
    admin = models.BooleanField(default=False)
    profile_pic = models.ImageField(upload_to='', null=True, blank=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)
    is_staff = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    report_to = models.IntegerField(blank=True, null=True)
    per_address1 = models.CharField(max_length=255, null=True)
    per_address2 = models.CharField(max_length=255, blank=True, null=True)
    tem_address1 = models.CharField(max_length=255, null=True)
    tem_address2 = models.CharField(max_length=255, blank=True, null=True)
    per_city = models.CharField(max_length=255, null=True)
    per_state = models.CharField(max_length=255, null=True)
    per_country = models.CharField(max_length=255, null=True)
    per_pincode = models.CharField(max_length=20, null=True)
    same_as_per_addr = models.BooleanField(default=False)
    per_phone_number = models.CharField(max_length=20, null=True)
    tem_city = models.CharField(max_length=255, null=True)
    tem_state = models.CharField(max_length=255, null=True)
    tem_country = models.CharField(max_length=255, null=True)
    tem_pincode = models.CharField(max_length=20, null=True)
    tem_phone_number = models.CharField(max_length=20, null=True)
    asset = models.CharField(max_length=255, null=True)
    computer_brand = models.CharField(max_length=255, null=True)
    computer_ram = models.CharField(max_length=255, null=True)
    computer_processor = models.CharField(max_length=255, null=True)
    personal_email = models.CharField(max_length=200, null=True, unique=True)
    employee_id = models.CharField(max_length=255, null=True, blank=True)
    bank_name = models.CharField(max_length=255, null=True)
    bank_account_number = models.CharField(max_length=255, null=True)
    objects = UserManager()

    USERNAME_FIELD = 'email'


class TempUserData(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    code = models.CharField(max_length=128, null=True)

    def __str__(self):
        return self.user.name + '  -  ' + str(self.code)


class UserHoliday(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    # user = models.OneToOneField(User, models.CASCADE, null=True)
    sick_leave_allowed = models.FloatField(default=9)
    casual_leave_allowed = models.FloatField(default=9)
    sick_leave = models.FloatField(default=0)
    casual_leave = models.FloatField(default=0)  # unpaid
    optional_leave = models.FloatField(default=0)
    redeem_leave = models.FloatField(default=0)
    year = models.CharField(max_length=200, null=True)
    lop = models.FloatField(default=0)

    def __str__(self):
        return self.user.name + '  -  ' + str(self.sick_leave_allowed) + ' - ' + str(self.casual_leave_allowed)


class HolidayRequest(models.Model):
    # userdetails = models.ForeignKey(UserDetails, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    no_of_days = models.FloatField()
    description = models.TextField()
    category = models.CharField(max_length=150)
    type = models.CharField(max_length=150, default='full day')
    manager_level_approval = models.BooleanField(blank=True, null=True, default=None)
    hr_level_approval = models.BooleanField(blank=True, null=True, default=None)
    admin_level_approval = models.BooleanField(blank=True, null=True, default=None)
    employee_level_approval = models.BooleanField(blank=True, null=True, default=None)
    date = models.DateField(default=datetime.today().date())
    decision = models.TextField(default='')
    delta_sick = models.FloatField(default=0)
    delta_casual = models.FloatField(default=0)  # unpaid
    delta_optional = models.FloatField(default=0)
    delta_lop = models.FloatField(default=0)
    attachment = models.ImageField(upload_to='', null=True, blank=True)
    year = models.CharField(max_length=20, blank=True, null=True)

    leaves_sep_v = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.user.name} - {self.category} - {self.no_of_days} - {self.start_date} - {self.end_date} -{self.type}"


class HolidayCalender(models.Model):  
    name = models.CharField(max_length=25)
    date = models.DateField()
    optional = models.BooleanField()

    def __str__(self):
        return self.name + '   -   ' + str(self.date)


class HelpDesk(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    category = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    attachment = models.FileField(upload_to='', null=True, blank=True)
    ticket_solved = models.BooleanField(default=False, null=True)


class Blog(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    slug = models.SlugField(max_length=255, null=True, blank=True)
    category = models.CharField(max_length=255, null=True, blank=True)
    bio = models.TextField(max_length=255, null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    content = RichTextUploadingField(blank=True, null=True)
    img_url = models.URLField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_on = models.DateTimeField(auto_created=True, null=True, blank=True)
    image = models.ImageField(upload_to='', null=True, blank=True)
    description = models.TextField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.title + '  by  ' + str(self.author)


class Project(models.Model):
    project_name = models.CharField(max_length=255, null=True, blank=True)
    project_manager = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.project_name


class Timesheet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    project = models.CharField(max_length=255, null=True)
    project_manager = models.CharField(max_length=255, null=True)
    start_time = models.CharField(max_length=255, null=True, blank=True)
    end_time = models.CharField(max_length=255, null=True, blank=True)
    date = models.DateField()
    status = models.TextField(null=True, blank=True)
    access = models.BooleanField(blank=True, null=True, default=False)
    logged_hours = models.CharField(max_length=255, null=True, blank=True, default=0)

    def __str__(self):
        return f'{self.user.name} - {self.project} - {self.status} - {self.date} -{self.id}'


class AutoDetectCasualLeave(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    created_date = models.CharField(max_length=255, null=True)
    year = models.CharField(max_length=255, null=True)
    casual_logs = models.IntegerField(null=True)
    leave_type = models.CharField(max_length=255, null=True)

    def __str__(self):
        return f'{self.created_date} - {self.user.name}'


class Notification(models.Model):
    not1 = 'AUTO_CASUAL'
    not2 = 'REMINDER'
    not3 = 'LOP_TIMESHEET'
    not4 = 'AUTO_SICK'
    notification_choice = ((not1, 'AUTO_CASUAL'), (not2, 'REMINDER'), (not3, 'LOP_TIMESHEET'), (not4, 'AUTO_SICK'))
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    notification_type = models.CharField(max_length=255, choices=notification_choice, null=True)
    message = models.TextField(null=True, blank=True)
    seen = models.BooleanField(blank=True, null=True, default=False)
    date_created = models.DateField(null=True)

    def __str__(self):
        return f'{self.notification_type} - {self.user.name} - {self.message}'


class Log_Schedulder(models.Model):
    name = models.CharField(max_length=255, null=True)
    start_time = models.DateTimeField(max_length=255, null=True)
    end_time = models.DateTimeField(max_length=255, null=True)

    def __str__(self):
        return self.name


from datetime import datetime, timedelta


def find_no_days(start, end):
    print(start, end)
    d = []
    delta = end - start  # returns timedelta

    for i in range(delta.days + 1):
        day = start + timedelta(days=i)
        d.append(str(day))
        print(day)
    return d


def add_leave_dates(sender, **kwargs):
    instance = kwargs['instance']
    if instance:
        f = datetime.strptime(str(instance.start_date), "%Y-%m-%d").strftime("%d-%m-%Y")
        t = datetime.strptime(str(instance.end_date), "%Y-%m-%d").strftime("%d-%m-%Y")
        start = datetime.strptime(f, '%d-%m-%Y').date()
        end = datetime.strptime(t, '%d-%m-%Y').date()
        leave = find_no_days(start=start, end=end)
        leaves = ','.join(leave)

        HolidayRequest.objects.filter(id=instance.id).update(leaves_sep_v=leaves)
        for j in leave:
            time = Timesheet.objects.filter(id=instance.user.id, date=j)
            print(time, 'time', instance.category)
            for k in time:
                if k.status == 'DetailsNone':
                    print('time status ', k.status)
                    k.status = 'LEAVE'
                    print('time status ', k.status)
                    k.save()

    else:
        return ''


signals.post_save.connect(receiver=add_leave_dates, sender=HolidayRequest)


class Skill_Sets(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    primary_skill = models.CharField(max_length=500, blank=True, null=True)
    secondary_skil = models.CharField(max_length=500, blank=True, null=True)
    update_date = models.DateField(default=datetime.today().date(), null=True)

    def __str__(self):
        return f'{self.pk} {self.user.name}'


class Jobs(models.Model):
    role = models.CharField(max_length=500)
    role_resp = models.TextField()
    skills = models.CharField(max_length=500)
    active = models.BooleanField(default=True)
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.pk} {self.role}'


class Notification_From_Admin(models.Model):
    title = models.CharField(max_length=255,default='')
    description = models.TextField()
    time = models.DateTimeField(null=True)


    def __repr__(self):
        return f'{self.title} and {self.time}'


# class upload_document(models.Model):
#     name = models.CharField(max_length=255)
#     file = models.FileField(upload_to='')

#     def get_absolute_url(self):
#         return self.file.url

#     def save(self, *args, **kwargs):
#         static_dir = settings.STATICFILES_DIRS[0]
#         training_dir = os.path.join(static_dir, 'Training')
#         self.file.storage.location = training_dir
#         super(upload_document, self).save(*args, **kwargs)

#     def __str__(self):
#         return f'{self.name}'

class Upload_Training_Document(models.Model):
    name = models.CharField(max_length=255)
    training_file = models.FileField(upload_to='')

    def get_absolute_url(self):
        return self.training_file.url

    def save(self, *args, **kwargs):
        static_dir = settings.STATICFILES_DIRS[0]
        training_dir = os.path.join(static_dir, 'Training')
        self.training_file.storage.location = training_dir
        super(Upload_Training_Document, self).save(*args, **kwargs)

    def __str__(self):
        return f'{self.name}'

