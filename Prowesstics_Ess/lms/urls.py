from django.conf.urls import url
from django.conf.urls.static import static
from django.http import HttpResponse
from django.urls import path
from django.contrib.auth.decorators import login_required
from prowesstics import settings
from . import views

urlpatterns = [

    path('logout/', views.logout_view, name='user_logout'),
    path('welcome/', views.dashboard, name='dashboard'),
    path('latest_leave/', views.latest_leave, name='latest_leave'),
    path('apply_leave/', views.apply_leave, name='apply_leave'),
    path('apply_ajax/', views.apply_leave_ajax, name='applyla'),
    path('my_profile/', views.my_profile, name='my_profile'),
    path('redeem/', views.redeem, name='redeem'),
    path('compensation/', views.compensation, name='compensation'),
    path('leave_tracker/', views.leave_tracker, name='leave_tracker'),
    path('latest_appications/', views.latest_appications, name='latest_applications'),
    path('rejected_applications/', views.rejected_applications, name='rejected_applications'),
    path('user_holiday_details', views.user_holiday_details, name="user_holiday_details"),
    path('leave_history/', views.user_leave_history, name='leave_history'),
    path('holiday_calender/', views.holiday_calender, name='holiday_calender'),
    path('leave_policy/', views.leave_policy, name='leave_policy'),
    path('create_user/', views.create_user, name='create_user'),
    path('modified_user/', views.modified_user, name='modified_user'),
    path('edit_user/', views.edit_user, name='edit_user'),
    path('delete_user/', views.delete_user, name='delete_user'),
    path('leave_details/', views.leave_details, name='leave_details'),
    path('user_leave_history/', views.user_leave_history, name='user_leave_history'),
    path('hr_leave_request/', views.hr_leave_request, name='hr_leave_request'),
    path('change_password/', views.change_password, name='change_password'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('organization_chart/', views.organisationchart, name='organization_chart'),
    path('user_details/', views.addressdetails, name='address'),
    path('edit_timesheet',views.edit_timesheet_,name="etime"),
    path('help-desk/', login_required(views.HelpDeskView.as_view()), name='help-desk'),
    path('tickets/', login_required(views.HelpDisk_Tickets.as_view()), name='tickets'),
    path('tickets_close/', login_required(views.HelpDisk_Tickets_Closed.as_view()), name='tickets_closed'),
    path('tickets_view/', login_required(views.Ticket_Viewer.as_view()), name='tickets_view'),
    path('timesheet',views.timesheet,name='timesheet'),
    path('get-manager/', views.get_manager, name="get_manager"),
    path('edit_timesheet_ajax',views.edit_timesheet_ajax,name="edit_timesheet"),
    path('timesheet-dashboard', views.hr_timesheet_dashboard, name='hr_timesheet_dashbord'),


    path('user-timesheet/', views.hr_timesheet_viewer, name='hr_timesheet_viwer'),
    path('excel',views.export_timesheet,name='timesheet_excel'),
    path('notification', views.notification_user, name='notification'),
    path('chart',views.dashboard_charts, name='chart'),
    path('casual-leave-detection',views.casual_leave_timesheet, name='casual-leave-detection'),
    path('daily-timesheet',views.check_timesheet_date,name='daily-timesheet'),
    path('my-skills',login_required(views.Myskills.as_view()),name ='my-skill'),
    path('my_skill_edit',views.my_skill_edit,name ='my-skill-edit'),
    # path('my_skill_admin', login_required(views.My_Skill_Admin.as_view()), name='my-skill-admin'),

    path('primary_my_skill_admin', login_required(views.My_Skill_Admin.as_view()), name='my-skill-admin'),
    path('secondary_my_skill_admin', login_required(views.Secondary_Skill_Admin.as_view()), name='secondary_my-skill-admin'),
    path('user_skill_table', login_required(views.Hr_Skill_Table.as_view()),name='user_skill_table'),

    path('announcement', views.announcement_admin, name='announcement'),

    path('training', views.training_page , name='training'),
    path('training_download/<str:file_name>/', views.training_download_file, name='training_download'),
    path('upload_training/', views.upload_training, name='upload_training'),
    path('delete_file/<int:file_id>/', views.delete_file, name='delete_file'),
    
    #logo
    path('upload_logo/', views.upload_logo, name='upload_logo'),
    path('delete_logo/<str:filename>/', views.delete_logo_file, name='delete_log'),
    path('logo-list/', views.logo_list, name='logo_list'),


    path('hr_pdf' , views.hr_pdf_view , name="hr_pdf_view"),
    path('hr_policy_view', views.hr_policy_pdf_view , name="hr_policy_view"),
    path('hr_update', views.hr_pdf_update, name="hr_update_view"),
    path('hr_policy_update', views.hr_policy_pdf_update, name="hr_policy_update"),

    # srini changes
    path('add_holiday/', login_required(views.Add_holiday.as_view()), name='add_holiday'),
    path('modify_holiday/', login_required(views.Modify_holiday.as_view()), name='modify_holiday'),
    path('delete_holiday/<int:id>/', views.delete_holiday, name='delete_holiday'),
    path('modify_or_delete_holiday/<int:id>/', views.modify_or_delete_holiday, name='modify_or_delete_holiday'),

]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
