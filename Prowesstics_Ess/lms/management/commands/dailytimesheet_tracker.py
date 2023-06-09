from datetime import datetime

from django.db.models import Q

from lms.models import Notification, Log_Schedulder, Timesheet, HolidayRequest, HolidayCalender, User
from django.core.management.base import BaseCommand
from django.utils import timezone

from prowesstics.utils import weekend
import datetime
from prowesstics.utils import find_no_days, current_year




class Command(BaseCommand):
    help = 'test scheduler'

    def handle(self, *args, **kwargs):
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
                print(holi.leaves_sep_v)
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

                    # print('iffffffffffff')
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
                                if holi.category == 'compensation':
                                    status='Compensation Leave'

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
                                if holi.category == 'compensation':
                                    status = 'Compensation Leave'


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
        time = timezone.now().strftime('%X')
        self.stdout.write("scheduler started %s" % time)

