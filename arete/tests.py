from django.test import TestCase
from django.db import IntegrityError
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from .permissions import is_teacher, is_student
from .models import *
from .model_factories import *

class TestSetup():
    """
    Create objects for tests
    """

    def factoryUser(self):
        self.user_a = UserFactory.create()

    def factoryTeachers(self):
        self.teacher_a = TeacherFactory.create()
        self.teacher_b = TeacherFactory.create()

    def factoryStudents(self):
        self.student_a = StudentFactory.create()
        self.student_b = StudentFactory.create()

    def factoryAdmin(self):
        self.admin = UserFactory.create(
            is_superuser=True, 
            is_staff=True)

    def factoryCourses(self):
        self.course_a = CourseFactory.create()
        self.course_b = CourseFactory.create()

    def factoryOfferings(self):
        self.offering_a = OfferingFactory.create(
            course=self.course_a,
            teacher=self.teacher_a)
        self.offering_b = OfferingFactory.create(
            course=self.course_b,
            teacher=self.teacher_b)
    


class ModelConstraintTest(TestSetup, TestCase):
    """
    Test Arete models behavior
    - Confirm groups work
    - Some permision checks
    - Creating objects
    """
    
    def setUp(self):
        """
        Create the test objects from the models:
        """
        self.factoryTeachers()
        self.factoryStudents()

        # create a basic user with no group
        self.factoryUser()

        # Create a course and an offering for the course
        self.factoryCourses()
        self.factoryOfferings()

    # -- Groups and permissions tests --
    
    def test_user_groups(self):
        """
        Test that student is in the Students group and teacher is in the Teachers group
        """
        self.assertTrue(self.student_a.groups.filter(name='Students').exists())
        self.assertTrue(self.teacher_a.groups.filter(name='Teachers').exists())
        self.assertFalse(self.user_a.groups.filter(name='Students').exists())
        self.assertFalse(self.user_a.groups.filter(name='Teachers').exists())

    def test_only_teacher_add_offering(self):
        """
        Test that only teacher can add an offering to a course. Students should not have permission to add an offering.
        """
        self.assertTrue(self.teacher_a.has_perm('arete.add_offering'))
        self.assertFalse(self.student_a.has_perm('arete.add_offering'))
        self.assertFalse(self.user_a.has_perm('arete.add_offering'))
    
    def test_only_teacher_add_course(self):
        """
        Test that only teacher can add a course. Students should not have permission to add a course.
        """
        self.assertTrue(self.teacher_a.has_perm('arete.add_course'))
        self.assertFalse(self.student_a.has_perm('arete.add_course'))
        self.assertFalse(self.user_a.has_perm('arete.add_course'))

    def test_only_teacher_change_course(self):
        """
        Test that only teacher can change a course. Students should not have permission to change a course.
        """
        self.assertTrue(self.teacher_a.has_perm('arete.change_course'))
        self.assertFalse(self.student_a.has_perm('arete.change_course'))
        self.assertFalse(self.user_a.has_perm('arete.change_course'))

    # -- Model Integrity tests --
    
    def test_course_code_is_unique(self):
        """
        A course code is the catalogue identity, so it cannot repeat. 
        - Pass = IntegrityError is raised when trying to create a course with the same code as an existing course.
        """
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Course.objects.create(code=self.course_a.code,
                                      title='Duplicate')

    def test_offering_season_year_is_unique(self):
        """
        Test that two offerings for the same course cannot have the same season and year.
        - Pass = IntegrityError is raised when trying to create an offering with the same season and year as an existing offering for the same course.
        """
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Offering.objects.create(course=self.course_a,
                                        season=self.offering_a.season,
                                        year=self.offering_a.year,
                                        teacher=self.teacher_a)

    def test_offering_season_year_is_not_unique_for_different_season_year(self):
        """
        Test that an offering can be created with the same course but different season year combination. 
        - Pass = No IntegrityError is raised when trying to create an offering with the same course but different season and year.
        """
        OfferingFactory.create(course=self.course_a, season="SUMMER",
                               year=self.offering_a.year, teacher=self.teacher_a)
        OfferingFactory.create(course=self.course_a, season="SPRING",
                               year=self.offering_a.year, teacher=self.teacher_a)
        self.assertEqual(self.course_a.offerings.count(), 3)



