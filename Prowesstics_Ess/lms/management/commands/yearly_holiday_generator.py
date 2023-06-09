from django.core.management.base import BaseCommand, CommandError
from prowesstics.utils import UserHoliday, User
import datetime
from prowesstics.utils import current_year


class Command(BaseCommand):
    help = 'Yearly User Holiday '

    def handle(self, *args, **options):

        today = datetime.datetime.now()
        if today.month == 4 and today.day == 1 :
            users = User.objects.exclude(role__in=['CEO', 'ADMIN'])
            for user in users:
                print(user)
                if str(today.year + 1) in current_year():
                    UserHoliday.objects.create(
                        user=user, year=current_year()
                    )
            self.stdout.write(self.style.SUCCESS('Successfully created user'))
        self.stdout.write(self.style.SUCCESS('Not April 1st '))