from django.apps import AppConfig
from django.db.models.signals import post_migrate


# Group permissions
TEACHER_PERMISSIONS = [
    'add_course', 'change_course',
    'add_offering', 'change_offering',
    'add_material',
    'add_assignment',
    'change_enrolment',        # R1h: remove or block a student
    'add_statusupdate',        # R1i says users, not only students
    'view_appuser',            # R1c: search for students and teachers
]

STUDENT_PERMISSIONS = [
    'add_enrolment',           # R1e: enrol on an offering
    'add_feedback',            # R1f
    'add_statusupdate',        # R1i
]



def create_groups(sender, **kwargs):
    from django.contrib.auth.models import Group, Permission

    teachers, created = Group.objects.get_or_create(name="Teachers")
    teachers.permissions.set(
        Permission.objects.filter(content_type__app_label='arete',
                                  codename__in=TEACHER_PERMISSIONS))

    students, created = Group.objects.get_or_create(name="Students")
    students.permissions.set(
        Permission.objects.filter(content_type__app_label='arete',
                                  codename__in=STUDENT_PERMISSIONS))


class AreteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'arete'

    def ready(self):
        post_migrate.connect(create_groups, sender=self)
