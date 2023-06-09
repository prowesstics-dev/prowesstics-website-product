from lms.models import Notification, User, Notification_From_Admin


def check_for_new_msg(request):
    message = Notification.objects.filter(user=request.user.id)

    # print(message,'dddddddddddddddddddddddddddddddddddddd')
    notification = False
    if not notification:
        for msg in message:
            if not msg.seen:
                notification = True
                break
    if not notification:
        return {'notification': False}
    else:
        return {'notification': True}


def name_x(request):
    name = User.objects.filter(report_to=request.user.id).exists()
    seens = False
    print(seens, 'sssss')
    if name:
        seens = name
        print(seens, 'sssss')
        return {'seens': seens}
    else:
        seens = False
        return {'seens': seens}


from datetime import datetime


def get_active_notifications():

    notifications = []
    current_time = datetime.now()

    # Add notifications that are active at the current time to the list
    active_notifications = Notification_From_Admin.objects.filter(time__gte=current_time)
    for notification in active_notifications:
        notifications.append({
            'title': notification.title,
            'description': notification.description,
            'end_time': notification.time
        })

    return notifications


def notifications(request):

    notifications = get_active_notifications()
    return {'notifications': notifications}