class RegistrationTest(TestCase):
    """
    Tests Arete Registraion pipline
    - register template exists
    - Valid forms
    - Bad forms
    - Model validation (duplicate, stored password is hashed)
    """

    def test_get_register_returns_form(self):
        """
        Confirm registration template exists
        """
        response = self.client.get('/register/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('user_form', response.context)
        self.assertIn('profile_form', response.context)

    # -- Valid Form --
    
    def test_register_teacher_joins_teachers_group(self):
        """
        Teacher group
        """
        self.client.post('/register/', RegistrationDataFactory(group='Teachers'))
        user = User.objects.get(username='newperson')
        self.assertTrue(user.groups.filter(name='Teachers').exists())
        self.assertTrue(user.has_perm('arete.add_offering'))

    def test_register_student_joins_students_group(self):
        """
        Student group
        """
        self.client.post('/register/', RegistrationDataFactory(group='Students'))
        user = User.objects.get(username='newperson')
        self.assertTrue(user.groups.filter(name='Students').exists())
        self.assertFalse(user.has_perm('arete.add_offering'))

    def test_register_creates_the_app_user_profile(self):
        """
        The profile row, which the OneToOneField cannot have before the user
        """
        self.client.post('/register/', RegistrationDataFactory())
        user = User.objects.get(username='newperson')
        self.assertTrue(AppUser.objects.filter(user=user).exists())

    def test_register_stores_the_real_name(self):
        """
        First and last name reach auth_user, not AppUser
        """
        self.client.post('/register/', RegistrationDataFactory())
        user = User.objects.get(username='newperson')
        self.assertEqual(user.first_name, 'New')
        self.assertEqual(user.last_name, 'Person')

    # -- Bad Form --

    def test_register_without_group_is_rejected(self):
        """
        Registering new user with no group 
        """
        # Get the factory object data from registration
        data = RegistrationDataFactory()

        # Delete the group
        del data['group']

        # Try to register
        response = self.client.post('/register/', data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='newperson').exists())

    def test_register_without_first_name_is_rejected(self):
        """
        No first name
        """
        self.client.post('/register/', RegistrationDataFactory(first_name=''))
        self.assertFalse(User.objects.filter(username='newperson').exists())

    def test_register_without_last_name_is_rejected(self):
        """
        No last name
        """
        self.client.post('/register/', RegistrationDataFactory(last_name=''))
        self.assertFalse(User.objects.filter(username='newperson').exists())

    def test_register_invalid_email_is_rejected(self):
        """
        Invalid email
        """
        response = self.client.post('/register/', RegistrationDataFactory(email='not-an-email'))
        self.assertFalse(User.objects.filter(username='newperson').exists())
        self.assertIn('email', response.context['user_form'].errors)

    # Invalid group
    def test_register_invalid_group_is_rejected(self):
        response = self.client.post('/register/', RegistrationDataFactory(group='Wizards'))
        self.assertFalse(User.objects.filter(username='newperson').exists())
        self.assertIn('group', response.context['profile_form'].errors)

    # -- Registration Model Check --

    # Duplicate username
    def test_register_duplicate_username_is_rejected(self):
        User.objects.create_user(username='newperson', password='x')
        self.client.post('/register/', RegistrationDataFactory())
        self.assertEqual(User.objects.filter(username='newperson').count(), 1)

    def test_registered_password_is_hashed_not_stored(self):
        """
        The password is hashed on the way in, and the account really works
        """

        self.client.post('/register/', RegistrationDataFactory())
        user = User.objects.get(username='newperson')
        self.assertNotEqual(user.password, 'password')
        self.assertTrue(user.password.startswith('pbkdf2_'))
        self.assertTrue(self.client.login(username='newperson',
                                          password='password'))


