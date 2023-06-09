from django.core.management.base import BaseCommand
from django.utils import timezone

import contextlib
from lms.models import User, HolidayCalender, Timesheet, UserHoliday, AutoDetectCasualLeave, Notification, \
    Log_Schedulder

from prowesstics.utils import current_year, date_range2, weekend, HolidayRequest,LeaveApproval
import datetime


class Command(BaseCommand):
    help = 'test scheduler'

    def handle(self, *args, **kwargs):
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        t_dat = None
        dat = datetime.date.today().isoweekday()
        time = timezone.now().strftime('%X')
        try:
            holi = HolidayCalender.objects.get(date=today)
            if holi.date.isoweekday() == 1:
                t_dat = 2
                print(t_dat)
            t_dat = t_dat
            print(dat)
            if dat == t_dat:

                pass
            else:
                print('Today is  holiday ')
                pass

            self.stdout.write("scheduler started %s" % time)


        except HolidayCalender.DoesNotExist:
            try:
                holi = HolidayCalender.objects.get(date=yesterday)

                if holi.date.isoweekday() == 1:
                    t_dat = 2
                t_dat = t_dat
                if dat == t_dat:
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
                                            Notification.objects.create(user_id=i.user_id,
                                                                        notification_type='AUTO_SICK',
                                                                        message=f'leave have been detected {i.date}',
                                                                        date_created=i.date)

                                            holiday.save()
                                            AutoDetectCasualLeave.objects.create(user_id=i.user_id, created_date=i.date,
                                                                                 year=current_year(), casual_logs=1,
                                                                                 leave_type='sickleave')

                                        else:
                                            holiday.casual_leave += 1
                                            Notification.objects.create(user_id=i.user_id,
                                                                        notification_type='AUTO_CASUAL',
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

                    Log_Schedulder.objects.create(name=f'Casual Logs for Tuesday {today} ', start_time=start,
                                                  end_time=end)
                    self.stdout.write("scheduler started %s" % time)


            except HolidayCalender.DoesNotExist:
                print('sss')
                dat =  datetime.date.today().isoweekday()


                if  dat == 1:
                    print('casual leave ')
                    start = datetime.datetime.now()

                    today = datetime.date.today()
                    yesterday = today - datetime.timedelta(days=1)
                    next_monday = today - datetime.timedelta(days=today.weekday())
                    next_sunday = today - datetime.timedelta(days=-today.weekday(), weeks=1)
                    get_user = Timesheet.objects.filter(date__gte=next_sunday, date__lte=next_monday)

                    print('get_user', get_user,next_monday,next_sunday)
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
                                            Notification.objects.create(user_id=i.user_id,
                                                                        notification_type='AUTO_SICK',
                                                                        message=f'leave have been detected {i.date}',
                                                                        date_created=i.date)

                                            holiday.save()
                                            AutoDetectCasualLeave.objects.create(user_id=i.user_id, created_date=i.date,
                                                                                 year=current_year(), casual_logs=1,
                                                                                 leave_type='sickleave')

                                        else:
                                            holiday.casual_leave += 1
                                            Notification.objects.create(user_id=i.user_id,
                                                                        notification_type='AUTO_CASUAL',
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
                    self.stdout.write("scheduler started %s" % time)
                else:
                  print('not monday')
                  self.stdout.write("scheduler started %s" % time)

# backup code for casual leave
# class Command(BaseCommand):
#     help = 'test scheduler'
#
#     def handle(self, *args, **kwargs):
#         if datetime.date.today().isoweekday() == 1:
#             print('casual leave ')
#             start = datetime.datetime.now()
#             today = datetime.date.today()
#             yesterday = today - datetime.timedelta(days=1)
#             next_monday = today - datetime.timedelta(days=today.weekday())
#             next_sunday = today - datetime.timedelta(days=-today.weekday(), weeks=1)
#             get_user = Timesheet.objects.filter(date__gte=next_sunday, date__lte=next_monday)
#             print(get_user)
#             dates = date_range2(next_sunday, next_monday)
#             for i in get_user:
#                 ''' approve is to check whether  approval is given by either Hr or Manager ,if so it return False
#                 and code will pass  to else condition and no leave will be detected  ,if it return True then  code
#                 will execute and leave will be detucted'''
#                 approve = LeaveApproval(i.date, i.user.id)
#                 # print(i.user,'================================================>', approved)
#                 print(i.status, i.date, dates)
#                 if str(i.date) in dates:
#                     if i.status == 'DetailsNone' and approve.approval():
#                         with contextlib.suppress(UserHoliday.DoesNotExist):
#                             holiday = UserHoliday.objects.get(user_id=i.user_id, year=current_year())
#                             print(holiday)
#                             x = i.date
#                             if not HolidayCalender.objects.filter(date=i.date).exists() and not weekend(x):
#                                 if holiday.casual_leave >= 9 and holiday.sick_leave >= 9:
#                                     holiday.lop += 1
#                                     Notification.objects.create(user_id=i.user_id, notification_type='LOP_TIMESHEET',
#                                                                 message=f'leave have been detected {i.date}',
#                                                                 date_created=i.date)
#
#                                     holiday.save()
#                                     AutoDetectCasualLeave.objects.create(user_id=i.user_id, created_date=i.date,
#                                                                          year=current_year(), casual_logs=1,
#                                                                          leave_type='lopleave')
#                                 elif holiday.casual_leave >= 9:
#                                     holiday.sick_leave += 1
#                                     Notification.objects.create(user_id=i.user_id, notification_type='AUTO_SICK',
#                                                                 message=f'leave have been detected {i.date}',
#                                                                 date_created=i.date)
#
#                                     holiday.save()
#                                     AutoDetectCasualLeave.objects.create(user_id=i.user_id, created_date=i.date,
#                                                                          year=current_year(), casual_logs=1,
#                                                                          leave_type='sickleave')
#
#                                 else:
#                                     holiday.casual_leave += 1
#                                     Notification.objects.create(user_id=i.user_id, notification_type='AUTO_CASUAL',
#                                                                 message=f'leave have been detected {i.date}',
#                                                                 date_created=i.date)
#
#                                     holiday.save()
#
#                                     AutoDetectCasualLeave.objects.create(user_id=i.user_id, created_date=i.date,
#                                                                          year=current_year(), casual_logs=1,
#                                                                          leave_type='casualleave')
#
#                                 # Notification.objects.create(user_id=i.user_id, notification_type='AUTO_CASUAL',
#                                 #                             message=f'leave have beeen detected {i.date}')
#
#
#                     else:
#                         print(f'No leave will be deducted {i.user} ')
#             end = datetime.datetime.now()
#
#             Log_Schedulder.objects.create(name=f'Casual Logs {today} ', start_time=start, end_time=end)
#         else:
#             print('Today is not monday')
#             pass
#         time = timezone.now().strftime('%X')
#         self.stdout.write("scheduler started %s" % time)