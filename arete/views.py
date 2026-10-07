# Http
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.shortcuts import get_object_or_404

# CRUD
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import View, ListView, DetailView

# Permisions
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin 
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied

# other
from django.db.models import Q  # search query
from django.utils import timezone

# local
from .models import *
from .forms import *
from .permissions import *

# -- URL Pages --

@login_required(login_url='login')
def home(request):
    """
    Home page
    - This is only accessible by an authenticated user
    - Only shows the current logged in user's home page
    - Uses helper function `home_context` to deterime who the user is and what to show
    - URL: `/home/`
    """
    # Get the context for the user
    context = home_context(request.user)

    # Create an status update, only available to the user of thier own homepage
    context['status_form'] = StatusUpdateForm(user=request.user)

    # your notifications, newest first, on your own home page only
    # Show only unread notifications
    context['notifications'] = Notification.objects.filter(recipient=request.user, is_read=False)[:20]
    context['unread_count'] = Notification.objects.filter(recipient=request.user, is_read=False).count()

    # Use group permision flag to check if teacher
    if is_teacher(request.user):

        # Retrieve the search parameter from the URL
        context['query'] = request.GET.get('q', '')

        # Pass the query to the user search helper
        context['results'] = search_users(context['query'])

    return render(request, 'arete/home.html', context)

@login_required(login_url='login')
def user_home(request, pk):
    """
    User Home page
    - Current User requests the homepage of another user
    - Current user is logged in
    - All users pages are vistable by other authernticated users
    - Renders the home page for another profile
    - URL: `/user/<user id>/`
    """
    profile_user = get_object_or_404(User, pk=pk)
    return render(request, 'arete/home.html', home_context(profile_user))

def index(request):
    """
    Index page
    - Landing page for non logged in users
    - Has a list of all courses
    """
    return render(request, 'arete/index.html',
                  {'courses': Course.objects.all()})

@login_required(login_url='login')
# filter out students (user withoug add_offering permisions)
@permission_required('arete.add_offering', raise_exception=True)
def teacher_dashboard(request):
    """
    Teacher_dashboard page
    - teacher only page. as a test
    - First check if user is logged in:
    - If true: teacher or admin -> redirect to 'arete/teacher_dashboard.html'
    - If false: 302 error -> redirect to login page
    - Next, if not a teacher:
    - Permision denied: 403 error as the user/student should not be here.
    """
    # Check if the user-teacher is the teacher for the offering
    offerings = Offering.objects.filter(teacher=request.user)
    return render(request, 'arete/teacher_dashboard.html',
                  {'offerings': offerings})

class Enrol(PermissionRequiredMixin, View):
    """
    Enrollment page for students to select an offering
    - Access:
        - Student
        - Teacher
    - Permission: add_enrolment
    - If teacher removes a student, the student can re-enroll
    - If teacher blocks a student, the student is banned from offering (not course)
    - post(): Checks the students status to determin if they may enroll
    """
    permission_required = 'arete.add_enrolment'
    login_url = 'login'
    http_method_names = ['post']

    def post(self, request, pk):
        # Check if offering exists
        offering = get_object_or_404(Offering, pk=pk)
        # Check student status for offering
        enrolment = Enrolment.objects.filter(offering=offering, student=request.user).first()
        # First time enrolling
        if enrolment is None:
            Enrolment.objects.create(offering=offering, student=request.user)

            # notify teacher of student enrolment
            notify(offering.teacher, "%s enrolled on %s" % (request.user.username, offering), offering=offering, url=reverse('offering_detail', kwargs={'pk': offering.pk}))
            
        # Prior enrolment, blocked, cant enroll
        elif enrolment.status == "BLOCKED":
            raise PermissionDenied("You are blocked from this offering.")
        # Prior enrolment, re-added
        elif enrolment.status == "REMOVED":
            enrolment.status = "ACTIVE"
            enrolment.save()

            # notify teacher of student enrolment
            notify(offering.teacher, "%s enrolled on %s" % (request.user.username, offering), offering=offering, url=reverse('offering_detail', kwargs={'pk': offering.pk}))

        # After enrolling the student redirect them to the detail page for the offering 
        return HttpResponseRedirect(reverse('offering_detail', kwargs={'pk': offering.pk}))



# --- CRUD Pages ---

# ---- CREATE ----

