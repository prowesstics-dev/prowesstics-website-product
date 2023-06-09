# import contextlib
#
# from django.core.mail import EmailMessage
# from django.db.models import Q
# from django_apscheduler.jobstores import DjangoJobStore, register_job, register_events
# from apscheduler.schedulers.background import BackgroundScheduler
# from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
# # from datetime import datetime, timedelta, date
# from lms.models import User, HolidayCalender, Timesheet, UserHoliday, AutoDetectCasualLeave,Notification,Log_Schedulder
#
# from prowesstics.utils import current_year ,date_range2, weekend,HolidayRequest
# import datetime
#
#
# executors = {
#     'default': ThreadPoolExecutor(10),
#     'processpool': ProcessPoolExecutor(5)
# }
# job_defaults = {
#     'coalesce': False,
#     'max_instances': 20
# }
#
# scheduler = BackgroundScheduler(executors=executors, job_defaults=job_defaults, timezone='Asia/Kolkata')
# scheduler.add_jobstore(DjangoJobStore(), "default")

#
# # #@scheduler.scheduled_job('cron', id='casual_leave_timesheet', day_of_week=1, hour=15, minute=3)
#
#
#
# #@scheduler.scheduled_job('cron', id='check_timesheet_date', hour=15, minute=1)
# def check_timesheet_date():
#     start = datetime.datetime.now()
#     user = User.objects.filter(admin=False).exclude(Q(role='HR') | Q(role='CEO'))
#     today = datetime.date.today()
#     yesterday = today - datetime.timedelta(days=1)
#     for i in user:
#
#         Timesheet.objects.filter(user_id=i.id, access=True).update(access=False)
#         holiday = HolidayCalender.objects.filter(date=yesterday).exists()
#         time = Timesheet.objects.filter(user_id=i.id, date=yesterday).exists()
#         user_holiday=HolidayRequest.objects.filter(user_id= i.id, date=yesterday,hr_level_approval=True ,manager_level_approval=True)
#
#         week = weekend(yesterday)
#         if user_holiday or holiday or time or week:
#             print('pass','sssssssssssssssssss')
#             pass
#
#         else:
#             project_name = 'Others'
#             manager = 'None'
#             stime = 'None'
#             etime = 'None'
#             status = 'DetailsNone'
#             times = Timesheet.objects.create(user_id=i.id, project=project_name, project_manager=manager,
#                                              start_time=stime,
#                                              end_time=etime,
#                                              status=status,date=yesterday)
#             Notification.objects.create(user_id=i.id, notification_type='REMINDER',
#                                        message=f' Fill Your Daily Timesheet details for {yesterday} ')
#             print(times)
#     end = datetime.datetime.now()
#
#     Log_Schedulder.objects.create(name=f'Daily Timesheet Logs {yesterday} ', start_time=start, end_time=end)
#
#
#
# def casual_leave_timesheet():
#     print('casual leave ')
#     start=datetime.datetime.now()
#
#     today = datetime.date.today()
#     next_monday = today - datetime.timedelta(days=today.weekday())
#     next_sunday = today - datetime.timedelta(days=-today.weekday(), weeks=1)
#     get_user = Timesheet.objects.filter(date__gte=next_sunday, date__lte=next_monday)
#
#     print(get_user)
#     dates = date_range2(next_sunday, next_monday)
#     for i in get_user:
#         print(i.status, i.date, dates)
#         if str(i.date) in dates:
#             if i.status == 'DetailsNone':
#                 with contextlib.suppress(UserHoliday.DoesNotExist):
#                     holiday = UserHoliday.objects.get(user_id=i.user_id, year=current_year())
#                     print(holiday)
#                     x = i.date
#                     if not HolidayCalender.objects.filter(date=i.date).exists() and not weekend(x):
#                         holiday.casual_leave_allowed -= 1
#                         AutoDetectCasualLeave.objects.create(user_id=i.user_id, created_date=i.date, year=current_year(), casual_logs=1)
#
#                         Notification.objects.create(user_id=i.user_id, notification_type='AUTO_CASUAL', message=f'leave have beeen detected {i.date}')
#
#
#                         holiday.save()
#
#             else:
#                 print('pass')
#     end = datetime.datetime.now()
#
#     Log_Schedulder.objects.create(name=f'Casual Logs {today} ' ,start_time =start ,end_time =end)
#
#
#
#
# import threading
# import time
#
# import schedule
#
#
# def run_continuously(interval=1):
#     """Continuously run, while executing pending jobs at each
#     elapsed time interval.
#     @return cease_continuous_run: threading. Event which can
#     be set to cease continuous run. Please note that it is
#     *intended behavior that run_continuously() does not run
#     missed jobs*. For example, if you've registered a job that
#     should run every minute and you set a continuous run
#     interval of one hour then your job won't be run 60 times
#     at each interval but only once.
#     """
#     cease_continuous_run = threading.Event()
#
#     class ScheduleThread(threading.Thread):
#         @classmethod
#         def run(cls):
#             while not cease_continuous_run.is_set():
#                 schedule.run_pending()
#                 time.sleep(interval)
#
#     continuous_thread = ScheduleThread()
#     continuous_thread.start()
#     return cease_continuous_run
#
#
#
#
# # schedule.every().day.at('03:10').do(check_timesheet_date)
# # schedule.every().thursday.at('10:37').do(casual_leave_timesheet)
# #
# #
# # # Start the background thread
# # stop_run_continuously = run_continuously()
#
# # Do some other things...
# #time.sleep(10)
#
# # Stop the background thread
# #stop_run_continuously.set()