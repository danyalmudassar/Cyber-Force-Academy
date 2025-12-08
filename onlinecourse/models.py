import sys
from django.utils.timezone import now
try:
    from django.db import models
except Exception:
    print("There was an error loading django modules. Do you have django installed?")
    sys.exit()

from django.conf import settings
import uuid


# Instructor model
class Instructor(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    full_time = models.BooleanField(default=True)
    total_learners = models.IntegerField(default=0)
    bio = models.TextField(max_length=1000, blank=True)
    expertise = models.CharField(max_length=200, blank=True)
    profile_image = models.ImageField(upload_to='instructor_images/', blank=True)

    def __str__(self):
        return self.user.username


# Learner model
class Learner(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    STUDENT = 'student'
    DEVELOPER = 'developer'
    DATA_SCIENTIST = 'data_scientist'
    DATABASE_ADMIN = 'dba'
    CYBERSECURITY_ANALYST = 'cybersecurity_analyst'
    AI_ENGINEER = 'ai_engineer'
    PENETRATION_TESTER = 'penetration_tester'

    OCCUPATION_CHOICES = [
        (STUDENT, 'Student'),
        (DEVELOPER, 'Developer'),
        (DATA_SCIENTIST, 'Data Scientist'),
        (DATABASE_ADMIN, 'Database Admin'),
        (CYBERSECURITY_ANALYST, 'Cybersecurity Analyst'),
        (AI_ENGINEER, 'AI Engineer'),
        (PENETRATION_TESTER, 'Penetration Tester'),
    ]
    occupation = models.CharField(
        null=False,
        max_length=25,
        choices=OCCUPATION_CHOICES,
        default=STUDENT
    )
    social_link = models.URLField(max_length=200, blank=True)
    profile_image = models.ImageField(upload_to='learner_images/', blank=True)
    date_joined = models.DateField(null=True, blank=True)
    completion_rate = models.FloatField(default=0.0)
    total_courses_completed = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} ({self.occupation})"


# Course model
class Course(models.Model):
    name = models.CharField(null=False, max_length=100, default='Online Course')
    image = models.ImageField(upload_to='course_images/')
    description = models.TextField(max_length=2000)
    pub_date = models.DateField(null=True)
    instructors = models.ManyToManyField(Instructor)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, through='Enrollment')
    total_enrollment = models.IntegerField(default=0)
    is_enrolled = False
    level = models.CharField(max_length=20, choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ], default='beginner')
    duration = models.CharField(max_length=50, default='Self-paced')  # e.g., "6 weeks", "Self-paced"
    category = models.CharField(max_length=50, default='Technology')
    prerequisites = models.TextField(max_length=500, blank=True)
    learning_outcomes = models.TextField(max_length=1000, blank=True)
    is_active = models.BooleanField(default=True)
    rating = models.FloatField(default=0.0)  # Average rating
    total_ratings = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name} - {self.description[:50]}..."

    def get_lessons_count(self):
        return self.lesson_set.count()

    def get_questions_count(self):
        return self.question_set.count()

    def get_enrollment_count(self):
        return self.enrollment_set.count()

    def get_thumbnail_image_url(self):
        """Return the thumbnail version of the course image"""
        if self.image:
            # Replace the image path to point to a thumbnail version
            image_path = str(self.image)
            if 'course_images/' in image_path:
                thumbnail_path = image_path.replace('course_images/', 'course_thumbnails/')
                return f'/media/{thumbnail_path}'
        return f'/media/{self.image}' if self.image else None


# Lesson model
class Lesson(models.Model):
    title = models.CharField(max_length=200, default="Lesson Title")
    order = models.IntegerField(default=0)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    content = models.TextField()
    video_url = models.URLField(max_length=500, blank=True)  # For video lessons
    duration = models.IntegerField(default=0)  # Duration in minutes
    is_preview = models.BooleanField(default=False)  # Whether lesson is freely accessible
    created_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.course.name} - {self.title}"