class CourseCreate(PermissionRequiredMixin, CreateView):
    """
    CREATE Courses
    - Teacher creates course (PERMISION: add_course)
    - User must be logedin
    """
    permission_required = 'arete.add_course'
    login_url = 'login'
    model = Course
    form_class = CourseForm
    template_name = 'arete/course_form.html'

    def get_success_url(self):
        return reverse('offering_create')

class OfferingCreate(PermissionRequiredMixin, CreateView):
    """
    CREATE Offering
    - Teacher creates offering (PERMISSION: add_offering)
    - User must be logged in
    - form_valid()
    """
    permission_required = 'arete.add_offering'
    login_url = 'login'
    model = Offering
    form_class = OfferingForm
    template_name = 'arete/offering_form.html'

    def form_valid(self, form):
        """
        save/create the offering
        """
        # Add the current user (assumed to to be a teacher) as the teacher for the offering
        form.instance.teacher = self.request.user
        # Save the offering
        return super().form_valid(form)

    def get_success_url(self):
        """
        Returns the URL the DETAIL page of the new offering
        """
        return reverse('offering_detail', kwargs={'pk': self.object.pk})

class MaterialCreate(PermissionRequiredMixin, CreateView):
    """
    Teacher CREATES Material for their Offering
    - Access: Teacher of the Offering only. No other teacher
    - Upload the file to db.
    - Stored in /media/
    - Known issue: The file is stored in /media/ as a static file. Thus access is limited via links not a correct URL.
    """
    permission_required = 'arete.add_material'
    login_url = 'login'
    model = Material
    form_class = MaterialForm
    template_name = 'arete/material_form.html'

    def has_permission(self):
        """
        Gets the Offering in question. 
        - Matches user to the offerings teacher
        """
        if not super().has_permission():
            return False
        self.offering = get_object_or_404(Offering, pk=self.kwargs['pk'])
        return self.offering.teacher == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['offering'] = self.offering
        return context

    def form_valid(self, form):
        """
        Sets the user as the uploader and offering
        """
        # save the materal
        form.instance.offering = self.offering
        form.instance.uploaded_by = self.request.user
        response = super().form_valid(form)

        # notify enrolled students of new material
        for enrolment in Enrolment.objects.filter(offering=self.offering, status="ACTIVE").select_related('student'):
            notify(enrolment.student, "New material on %s: %s" % (self.offering, self.object.title), offering=self.offering, url=reverse('offering_detail', kwargs={'pk': self.offering.pk}))

        return response

    def get_success_url(self):
        return reverse('offering_detail', kwargs={'pk': self.offering.pk})

class FeedbackCreate(PermissionRequiredMixin, CreateView):
    """
    Student leaves feedback on Offering
    - Access: Student enrolled in offering
    """
    permission_required = 'arete.add_feedback'
    login_url = 'login'
    model = Feedback
    form_class = FeedbackForm
    template_name = 'arete/feedback_form.html'

    def has_permission(self):
        if not super().has_permission():
            return False
        self.offering = get_object_or_404(Offering, pk=self.kwargs['pk'])
        return Enrolment.objects.filter(offering=self.offering, student=self.request.user,
                                        status="ACTIVE").exists()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['offering'] = self.offering
        return context

    def form_valid(self, form):
        if Feedback.objects.filter(offering=self.offering, student=self.request.user).exists():
            form.add_error(None, "You have already left feedback for this offering.")
            return self.form_invalid(form)
        form.instance.offering = self.offering
        form.instance.student = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('offering_detail', kwargs={'pk': self.offering.pk})

class StatusUpdateCreate(PermissionRequiredMixin, CreateView):
    """
    User adds a status update to their own homepage
    - Access: any loged in user, on thier own homepage
    - Issue: No update, delete functionality yet for created posts
    """
    permission_required = 'arete.add_statusupdate'
    login_url = 'login'
    model = StatusUpdate
    form_class = StatusUpdateForm
    http_method_names = ['post']

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def form_invalid(self, form):
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('home')

# ---- READ ----

