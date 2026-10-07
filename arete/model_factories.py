import factory

from django.contrib.auth.models import User, Group

from .models import *


class UserFactory(factory.django.DjangoModelFactory):
    """
    Valid User
    - username: user1 (incriments)
    - first_name: Test
    - last_name: Person1 (incriments)
    - email: user1@example.com (incriments)
    """
    username = factory.Sequence(lambda n: 'user%d' % n)
    first_name = "Test"
    last_name = factory.Sequence(lambda n: 'Person%d' % n)
    email = factory.Sequence(lambda n: 'user%d@example.com' % n)

    class Meta:
        model = User


class AppUserFactory(factory.django.DjangoModelFactory):
    """
    Valid AppUser
    - Base user
    - No media
    """
    user = factory.SubFactory(UserFactory)

    class Meta:
        model = AppUser


class StudentFactory(UserFactory):
    """
    Valid student group
    - Adds Student group to AppUser
    """
    @factory.post_generation
    def make_student(self, create, extracted, **kwargs):
        if not create:
            return
        AppUser.objects.create(user=self)
        self.groups.add(Group.objects.get(name="Students"))


class TeacherFactory(UserFactory):
    """
    Valid teacher group
    - Adds Teacher group to AppUSer
    """

    @factory.post_generation
    def make_teacher(self, create, extracted, **kwargs):
        if not create:
            return
        AppUser.objects.create(user=self)
        self.groups.add(Group.objects.get(name="Teachers"))


class CourseFactory(factory.django.DjangoModelFactory):
    """
    Valid course
    - code: CM0001 (increments)
    - title: Course 1 (increments)
    - desription: "A test course"
    """
    code = factory.Sequence(lambda n: 'CM%04d' % n)
    title = factory.Sequence(lambda n: 'Course %d' % n)
    description = "A test course."

    class Meta:
        model = Course


# valid offering
class OfferingFactory(factory.django.DjangoModelFactory):
    course = factory.SubFactory(CourseFactory)
    season = "WINTER"
    year = factory.Sequence(lambda n: 2020 + n)
    teacher = factory.SubFactory(UserFactory)

    class Meta:
        model = Offering


# valid enronlemt of student in offering
class EnrolmentFactory(factory.django.DjangoModelFactory):
    student = factory.SubFactory(UserFactory)
    offering = factory.SubFactory(OfferingFactory)

    class Meta:
        model = Enrolment

# Valid status update
class StatusUpdateFactory(factory.django.DjangoModelFactory):
    author = factory.SubFactory(UserFactory)
    offering = None
    body = factory.Sequence(lambda n: 'Working on task %d today.' % n)

    class Meta:
        model = StatusUpdate


# Valid feedback
class FeedbackFactory(factory.django.DjangoModelFactory):
    offering = factory.SubFactory(OfferingFactory)
    student = factory.SubFactory(UserFactory)
    rating = 4
    comment = "Clear and well paced."

    class Meta:
        model = Feedback

# Base valid registration form
class RegistrationDataFactory(factory.DictFactory):
    username = 'newperson'
    first_name = 'New'
    last_name = 'Person'
    email = 'new@example.ac.uk'
    password = 'password'
    group = 'Students'


# For tests that need to actualy use a password 
class LoginUserFactory(UserFactory):

    @factory.post_generation
    def set_login_password(self, create, extracted, **kwargs):
        if not create:
            return
        self.set_password(extracted or 'testpass')
        self.save()

# Factory object logged in w/ password as a Teacher
class LoginTeacherFactory(LoginUserFactory, TeacherFactory):
    pass

# Factory object logged in w/ password as a Student
class LoginStudentFactory(LoginUserFactory, StudentFactory):
    pass


# Factory object logged in w/ password as a Superuser (admin)
class SuperuserFactory(LoginUserFactory):
    is_superuser = True
    is_staff = True