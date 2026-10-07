from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator

# Do not delete a user unless created by mistake.
# To retire a user, set User.is_active to False.
# design.md 3.2.1 and 4.9
class AppUser(models.Model):
    # Base django user model
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # profile photo
    photo = models.ImageField(null=True, blank=True)

    def __str__(self):
        return self.user.username


# Catalogue entry: The base course as seen in the course catalogue
# Example: Every year, Math 101 is offered
class Course(models.Model):

    # the course code, e.g., "MATH101"
    code = models.CharField(max_length=16, unique=True, null=False, blank=False)

    # the course title, e.g., "Descrete Mathematics"
    title = models.CharField(max_length=256, null=False, blank=False)

    # the course description, A longer text field, optional. 
    description = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return self.code


# The instance of a course. 
# Example: Math 101 is taught in 2024 during winter by Mr. Smith.
class Offering(models.Model):
    class Season(models.TextChoices):
        WINTER = "WINTER", "Winter"
        SPRING = "SPRING", "Spring"
        SUMMER = "SUMMER", "Summer"

    # the term in which the course is offered, e.g. "Winter 2024"
    season = models.CharField(max_length=16, choices=Season.choices,
                                null=False, blank=False)
    year = models.IntegerField(null=False, blank=False)

    # course --has many--> offerings. 
    course = models.ForeignKey(Course, on_delete=models.CASCADE,
                               related_name='offerings')

    
    # teacher --has many--> offerings
    teacher = models.ForeignKey(User, on_delete=models.CASCADE,
                                related_name='offerings_taught')
    
    # Link table: students enrolled in this offering. Many-to-many, through Enrolment
    students = models.ManyToManyField(User, through='Enrolment',
                                      related_name='offerings_taken')

    # Sorting and uniqueness constraints. 
    # The natural key is (course, season, year)
    class Meta:
        ordering = ['-year', 'season']
        constraints = [
            # as this is an elearing platform, a course can be offered only once per term
            models.UniqueConstraint(fields=['course', 'season', 'year'],
                                    name='unique_offering_per_term'),
        ]

    # Term is the concatenation of the season and year, e.g., "Spring 2026"
    # it derived not stored. So it used as a the display string and not for filtering or ordering. 
    # Filter on season and year instead.
    @property
    def term(self):
        return self.get_season_display()+" "+str(self.year)

    # Display string is the course code and term, e.g., "MATH101 Spring 2026"
    def __str__(self):
        return self.course.code+" "+self.term


# Many-to-many through table: a student is enrolled in an offering.
class Enrolment(models.Model):

    # Status choices: active, removed, blocked. 
    # Allows the teacher to remove a student from the course, or block them from enrolling again.
    # When a student enrolls, they default to ACTIVE.
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        REMOVED = "REMOVED", "Removed"
        BLOCKED = "BLOCKED", "Blocked"
    status = models.CharField(max_length=16, choices=Status.choices,
                                  null=False, blank=False,
                                  default=Status.ACTIVE)

    # Student --has many--> Enrolments
    # Offering --has many--> Enrolments
    # A student will be linked to all their classes through this table. 
    # - Enrolemnt 1: Student A -> Offering (MATH101 Spring 2026)
    # - Enrolment 2: Student A -> Offering (MATH101 Spring 2027)
    # - Enrolment 3: Student A -> Offering (MATH220 Spring 2028)
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    offering = models.ForeignKey(Offering, on_delete=models.CASCADE)

    # The date and time when the student enrolled in the offering. Auto-set on creation.
    enrolled_at = models.DateTimeField(auto_now_add=True)
    
    # Sort students by the date they enrolled, most recent first.
    # Enforce uniqueness: a student can only be enrolled in an offering once. (Cannot have two enrolments for the same offering.)
    class Meta:
        ordering = ['-enrolled_at']
        constraints = [
            models.UniqueConstraint(fields=['student', 'offering'],
                                    name='unique_student_per_offering'),
        ]

    # Display string is the student username and the offering, e.g., "Student A on MATH101 Spring 2026"
    def __str__(self):
        return self.student.username+" on "+str(self.offering)


# teaching material: images, pdfs, anything.
class Material(models.Model):

    # Offering --has many--> Materials
    # - A course can have many materials, but each material belongs to one offering.
    # - If the offering is deleted, the material is deleted too.
    offering = models.ForeignKey(Offering, on_delete=models.CASCADE)

    # User --has many--> Materials
    # - Track the user who uploaded the material. 
    # - If the user is deleted, the material is deleted too.
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)

    # The title of the material, e.g., "Lecture 1 Slides"
    title = models.CharField(max_length=256, null=False, blank=False)

    # The file itself. Stored in the media folder, storage path.
    file = models.FileField(blank=False)

    # The date and time when the material was uploaded. Auto-set on creation.
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # Sort materials by the date they were uploaded, most recent first.
    class Meta:
        ordering = ['-uploaded_at']

    # Display string is the title of the material. e.g., "Lecture 1 Slides"
    def __str__(self):
        return self.title


