from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse
from django.utils.timezone import now
# <HINT> Import any new Models here
from .models import Course, Enrollment, Question, Choice, Submission, ExamSession, Learner, Instructor, Progress, Certificate
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
import logging
from django.db.models import Avg
from datetime import datetime
# Get an instance of a logger
logger = logging.getLogger(__name__)
# Create your views here.


def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            # Create a learner profile for the user
            learner = Learner.objects.create(user=user, occupation='student')
            login(request, user)
            return redirect("onlinecourse:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'onlinecourse/user_registration_bootstrap.html', context)


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'onlinecourse/user_login_bootstrap.html', context)
    else:
        return render(request, 'onlinecourse/user_login_bootstrap.html', context)


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


def check_if_enrolled(user, course):
    is_enrolled = False
    if user.id is not None:
        # Check if user enrolled
        num_results = Enrollment.objects.filter(user=user, course=course).count()
        if num_results > 0:
            is_enrolled = True
    return is_enrolled


# CourseListView
class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.filter(is_active=True).order_by('-pub_date')
        for course in courses:
            if user.is_authenticated:
                course.is_enrolled = check_if_enrolled(user, course)
        return courses


class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_detail_bootstrap.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.get_object()

        # Check if the user is enrolled in the course
        if self.request.user.is_authenticated:
            is_enrolled = check_if_enrolled(self.request.user, course)
            course.is_enrolled = is_enrolled
        else:
            course.is_enrolled = False

        # Add additional context
        context['course'] = course
        context['lessons'] = course.lesson_set.order_by('order')
        context['questions_count'] = course.question_set.filter(is_active=True).count()
        context['enrollment_count'] = course.get_enrollment_count()
        
        # Calculate progress if enrolled
        if self.request.user.is_authenticated and course.is_enrolled:
            try:
                enrollment = Enrollment.objects.get(user=self.request.user, course=course)
                context['progress'] = enrollment.progress
            except Enrollment.DoesNotExist:
                context['progress'] = 0
                
        return context


def start_exam_session(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    # Check if user is enrolled
    if not check_if_enrolled(user, course):
        return redirect('onlinecourse:course_details', pk=course_id)

    # Check if there's an existing active exam session
    existing_session = ExamSession.objects.filter(user=user, course=course, is_active=True).first()
    if existing_session:
        # If there's an active session, redirect to continue it
        return redirect('onlinecourse:course_details', pk=course_id)

    # Create a new exam session for the user
    exam_session = ExamSession.objects.create(
        user=user,
        course=course,
        total_time_allowed=3600  # 1 hour default
    )

    return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))


def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_enrolled = check_if_enrolled(user, course)
    if not is_enrolled and user.is_authenticated:
        # Create an enrollment
        enrollment = Enrollment.objects.create(user=user, course=course, mode='honor')
        course.total_enrollment += 1
        course.save()
        
        # Create progress tracking
        Progress.objects.get_or_create(user=user, course=course)

    return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))


def update_progress(request, course_id, lesson_id):
    """Update progress when user completes a lesson"""
    if request.method == 'POST' and request.user.is_authenticated:
        course = get_object_or_404(Course, pk=course_id)
        lesson = get_object_or_404(course.lesson_set.all(), pk=lesson_id)
        
        if check_if_enrolled(request.user, course):
            progress, created = Progress.objects.get_or_create(
                user=request.user,
                course=course
            )
            progress.lesson_completed.add(lesson)
            
            # Calculate progress percentage
            total_lessons = course.get_lessons_count()
            completed_lessons = progress.lesson_completed.count()
            progress.progress_percentage = (completed_lessons / total_lessons) * 100 if total_lessons > 0 else 0
            
            # Update enrollment progress as well
            enrollment = Enrollment.objects.get(user=request.user, course=course)
            enrollment.progress = progress.progress_percentage
            enrollment.save()
            progress.save()
            
            return JsonResponse({'status': 'success', 'progress': progress.progress_percentage})
    
    return JsonResponse({'status': 'error'})


