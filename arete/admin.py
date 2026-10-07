from django.contrib import admin
from .models import *


class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'title')


class OfferingAdmin(admin.ModelAdmin):
    list_display = ('course', 'season', 'year', 'teacher')


class EnrolmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'offering', 'status', 'enrolled_at')
    list_filter = ('status',)


class AppUserAdmin(admin.ModelAdmin):
    list_display = ('user',)


admin.site.register(AppUser, AppUserAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Offering, OfferingAdmin)
admin.site.register(Enrolment, EnrolmentAdmin)
admin.site.register(Material)
admin.site.register(StatusUpdate)
admin.site.register(Feedback)
admin.site.register(Notification)
admin.site.register(Assignment)