# The blog-like status updates for R1i. A student or teacher can post a status update about a course.
class StatusUpdate(models.Model):

    # User --has many--> StatusUpdates
    # - Can be a student or a teacher.
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    # A status update --can have a--> Offering
    # - *optional*: a status update can be about a specific course offering. If not, it is a general post. "I had a great weekend!"
    # - Every offering a student is enrolled in will have a blog option for the student to post a status update.
    # - Every offering a teacher is teaching will have a blog option for the teacher to post a status update.
    offering = models.ForeignKey(Offering, on_delete=models.CASCADE,
                                 null=True, blank=True)

    # The body of the status update. Cannot be null or blank.
    body = models.TextField(null=False, blank=False)

    # The date and time when the status update was posted. Auto-set on creation.
    posted_at = models.DateTimeField(auto_now_add=True)

    # Sort status updates by the date they were posted, most recent first.
    class Meta:
        ordering = ['-posted_at']

    # Display string is the author username and the first 50 characters of the body. e.g., "Student A: I had a great weekend!"
    def __str__(self):
        return self.author.username+": "+self.body[:50]


# Link table for student's feedback on a course (R1f)
# - A student can give feedback on a course they are enrolled in.
# - A student can only give feedback once per offering.
# - Each offering can have many feedbacks from different students.
class Feedback(models.Model):

    # Offering --has many--> Feedbacks
    # Student --has many--> Feedbacks
    # A student can only give feedback once per offering. Enforced by a unique constraint on (offering, student).
    # - Feedback 1: Student A -> Offering (MATH101 Spring 2026)
    # - Feedback 2: Student B -> Offering (MATH101 Spring 2026)
    # - Feedback 3: Student A -> Offering (CS210 Spring 2026)
    offering = models.ForeignKey(Offering, on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.CASCADE)

    # The rating given by the student. Optional, can be null or blank. Integer between 1 and 5.
    rating = models.IntegerField(validators=[MaxValueValidator(5), MinValueValidator(1)], null=True, blank=True)

    # The comment given by the student. Cannot be null or blank.
    comment = models.TextField(null=False, blank=False)

    # The date and time when the feedback was created. Auto-set on creation.
    created_at = models.DateTimeField(auto_now_add=True)

    # Sort and enforce uniqueness:
    class Meta:
        # Sort feedbacks by the date they were created, most recent first.
        ordering = ['-created_at']
        # Enforce uniqueness: a student can only give feedback once per offering.
        constraints = [
            models.UniqueConstraint(fields=['offering', 'student'],
                                    name='unique_feedback_per_student'),
        ]

    # Display string is the offering and the student username. 
    # - e.g., "MATH101 Spring 2026 feedback by Student A"
    def __str__(self):
        return str(self.offering)+" feedback by "+self.student.username


# stored notifications for:
# - R1k: Notify teachers when a student enrolls in their offering.
# - R1l: Notify students when a new material is uploaded to an offering they are enrolled in.

class Notification(models.Model):

    # User --has many--> Notifications
    # - When an action occurs, a notification is created for the user (the target recipient of the notification).
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)

    # The course offering that the notification is connected to.
    # - *optional*: a notification can be about a specific course offering. If not, it is a general post. "Students enrolled in your courses!""
    offering = models.ForeignKey(Offering, on_delete=models.SET_NULL,
                                 null=True, blank=True)

    # The message of the notification. Cannot be null or blank. Max length 256 characters.
    message = models.CharField(max_length=256, null=False, blank=False)

    # Link to the resource this holds a path like /offering/3/
    url = models.CharField(max_length=256, null=True, blank=True)

    # A flag for if the indivual user has read the notification. Default is False. When the user clicks on the notification, it is marked as read.
    is_read = models.BooleanField(default=False)

    # The date and time when the notification was created. Auto-set on creation.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return "to "+self.recipient.username+": "+self.message[:50]


# Created by teacher for a course offering. Allows students to see the upcoming deadlines for their assignments. 
# - Offers no support for submission or grading. 
# - This is a simple assignment tracker for students to see their upcoming deadlines.
# - Allows for student to see upcoming deadlines on their home page.
class Assignment(models.Model):
    offering = models.ForeignKey(Offering, on_delete=models.CASCADE)
    title = models.CharField(max_length=256, null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    due_date = models.DateTimeField(null=False, blank=False)

    class Meta:
        ordering = ['due_date']

    def __str__(self):
        return self.title
