from rest_framework import permissions

# user groups
STUDENTS = "Students"
TEACHERS = "Teachers"

# The groups wont helpus determin with home to render. 
# So we need to check that here and pass the group as a flag to the view

"""
Check if the user is a member of group: teacher
"""
def is_teacher(user):
    return user.groups.filter(name=TEACHERS).exists()

"""
Check if the user is a member of group: student
"""
def is_student(user):
    return user.groups.filter(name=STUDENTS).exists()

"""
REST permission: the object is the logged-in user themselves.
Used by the user detail endpoint, so users reach their own data only
"""
class IsSelf(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj == request.user