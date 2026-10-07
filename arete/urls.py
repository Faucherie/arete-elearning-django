from django.urls import path
from . import api

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # Home page for user
    path('home/', views.home, name='home'),

    # Home page of another user
    path('user/<int:pk>/', views.user_home, name='user_home'),

    # Catalogue, courses and offerings
    path('catalogue/', views.OfferingList.as_view(), name='catalogue'),
    path('course/new/', views.CourseCreate.as_view(), name='course_create'),
    path('offering/new/', views.OfferingCreate.as_view(), name='offering_create'),
    path('offering/<int:pk>/', views.OfferingDetail.as_view(), name='offering_detail'),

    # Enrolment
    path('offering/<int:pk>/enrol/', views.Enrol.as_view(), name='enrol'),
    path('enrolment/<int:pk>/status/', views.EnrolmentStatusUpdate.as_view(), name='enrolment_status'),

    # Teacher only page
    path('teaching/', views.teacher_dashboard, name='teacher_dashboard'),

    # Materials
    path('offering/<int:pk>/material/new/', views.MaterialCreate.as_view(), name='material_create'),

    # Feedback and blog status updates
    path('offering/<int:pk>/feedback/new/', views.FeedbackCreate.as_view(), name='feedback_create'),
    path('status/new/', views.StatusUpdateCreate.as_view(), name='status_create'),

    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # Notifications
    path('notifications/read/', views.NotificationsMarkRead.as_view(), name='notifications_read'),

    # REST interface
    path('api/users/', api.UserList.as_view(), name='api_user_list'),
    path('api/user/<int:pk>/', api.UserDetail.as_view(), name='api_user_detail'),
    path('api/user/<int:pk>/status/', api.UserStatusUpdates.as_view(), name='api_user_status'),
    path('api/course/', api.CourseList.as_view(), name='api_course_list'),
    path('api/offering/', api.OfferingList.as_view(), name='api_offering_list'),
]