class AuthenticationTest(TestCase):
    """
    Test Login and Logout
    - Valid login
    - Bad login
    """

    student = None
    def setUp(self):
        self.student = LoginStudentFactory.create()

    # -- Valid Login --

    def test_valid_credentials_log_user_in(self):
        """
        Valid login and user
        - Redirect to /home after login
        """
        response = self.client.post('/login/',
                                    {'username': self.student.username,
                                     'password': 'testpass'})
        self.assertRedirects(response, '/home/')
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    # -- Bad Login --

    
    def test_invalid_credentials_do_not_log_user_in(self):
        """
        Invalid password
        - Test app responds password is wrong
        """

        # Valid user logs in with wrong password
        response = self.client.post('/login/',
                                    {'username': self.student.username,
                                     'password': 'wrongpass'})
        # Validate the app rejects the login attempt
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    
    def test_inactive_user_cannot_log_in(self):
        """
        Vaild user but flagged inactive
        """

        self.student.is_active = False
        self.student.save()
        response = self.client.post('/login/',
                                    {'username': self.student.username,
                                     'password': 'testpass'})
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    # -- Valid logout --
        
    # -- Bad Logout --


class AccessControlTest(TestSetup, TestCase):
    """
    Permission Gates
    - Teacher only Access
    - Homepage
    """

    def setUp(self):
        self.factoryTeachers()
        self.factoryStudents()
        self.factoryAdmin()
        self.factoryCourses()
        self.factoryOfferings()

    # -- Teacher only Restrictions --

    def test_anonymous_user_is_redirected_to_login(self):
        """
        non logged in user
        - 302 code redirecting the user to the login page
        """
        # get request to teacher only permision
        response = self.client.get('/teaching/')
        self.assertRedirects(response, '/login/?next=/teaching/')
        self.assertEqual(response.status_code, 302)

    # Student user tries to access teacher page
    # - 403 error: Denied permision
    def test_student_rejected_from_teacher_dashboard(self):
        # Log in as the student user
        self.client.force_login(self.student_a)

        # Attempt to access the restricted teacher URL
        response = self.client.get('/teaching/')

        # Assert permission is denied (HTTP 403)
        self.assertEqual(response.status_code, 403)

        # Confirm the teacher dashboard template was not rendered
        self.assertTemplateNotUsed(response, 'arete/teacher_dashboard.html')

    def test_teacher_is_allowed(self):
        """
        Teacher is granted access
        - 200 code: OK
        """

        # Log in as the authorized teacher user
        self.client.force_login(self.teacher_a)

        # Access the teacher dashboard
        response = self.client.get('/teaching/')
        
        # Assert the request is successful (HTTP 200)
        self.assertEqual(response.status_code, 200)
        
        # Confirm the correct dashboard template is used
        self.assertTemplateUsed(response, 'arete/teacher_dashboard.html')

    def test_teacher_sees_only_their_own_offerings(self):
        """
        Teacher A and teacher B each see only their own offering
        - the gate lets both in, the view's filter decides what each sees
        """

        # Verify Teacher A only sees Offering A
        self.client.force_login(self.teacher_a)
        response = self.client.get('/teaching/')
        self.assertIn(self.offering_a, response.context['offerings'])
        self.assertNotIn(self.offering_b, response.context['offerings'])

        # Verify Teacher B only sees Offering B
        self.client.force_login(self.teacher_b)
        response = self.client.get('/teaching/')
        self.assertIn(self.offering_b, response.context['offerings'])
        self.assertNotIn(self.offering_a, response.context['offerings'])

    # Superuser (admin) needs to have access to all permisions while in none
    # - 200 code: OK, (superuser has access)
    # - Superuser is in neither group
    def test_superuser_passes_the_gate_but_is_not_a_teacher_or_student(self):
        # create superuser
        self.client.force_login(self.admin)

        # Varify superuse access to teacher only page
        response = self.client.get('/teaching/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'arete/teacher_dashboard.html')

        # Varify superuser is neither in sutdent or teacher group
        self.assertFalse(is_teacher(self.admin))
        self.assertFalse(is_student(self.admin))

    # -- Home pages --

    # Teacher sees the offering they teach, not another teacher's
    def test_teacher_home_lists_only_their_own_offerings(self):
        # create Teacher `A`
        self.client.force_login(self.teacher_a)

        # Go to Teacher `A`'s homepage
        response = self.client.get('/home/')
        self.assertEqual(response.status_code, 200)

        # Varify Teacher `A` has Offerings `A` not Offerings `B`
        self.assertIn(self.offering_a, response.context['offerings'])
        self.assertNotIn(self.offering_b, response.context['offerings'])

    # Home pages are visible to other users
    # - 200 code: OK, and the page is about the person asked for
    def test_logged_in_user_can_view_another_users_home(self):
        # create Student `A`
        self.client.force_login(self.student_a)

        # As Student `A` access Teacher `A`'s homepage
        response = self.client.get('/user/%d/' % self.teacher_a.pk)
        self.assertEqual(response.status_code, 200)

        # Varify we visted Teacher `A`s page
        self.assertEqual(response.context['profile_user'], self.teacher_a)


class HomePageTest(TestSetup, TestCase):
    """
    Home Page Functionality

    """
    def setUp(self):
        self.factoryTeachers()
        self.factoryStudents()
        self.factoryAdmin()
        self.factoryCourses()
        self.factoryOfferings()

    # Student sees an ACTIVE enrolment, not a REMOVED one
    def test_student_home_lists_only_active_enrolments(self):
        EnrolmentFactory.create(student=self.student_a, offering=self.offering_a)
        EnrolmentFactory.create(student=self.student_a, offering=self.offering_b,
                                status="REMOVED")
        self.client.force_login(self.student_a)
        response = self.client.get('/home/')
        self.assertIn(self.offering_a, response.context['offerings'])
        self.assertNotIn(self.offering_b, response.context['offerings'])

    # Student sees a deadline next week, not one last week
    def test_student_home_lists_only_upcoming_deadlines(self):
        EnrolmentFactory.create(student=self.student_a, offering=self.offering_a)
        upcoming = Assignment.objects.create(offering=self.offering_a, title='Coursework',
                                             due_date=timezone.now() + timedelta(days=7))
        past = Assignment.objects.create(offering=self.offering_a, title='Midterm',
                                         due_date=timezone.now() - timedelta(days=7))
        self.client.force_login(self.student_a)
        response = self.client.get('/home/')
        self.assertIn(upcoming, response.context['deadlines'])
        self.assertNotIn(past, response.context['deadlines'])

    # non logged in user
    # - 302 code redirecting the user to the login page
    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get('/user/%d/' % self.teacher_a.pk)
        self.assertRedirects(response, '/login/?next=/user/%d/' % self.teacher_a.pk)

    # Administrator is in neither group: same page, no courses
    def test_administrator_home_renders_with_no_courses(self):
        self.client.force_login(self.admin)
        response = self.client.get('/home/')
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['offerings'])

    # No such user
    # - 404 code: not found
    def test_missing_user_is_404(self):
        self.client.force_login(self.student_a)
        response = self.client.get('/user/999999/')
        self.assertEqual(response.status_code, 404)

