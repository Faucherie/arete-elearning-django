import os
import sys
import django
import csv
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elearning.settings')
django.setup()

from django.contrib.auth.models import User, Group
from django.utils import timezone

from arete.models import *

PASSWORD = 'password'
DATA_DIR = os.path.join(PROJECT_ROOT, 'scripts')


def rows(filename):
    with open(os.path.join(DATA_DIR, filename)) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        csv_reader.__next__()  # throw the header row away
        return list(csv_reader)

def make_user(username, first, last, group_name):
    user, created = User.objects.get_or_create(
        username=username,
        defaults={'first_name': first,
                  'last_name': last,
                  'email': username+'@example.ac.uk'})
    if created:
        user.set_password(PASSWORD)
        user.save()
    AppUser.objects.get_or_create(user=user)
    # outside the if: add() is idempotent, so re-running repairs a user
    # whose group was removed by hand rather than skipping them
    user.groups.add(Group.objects.get(name=group_name))
    return user


# Users
user_rows = {}
for row in rows('users.csv'):
    user_rows[row[0]] = make_user(row[0], row[1], row[2], row[3])

# Courses
course_rows = {}
for row in rows('courses.csv'):
    course_rows[row[0]], created = Course.objects.get_or_create(
        code=row[0], defaults={'title': row[1], 'description': row[2]})

# Offerings
offering_rows = {}
for row in rows('offerings.csv'):
    offering_rows[row[0]], created = Offering.objects.get_or_create(
        course=course_rows[row[1]], season=row[2], year=int(row[3]),
        defaults={'teacher': user_rows[row[4]]})

# Enrolments
for row in rows('enrolments.csv'):
    Enrolment.objects.get_or_create(
        student=user_rows[row[1]], offering=offering_rows[row[0]],
        defaults={'status': row[2]})

# Assignments
for row in rows('assignments.csv'):
    Assignment.objects.get_or_create(
        offering=offering_rows[row[0]], title=row[1],
        defaults={'description': row[2],
                  'due_date': timezone.make_aware(
                      datetime.strptime(row[3], '%Y-%m-%d %H:%M'))})

# -- Feedback --
# ref, student_username, rating, comment
for row in rows('feedback.csv'):
    Feedback.objects.get_or_create(
        offering=offering_rows[row[0]], student=user_rows[row[1]],
        defaults={'rating': int(row[2]), 'comment': row[3]})

# -- Status updates --
# author_username, ref, body. An empty ref is a general post, which the
# model allows because StatusUpdate.offering is nullable
for row in rows('status_updates.csv'):
    StatusUpdate.objects.get_or_create(
        author=user_rows[row[0]], body=row[2],
        offering=offering_rows[row[1]] if row[1] else None)

print("Seeded. Password for every account: "+PASSWORD)
print("  teachers     %d" % Group.objects.get(name="Teachers").user_set.count())
print("  students     %d" % Group.objects.get(name="Students").user_set.count())
print("  courses      %d" % Course.objects.count())
print("  offerings    %d" % Offering.objects.count())
print("  enrolments   %d" % Enrolment.objects.count())
print("  assignments  %d" % Assignment.objects.count())
print("  feedback     %d" % Feedback.objects.count())
print("  updates      %d" % StatusUpdate.objects.count())