def submit(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user
    
    if not user.is_authenticated:
        return redirect('onlinecourse:login')
    
    if not check_if_enrolled(user, course):
        return redirect('onlinecourse:course_details', pk=course_id)

    enrollment = Enrollment.objects.get(user=user, course=course)
    submission = Submission.objects.create(enrollment=enrollment)
    choices = extract_answers(request)
    submission.choices.set(choices)
    
    # Calculate score
    total_score = 0
    max_score = 0
    questions = course.question_set.filter(is_active=True)
    
    for question in questions:
        max_score += question.grade
        # Get selected choices for this question from the submission
        question_choices = [choice for choice in choices if choice.question_id == question.id]
        selected_choice_ids = [choice.id for choice in question_choices]
        
        if question.is_get_score(selected_choice_ids):
            total_score += question.grade

    # Calculate percentage grade if max_score > 0
    if max_score > 0:
        grade = round((total_score / max_score) * 100)
    else:
        grade = 0
    
    # Update submission with score and grade
    submission.score = total_score
    submission.grade = grade
    submission.save()
    
    # Update exam session as completed
    exam_session = ExamSession.objects.filter(user=user, course=course, is_active=True).first()
    if exam_session:
        exam_session.is_active = False
        exam_session.completed = True
        exam_session.save()
    
    # Update enrollment if passed
    if grade >= 80:  # Passing grade
        enrollment.completed = True
        enrollment.completion_date = datetime.now().date()
        enrollment.save()
        
        # Update learner stats
        learner = Learner.objects.filter(user=user).first()
        if learner:
            learner.total_courses_completed += 1
            learner.completion_rate = (learner.total_courses_completed / Enrollment.objects.filter(user=user).count()) * 100
            learner.save()
        
        # Update course rating
        course.total_ratings += 1
        all_ratings = Enrollment.objects.filter(course=course, completed=True).aggregate(Avg('rating'))
        if all_ratings['rating__avg']:
            course.rating = all_ratings['rating__avg']
        course.save()

    submission_id = submission.id
    return HttpResponseRedirect(reverse(viewname='onlinecourse:exam_result', args=(course_id, submission_id,)))


# An example method to collect the selected choices from the exam form from the request object
def extract_answers(request):
    submitted_choices = []
    for key in request.POST:
        if key.startswith('choice_'):
            value = request.POST[key]
            try:
                choice_id = int(value)
                choice = Choice.objects.get(id=choice_id)
                submitted_choices.append(choice)
            except (ValueError, Choice.DoesNotExist):
                pass  # Skip invalid choice IDs
    return submitted_choices


def show_exam_result(request, course_id, submission_id):
    context = {}
    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(Submission, id=submission_id)
    choices = submission.choices.all()
    
    # Calculate score and grade
    total_score = 0
    max_score = 0
    questions = course.question_set.filter(is_active=True)
    
    for question in questions:
        max_score += question.grade
        question_choices = [choice for choice in choices if choice.question_id == question.id]
        selected_choice_ids = [choice.id for choice in question_choices]
        
        if question.is_get_score(selected_choice_ids):
            total_score += question.grade

    # Calculate percentage grade if max_score > 0
    if max_score > 0:
        grade = round((total_score / max_score) * 100)
    else:
        grade = 0

    context['course'] = course
    context['grade'] = grade
    context['choices'] = choices
    context['submission'] = submission
    context['questions'] = questions
    
    # Add feedback for each question
    question_feedback = {}
    for question in questions:
        question_choices = [choice for choice in choices if choice.question_id == question.id]
        selected_choice_ids = [choice.id for choice in question_choices]
        is_correct = question.is_get_score(selected_choice_ids)
        question_feedback[question.id] = {
            'is_correct': is_correct,
            'selected_choices': question_choices
        }
    context['question_feedback'] = question_feedback
    
    return render(request, 'onlinecourse/exam_result_bootstrap.html', context)


def my_courses(request):
    """View to show user's enrolled courses and progress"""
    if not request.user.is_authenticated:
        return redirect('onlinecourse:login')
        
    enrollments = Enrollment.objects.filter(user=request.user).select_related('course')
    
    context = {
        'enrollments': enrollments
    }
    
    return render(request, 'onlinecourse/my_courses.html', context)


def course_progress(request, course_id):
    """View to show detailed progress for a specific course"""
    if not request.user.is_authenticated:
        return redirect('onlinecourse:login')
        
    course = get_object_or_404(Course, pk=course_id)
    
    if not check_if_enrolled(request.user, course):
        return redirect('onlinecourse:course_details', pk=course_id)
    
    progress, created = Progress.objects.get_or_create(
        user=request.user,
        course=course
    )
    
    context = {
        'course': course,
        'progress': progress,
        'lessons': course.lesson_set.order_by('order'),
    }
    
    return render(request, 'onlinecourse/course_progress.html', context)


def search_courses(request):
    """View to search for courses"""
    query = request.GET.get('q', '')
    courses = []
    
    if query:
        courses = Course.objects.filter(
            name__icontains=query,
            is_active=True
        ).order_by('-pub_date')
    
    context = {
        'course_list': courses,
        'query': query
    }
    
    return render(request, 'onlinecourse/search_results.html', context)