class OfferingList(LoginRequiredMixin, ListView):
    """
    LIST Offerings
    - The list of every offering, for any loged in user
    - get_queryset(): Every offering with its course and teacher
    - get_context_data(): Adds the ids to the contex dict for every offering the user is active or blocked from.
    """
    login_url = 'login'
    model = Offering
    context_object_name = 'offerings'
    template_name = 'arete/catalogue.html'

    def get_queryset(self):
        """
        Returns every offering with corresponding linked Course and Teacher
        """
        return Offering.objects.select_related('course', 'teacher')

    def get_context_data(self, **kwargs):
        """
        Add to the template's data
        - offerings: already added by ListView
        - active_ids: offerings the user is enrolled on
        - blocked_ids: offerings the user is blocked from
        """
        context = super().get_context_data(**kwargs)

        # Get the Enrolment status for all the current loged in user's offerings
        mine = Enrolment.objects.filter(student=self.request.user)

        # Offerings ids, split by enrolment status
        context['active_ids'] = list(mine.filter(status="ACTIVE").values_list('offering_id', flat=True))
        context['blocked_ids'] = list(mine.filter(status="BLOCKED").values_list('offering_id', flat=True))
        return context


class OfferingDetail(UserPassesTestMixin, DetailView):
    """
    DETAIL Offering
    - Read all the data for a given offering
    - Access: 
        - The offering's teacher
        - Enrolled students
        - Admin
    - test_func(): Can this user open this page
    - get_context_data(): Prevents non offering teachers from geting roster
    """
    login_url = 'login'
    model = Offering
    context_object_name = 'offering'
    template_name = 'arete/offering_detail.html'

    def test_func(self):
        """
        Can this user open this offering's page
        - True: The page is shown
        - False: 
            - If the user is logged out: The user is redirected to login page.
            - If the user is logged in: The user gets 403 Forbidden error code.
        """
        user = self.request.user
        # turn away non logged in user
        if not user.is_authenticated:
            return False
        offering = self.get_object()

        # user has permision to access page
        if user.is_superuser or offering.teacher == user:
            return True
        # check if user is enroled in offering
        return Enrolment.objects.filter(offering=offering, student=user,
                                        status="ACTIVE").exists()

    def get_context_data(self, **kwargs):
        """
        Add to the template's data
        - offering: already added by DetailView
        - is_owner: Set the offerings teacher as owner
        - roster: every enrolment on this offering, for the owner only.
          None for students, so they never receive the student list
        """
        context = super().get_context_data(**kwargs)
        user = self.request.user
        is_owner = self.object.teacher == user or user.is_superuser

        context['is_owner'] = is_owner
        context['roster'] = None

        if is_owner:
            # Students in offering
            context['roster'] = Enrolment.objects.filter(offering=self.object).select_related('student')

        # Path to files uploaded by teacher for offering
        context['materials'] = Material.objects.filter(offering=self.object)

        # Blog status updates
        context['feedback'] = Feedback.objects.filter(offering=self.object).select_related('student')
        context['can_leave_feedback'] = (
            Enrolment.objects.filter(offering=self.object, student=user, status="ACTIVE").exists()
            and not Feedback.objects.filter(offering=self.object, student=user).exists())

        # Chat room for offering
        context['chat_room'] = 'room%d' % self.object.pk
        return context

# --- Update ---

class EnrolmentStatusUpdate(PermissionRequiredMixin, UpdateView):
    """
    Teacher Updates the Enrolemnt Status for Students in their Offering
    - Access: Teacher of Offering
    - Permission: change_enrolment
    - Options: 
        - Remove: Unenroll an active student
        - Block: Remove and preven student from enrolling again in this offering
        - Restore: Re-enroll student in this offering
    """
    permission_required = 'arete.change_enrolment'
    login_url = 'login'
    model = Enrolment
    fields = ['status']
    http_method_names = ['post']

    def has_permission(self):
        """
        Only the Teacher of the offering or superuser has access
        """
        if not super().has_permission():
            return False
        user = self.request.user
        return self.get_object().offering.teacher == user or user.is_superuser

    def form_invalid(self, form):
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('offering_detail', kwargs={'pk': self.object.offering.pk})

# --- Delete ---

# -- Helper Functions --