# Enrollment model
# <HINT> Once a user enrolled a class, an enrollment entry should be created between the user and course
# And we could use the enrollment to track information such as exam submissions
class Enrollment(models.Model):
    AUDIT = 'audit'
    HONOR = 'honor'
    CERTIFICATE = 'certificate'
    VERIFIED = 'verified'

    COURSE_MODES = [
        (AUDIT, 'Audit'),
        (HONOR, 'Honor'),
        (CERTIFICATE, 'Certificate'),
        (VERIFIED, 'Verified'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date_enrolled = models.DateField(default=now)
    mode = models.CharField(max_length=15, choices=COURSE_MODES, default=AUDIT)
    rating = models.FloatField(default=0.0)
    progress = models.FloatField(default=0.0)  # Progress percentage
    completed = models.BooleanField(default=False)  # Whether course is completed
    completion_date = models.DateField(null=True, blank=True)  # When course was completed
    certificate_issued = models.BooleanField(default=False)  # Whether certificate was issued
    certificate_url = models.URLField(max_length=500, blank=True)  # Link to certificate

    def __str__(self):
        return f"{self.user.username} - {self.course.name}"


class Question(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    content = models.CharField(max_length=500)
    grade = models.IntegerField(default=10)
    question_type = models.CharField(max_length=20, choices=[
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
        ('multiple_select', 'Multiple Select'),
    ], default='multiple_choice')
    difficulty_level = models.CharField(max_length=20, choices=[
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
        ('expert', 'Expert'),
    ], default='medium')
    is_active = models.BooleanField(default=True)
    max_attempts = models.IntegerField(default=3)  # Number of attempts allowed
    feedback = models.TextField(blank=True)  # Feedback to show after answering

    def __str__(self):
        return f"Question: {self.content[:50]}..."

    # method to calculate if the learner gets the score of the question
    def is_get_score(self, selected_ids):
        all_correct_answers = self.choice_set.filter(is_correct=True).count()
        selected_correct = self.choice_set.filter(is_correct=True, id__in=selected_ids).count()

        if self.question_type == 'multiple_select':
            # For multiple select, all correct answers must be selected and no wrong ones
            selected_wrong = self.choice_set.filter(is_correct=False, id__in=selected_ids).count()
            if all_correct_answers == selected_correct and selected_wrong == 0:
                return True
            else:
                return False
        else:
            # For other types, just need to select all correct answers
            if all_correct_answers == selected_correct:
                return True
            else:
                return False


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    content = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    explanation = models.TextField(blank=True)  # Explanation for why this is correct/incorrect

    def __str__(self):
        return f"Choice: {self.content[:30]}..."


class Submission(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
    choices = models.ManyToManyField(Choice)
    timestamp = models.DateTimeField(null=True, blank=True)  # Will be set in the view
    exam_session_time = models.IntegerField(null=True, blank=True)  # Time taken in seconds
    score = models.FloatField(default=0.0)  # Score for this submission
    grade = models.FloatField(default=0.0)  # Grade percentage

    def __str__(self):
        return f"Submission by {self.enrollment.user.username} for {self.enrollment.course.name}"


class ExamSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    time_remaining = models.IntegerField(null=True, blank=True)  # For timed exams
    is_active = models.BooleanField(default=True)
    total_time_allowed = models.IntegerField(null=True, blank=True)  # Time allowed in seconds
    current_question_index = models.IntegerField(default=0)  # Track current question
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Exam Session: {self.user.username} - {self.course.name}"

# Progress tracking model
class Progress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    lesson_completed = models.ManyToManyField(Lesson, blank=True)
    current_lesson = models.IntegerField(default=0)  # Index of current lesson
    progress_percentage = models.FloatField(default=0.0)  # Course progress percentage
    last_accessed = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Progress: {self.user.username} - {self.course.name}"

# Certificate model
class Certificate(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
    issue_date = models.DateField(auto_now_add=True)
    certificate_id = models.CharField(max_length=100, unique=True)
    is_valid = models.BooleanField(default=True)
    file_path = models.CharField(max_length=500, blank=True)  # Path to certificate file

    def __str__(self):
        return f"Certificate: {self.user.username} - {self.course.name}"
