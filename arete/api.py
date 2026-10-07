from django.contrib.auth.models import User

from rest_framework import generics
from rest_framework import mixins
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import *
from .serializers import *
from .permissions import IsSelf

class UserList(generics.ListAPIView):
    """
    All users
    """
    queryset = User.objects.filter(is_active=True).order_by('username')
    serializer_class = UserListSerializer
    permission_classes = [IsAuthenticated]

class UserDetail(mixins.RetrieveModelMixin,
                 mixins.UpdateModelMixin,
                 generics.GenericAPIView):
    """
    A users data
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsSelf]

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

class CourseList(generics.ListAPIView):
    """
    All Courses
    """
    queryset = Course.objects.filter()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

class OfferingList(generics.ListAPIView):
    """
    All Offerings
    """
    queryset = Offering.objects.filter()
    serializer_class = OfferingSerializer
    permission_classes = [IsAuthenticated]

class UserStatusUpdates(generics.ListAPIView):
    """
    A user's status updates, newest first
    """
    serializer_class = StatusUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = get_object_or_404(User, pk=self.kwargs['pk'])
        return StatusUpdate.objects.filter(author=user)