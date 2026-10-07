from rest_framework import serializers
from django.contrib.auth.models import User

from .models import *
from .permissions import is_teacher, is_student

class AppUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppUser
        fields = ['photo']

class UserSerializer(serializers.ModelSerializer):
    """
    The data belonging to each user
    - Password not listed in REST
    """
    profile = AppUserSerializer(source='appuser', read_only=True)
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'profile', 'role']
        read_only_fields = ['id', 'username']

    def get_role(self, user):
        if is_teacher(user):
            return "teacher"
        if is_student(user):
            return "student"
        return None
    
class StatusUpdateSerializer(serializers.ModelSerializer):
    """
    A status update, with its author and offering shown by name
    """
    author = serializers.StringRelatedField()
    offering = serializers.StringRelatedField()

    class Meta:
        model = StatusUpdate
        fields = ['id', 'author', 'body', 'offering', 'posted_at']

class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'code', 'title']

class OfferingSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    teacher = serializers.StringRelatedField()

    class Meta:
        model = Offering
        fields = ['id', 'course', 'season', 'year', 'term', 'teacher']