def home_context(profile_user):
    """
    Context for home pages
    - Not a url page
    - Serves the users unique data
    - Checks if user is teacher or student using group membership flag (@permissions.py)

    Teacher Context:
    - Offerings they are teaching

    Student Context:
    - Offerings they are currently enrolled in
    - Upcoming deadlines
    - Past dealines
    """

    deadlines = None
    past_deadlines = None
 
    # The current user is a teacher
    if is_teacher(profile_user):
        # get all the offerings the teacher teaches.
        offerings = Offering.objects.filter(teacher=profile_user)

    # The current user is a student
    elif is_student(profile_user):
        # get all the offering the student is activly enrolled in
        offerings = Offering.objects.filter(enrolment__student=profile_user,
                                            enrolment__status="ACTIVE")
        # For each offering get the deadlines
        assignments = Assignment.objects.filter(
            offering__enrolment__student=profile_user,
            offering__enrolment__status="ACTIVE")
        now = timezone.now()
        # Upcoming deadlines, soonest first
        deadlines = assignments.filter(due_date__gte=now)
        # Deadlines that have passed, most recent first
        past_deadlines = assignments.filter(due_date__lt=now).order_by('-due_date')

    # profile is neither a student or teacher, thus admin
    # - This means anyone will see a homepage for admin which is wreird
    else:
        # dont need anything
        offerings = None

    # The data retured to the home page based who the user is
    return {'profile_user': profile_user,
            'profile_is_teacher': is_teacher(profile_user),
            'profile_is_student': is_student(profile_user),
            'offerings': offerings,
            'deadlines': deadlines,
            'past_deadlines': past_deadlines,
            'updates': StatusUpdate.objects.filter(author=profile_user)}

def search_users(query):
    """
    Search for active users by username, first name, or last name.
    """
    # Clean the search string by removing extra whitespace
    cleaned_query = query.strip() if query else ""

    # Return an empty QuerySet instead of None if no search term is provided
    if not cleaned_query:
        return User.objects.none()

    # 3. Filter for active users matching any of the name criteria
    return User.objects.filter(
        Q(is_active=True) & (
            Q(username__icontains=cleaned_query) |
            Q(first_name__icontains=cleaned_query) |
            Q(last_name__icontains=cleaned_query)
        )
    ).distinct()

def notify(recipient, message, offering=None, url=None):
    """
    - R1k: IF a student enrolls in course notify teacher
    - R1l: If a teacher adds material to a cousrse notify enrolled student
    """
    return Notification.objects.create(recipient=recipient, message=message,
                                       offering=offering, url=url)

class NotificationsMarkRead(LoginRequiredMixin, View):
    """
    Once a user logs in, mark any of their notifications as read
    """
    login_url = 'login'
    http_method_names = ['post']

    def post(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return HttpResponseRedirect(reverse('home'))

# -- Authentication --

def register(request):
    """
    Register view for handling user registration.
    - Successful registration redirects to the login page.
    - Invalid form data returns error messages.
    """

    registered = False

    # User has sent us data (filled in registation forum)
    if request.method == 'POST':
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST, files=request.FILES)

        # The users forms are correct
        if user_form.is_valid() and profile_form.is_valid():

            # create the django user
            user = user_form.save(commit=False)
            user.set_password(user.password)
            user.save()

            # create the profile object
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()

            # We dont sanitize the photo path here for AppUser.photo because the models data type ImagField handles it.

            # apply the group for the profile permissions
            group = Group.objects.get(
                name=profile_form.cleaned_data['group'])
            user.groups.add(group)

            # Flip the proflie flag
            registered = True

        # Problem with user form
        else:
            print(user_form.errors, profile_form.errors)

    # User has not sent data, so create blank registration form
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    # render register template
    return render(request, 'arete/register.html',
                  {'user_form': user_form,
                   'profile_form': profile_form,
                   'registered': registered})


def user_login(request):
    """
    Login view for handling user authentication.
    - Successful login redirects to the index page.
    - Invalid login details return an error message.
    """
    # Check if the request is a POST (the user has submitted the login form)
    if request.method == 'POST':

        # Get the username and password from the POST data
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Create a user object by authenticating the username and password
        user = authenticate(request, username=username, password=password)

        # Check if user exists
        if user:

            # Check if user accout is active and not flagged as disabled which is what djanog recomeds rather than deleting user. Same approach to teahcer.
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect(reverse('home'))
            else:
                # Return HTTP Response
                return HttpResponse("Your account has been disabled")
        else:
            # Return HTTP Response
            return HttpResponse("Invalid login details supplied. Try again")

    # The request is not a POST, so hand back an empty login form
    else:
        return render(request, 'arete/login.html', {})


@login_required(login_url='login')
def user_logout(request):
    """
    Logout view for handling user logout.
    - Logs out the user and redirects to the index page.
    - @login_required: Requires the user to be logged in to access this view.
    """
    logout(request)
    return HttpResponseRedirect(reverse('index'))

