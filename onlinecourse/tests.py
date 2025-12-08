from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from onlinecourse.models import Course, Lesson, Question, Choice, Instructor, Learner, Enrollment, Submission, ExamSession, Progress
from django.utils import timezone
from datetime import date


class CyberForceAcademyTestCase(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create instructor
        instructor_user = User.objects.create_user(
            username='instructor',
            password='instructorpass123'
        )
        self.instructor = Instructor.objects.create(
            user=instructor_user,
            total_learners=0
        )
        
        # Create a test course
        self.course = Course.objects.create(
            name='Test Course',
            description='This is a test course',
            pub_date=date.today(),
            level='beginner',
            category='Technology'
        )
        self.course.instructors.add(self.instructor)
        
        # Create a lesson
        self.lesson = Lesson.objects.create(
            course=self.course,
            title='Test Lesson',
            order=0,
            content='This is a test lesson content',
            duration=30
        )
        
        # Create a question
        self.question = Question.objects.create(
            course=self.course,
            content='What is AI?',
            grade=10,
            question_type='multiple_choice',
            difficulty_level='easy'
        )
        
        # Create choices for the question
        self.choice1 = Choice.objects.create(
            question=self.question,
            content='Artificial Intelligence',
            is_correct=True
        )
        self.choice2 = Choice.objects.create(
            question=self.question,
            content='Actual Implementation',
            is_correct=False
        )
        
        self.client = Client()

    def test_home_page_loads(self):
        """Test that the home page loads correctly"""
        response = self.client.get(reverse('onlinecourse:index'))
        self.assertEqual(response.status_code, 200)

    def test_registration_page_loads(self):
        """Test that the registration page loads correctly"""
        response = self.client.get(reverse('onlinecourse:registration'))
        self.assertEqual(response.status_code, 200)

    def test_login_page_loads(self):
        """Test that the login page loads correctly"""
        response = self.client.get(reverse('onlinecourse:login'))
        self.assertEqual(response.status_code, 200)

    def test_course_detail_page_loads(self):
        """Test that the course detail page loads correctly"""
        response = self.client.get(reverse('onlinecourse:course_details', args=[self.course.id]))
        self.assertEqual(response.status_code, 200)

    def test_user_registration(self):
        """Test user registration functionality"""
        response = self.client.post(reverse('onlinecourse:registration'), {
            'username': 'newuser',
            'firstname': 'New',
            'lastname': 'User',
            'psw': 'newpass123'
        })
        self.assertEqual(response.status_code, 302)  # Should redirect after successful registration

    def test_user_login_logout(self):
        """Test user login and logout functionality"""
        # Test login
        login_data = {'username': 'testuser', 'psw': 'testpass123'}
        response = self.client.post(reverse('onlinecourse:login'), login_data)
        self.assertEqual(response.status_code, 302)  # Should redirect after login
        
        # Test logout
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('onlinecourse:logout'))
        self.assertEqual(response.status_code, 302)  # Should redirect after logout

    def test_course_enrollment(self):
        """Test course enrollment functionality"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('onlinecourse:enroll', args=[self.course.id]))
        self.assertEqual(response.status_code, 302)  # Should redirect after enrollment
        
        # Verify enrollment was created
        enrollment = Enrollment.objects.filter(user=self.user, course=self.course)
        self.assertTrue(enrollment.exists())

    def test_lesson_completion_tracking(self):
        """Test lesson completion tracking functionality"""
        # Create enrollment first
        self.client.login(username='testuser', password='testpass123')
        self.client.post(reverse('onlinecourse:enroll', args=[self.course.id]))
        
        # Test lesson completion update
        response = self.client.post(reverse('onlinecourse:update_progress', args=[self.course.id, self.lesson.id]))
        self.assertEqual(response.status_code, 200)
        
        # Verify response is JSON with success status
        import json
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')

    def test_my_courses_page(self):
        """Test 'My Courses' page functionality"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create an enrollment first
        self.client.post(reverse('onlinecourse:enroll', args=[self.course.id]))
        
        response = self.client.get(reverse('onlinecourse:my_courses'))
        self.assertEqual(response.status_code, 200)

    def test_course_progress_page(self):
        """Test course progress page functionality"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create an enrollment first
        self.client.post(reverse('onlinecourse:enroll', args=[self.course.id]))
        
        response = self.client.get(reverse('onlinecourse:course_progress', args=[self.course.id]))
        self.assertEqual(response.status_code, 200)

    def test_search_functionality(self):
        """Test course search functionality"""
        response = self.client.get(reverse('onlinecourse:search'), {'q': 'Test'})
        self.assertEqual(response.status_code, 200)

    def test_admin_interface_accessible(self):
        """Test admin interface is accessible"""
        # Create admin user
        admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'adminpass')
        self.client.login(username='admin', password='adminpass')
        
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)

    def test_question_submission_and_grading(self):
        """Test question submission and grading functionality"""
        # Login and enroll first
        self.client.login(username='testuser', password='testpass123')
        self.client.post(reverse('onlinecourse:enroll', args=[self.course.id]))
        
        # Test submitting answers
        response = self.client.post(reverse('onlinecourse:submit', args=[self.course.id]), {
            f'choice_{self.choice1.id}': self.choice1.id
        })
        # This will redirect, so just check it doesn't crash
        self.assertIn(response.status_code, [302])  # Should redirect to results page

    def test_models_creation(self):
        """Test that all models can be created and saved properly"""
        # Test that our setup objects were created correctly
        self.assertEqual(Course.objects.count(), 1)
        self.assertEqual(Lesson.objects.count(), 1)
        self.assertEqual(Question.objects.count(), 1)
        self.assertEqual(Choice.objects.count(), 2)
        self.assertEqual(Instructor.objects.count(), 1)
        self.assertGreaterEqual(User.objects.count(), 2)  # At least testuser and instructor

    def test_progress_model_functionality(self):
        """Test progress tracking model functionality"""
        # Create enrollment
        enrollment = Enrollment.objects.create(user=self.user, course=self.course)
        
        # Create progress
        progress = Progress.objects.create(user=self.user, course=self.course)
        progress.lesson_completed.add(self.lesson)
        
        # Verify progress tracking
        self.assertIn(self.lesson, progress.lesson_completed.all())
        self.assertEqual(progress.lesson_completed.count(), 1)