# Search for users home helper function unit tests

class CourseTest(TestSetup, TestCase):
    """
    Course, Offerings and Catalogue 
    """
    # - error Can make courses for the year -1
    # - Probably want logic gate for that between 2020 and 3000?

    def setUp(self):
        self.factoryTeachers()
        self.factoryStudents()
        self.factoryAdmin()
        self.factoryCourses()
        self.factoryOfferings()

    # -- Creating courses and offerings --

    def test_teacher_can_create_course(self):
        """
        Teacher adds a catalogue entry
        - 302 code: on to the new offering form
        - Count increase in courses on db after creation
        - Check course attributes
        """
        # create teacher
        self.client.force_login(self.teacher_a)
        # get current courses length
        before = Course.objects.count()
        # create new course 
        response = self.client.post('/course/new/', {'code': 'CM3035', 'title': 'Advanced Web'})

        # Validate redirect to offering page with the new course as the offerings course 
        self.assertRedirects(response, '/offering/new/')
        # Validate the pk of the new cousre (code: CM3035) is now in the db
        self.assertTrue(Course.objects.filter(code='CM3035').exists())
        # Validate there is a new cousre added to db by length
        self.assertEqual(Course.objects.count(), before + 1)

    def test_student_cannot_create_course(self):
        """
        Student cannot to add a course
        - 403 error: Denied permision
        """
        # create student
        self.client.force_login(self.student_a)
        # get current courses length
        before = Course.objects.count()
        # create course
        response = self.client.post('/course/new/', {'code': 'CM3035', 'title': 'Advanced Web'})

        # Validate course made by student is rejected
        self.assertEqual(response.status_code, 403)
        # Validate new course pk is not in db
        self.assertFalse(Course.objects.filter(code='CM3035').exists())
        # Validate the catalogue length of cousrses has not increased
        self.assertEqual(Course.objects.count(), before)

    def test_teacher_can_create_offering(self):
        """
        Teacher creates a new offering
        - Same offering as offering_a but in Spring, not Winter
        """
        # create teacher
        self.client.force_login(self.teacher_a)
        # get current offerins length
        before = Offering.objects.count()
        # create offering 
        response = self.client.post('/offering/new/', {'course': self.course_a.pk,
                                                       'season': "SPRING",
                                                       'year': self.offering_a.year})

        # find the new offering by course, season and year
        offering = Offering.objects.get(course=self.course_a, season="SPRING", year=self.offering_a.year)
        # Validate redirect to offering detail page for the pk of new offerings
        self.assertRedirects(response, '/offering/%d/' % offering.pk)
        # Validate the new offering belongs to the teacher who made it
        self.assertEqual(offering.teacher, self.teacher_a)
        # Validate there is a new offering added to db by length
        self.assertEqual(Offering.objects.count(), before + 1)

    def test_duplicate_offering(self):
        """
        Duplicate Offering Rejected
        - Same course, season, and year
        """
        # create teacher
        self.client.force_login(self.teacher_a)
        # get current offerins length
        before = Offering.objects.count()
        # create duplicate offering to `TestSetup.factoringOfferings` object `offering_a`
        response = self.client.post('/offering/new/', {'course': self.course_a.pk,
                                                       'season': self.offering_a.season,
                                                       'year': self.offering_a.year})
        # Validate the app still runs with out crashing
        self.assertEqual(response.status_code, 200)
        # Validate the `OfferingForm` reported an error
        self.assertTrue(response.context['form'].errors)
        # Validate the length of offerings has not increased
        self.assertEqual(Offering.objects.count(), before)

    #def test_student_cannot_create_offering(self):
        """
        """

    # -- The catalogue and the offering page --

class EnrolmentTest(TestSetup, TestCase):

    def setUp(self):
        self.factoryTeachers()
        self.factoryStudents()
        self.factoryCourses()
        self.factoryOfferings()

    # Student enrols and is ACTIVE
    def test_student_can_enrol(self):
        self.client.force_login(self.student_a)
        response = self.client.post('/offering/%d/enrol/' % self.offering_a.pk)
        self.assertRedirects(response, '/offering/%d/' % self.offering_a.pk)
        enrolment = Enrolment.objects.get(student=self.student_a, offering=self.offering_a)
        self.assertEqual(enrolment.status, "ACTIVE")

    # Student errolls but is blocked

    # Student enrols but was prior removed now active

    # teacher removes student

    # teacher blocks student

    # teacher cannot enroll in offering

    # admin cannot enroll in offering

# Material Tests

# Feedback Blog posts Tests

# Serializer tests

# API tests

# Notification tests

