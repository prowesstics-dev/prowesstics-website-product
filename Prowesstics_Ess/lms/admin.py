from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from lms.models import User, HelpDesk ,Blog # modified user table
from lms.models import (UserHoliday, HolidayRequest, HolidayCalender, TempUserData, Timesheet, Project,
                        AutoDetectCasualLeave, Notification, Log_Schedulder, Skill_Sets,Jobs,Notification_From_Admin,Upload_Training_Document
                        )


class Useradmin(UserAdmin):
    ordering = ('email',)
    list_display = ('email', 'name', 'role', 'admin', 'is_staff')
    # search_fields = ('email', 'name')
    fieldsets = (
        (None, {'fields': ('id', 'last_login',)}),
        ("Personal Information", {'fields': (
        'name', 'email', 'password', 'gender', 'dob', 'per_address1', 'per_address2', 'tem_address1', 'tem_address2',
        'per_city', 'per_state', 'per_country', 'per_pincode', 'same_as_per_addr', 'per_phone_number', 'tem_city',
        'tem_state', 'tem_country', 'tem_pincode', 'tem_phone_number'
        )}),
        ("Official Information", {'fields': ('designation', 'role', 'doj', 'profile_pic', 'report_to')}),
        (None, {'fields': ('is_staff', 'admin', 'is_active', 'created_on', 'updated_on')})

    )
    add_fieldsets = (

        ("Personal Information", {'fields': ('name', 'email', 'password', 'gender', 'dob')}),
        ("Official Information", {'fields': ('designation', 'role', 'doj', 'profile_pic')}),
        (None, {'fields': ('is_staff', 'admin', 'is_active')})
    )
    readonly_fields = ('id', 'created_on', 'updated_on')


# Register your models here.

admin.site.register(User,Useradmin)
admin.site.register(UserHoliday)
admin.site.register(HolidayRequest)
admin.site.register(HolidayCalender)
admin.site.register(TempUserData)
admin.site.register(HelpDesk)
admin.site.register(Blog)
admin.site.register(Timesheet)
admin.site.register(Project)
admin.site.register(AutoDetectCasualLeave)
admin.site.register(Notification)
admin.site.register(Log_Schedulder)
admin.site.register(Skill_Sets)
admin.site.register(Jobs)
admin.site.register(Notification_From_Admin)
admin.site.register(Upload_Training_Document)