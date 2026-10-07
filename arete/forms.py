from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import User
from django.db.models import Q #search offerings for blog

from .models import *


class UserForm(forms.ModelForm):
    """
    Base django user profile
    - password *required
    - first_name *required
    - last_name *required
    - email *required
    """
    password = forms.CharField(widget=forms.PasswordInput())
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'placeholder@example.com'}),
        error_messages={'invalid': 'That does not look like an email address.',
                        'required': 'An email address is needed.'})
    

    class Meta:
        model = User
        fields = ('username', 
                  'first_name', 
                  'last_name', 
                  'email', 
                  'password')

class UserProfileForm(forms.ModelForm):
    """
    Create a user with attributes not in django
    - Groups: 
        - Student
        - Teacher
    - Atach a media path store to `/media`
    """

    # Users can choose between two groups: being a student or teacher
    GROUP_CHOICES = [("Students", "Student"), 
                     ("Teachers", "Teacher")]
    
    group = forms.ChoiceField(choices=GROUP_CHOICES, label="I am a")

    class Meta:
        model = AppUser
        fields = ('photo',)


class CourseForm(ModelForm):
    """
    Create a new course
    - Course code only allows numbers and letters
    """
    def clean(self):
        # Start with an empty form
        cleaned_data = super(CourseForm, self).clean()
        # Sanitize user input
        code = cleaned_data.get("code")
        # Check input is only numbers and letters
        if code and not code.isalnum():
            raise forms.ValidationError("Course code must be letters and digits only, e.g. CM3035")
        return cleaned_data

    class Meta:
        model = Course
        fields = ['code', 'title', 'description']


class OfferingForm(ModelForm):
    """
    Create a new offering
    - When a teacher creates an offering, they are tagged as the teacher
    - Issue This dosen't allow a administration personel (not in app) to assign a teacher
    """

    class Meta:
        model = Offering
        fields = ['course', 'season', 'year']


class MaterialForm(ModelForm):
    """
    Material file paths for Offerings
    - Uploaded only by a Teacher
    """

    class Meta:
        model = Material
        fields = ['title', 'file']

class FeedbackForm(ModelForm):
    """
    Students rating of an Offering
    """

    class Meta:
        model = Feedback
        fields = ['rating', 'comment']

class StatusUpdateForm(ModelForm):
    """
    Create a new post for the blog
    - A post dosn't need an Offering to be attached to.
    - A student must be enrolled and active status of Offering
    - Teacher must be the teacher for the Offering
    """

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['offering'].queryset = Offering.objects.filter(
            Q(teacher=user) | Q(enrolment__student=user, enrolment__status="ACTIVE")).distinct()

    class Meta:
        model = StatusUpdate
        fields = ['body', 'offering']