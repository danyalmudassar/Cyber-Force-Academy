from django.contrib import admin
from .models import Course, Lesson, Instructor, Learner, Question, Choice, Enrollment, Submission, ExamSession, Progress, Certificate


# Custom admin classes for enhanced management

class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'level', 'category', 'total_enrollment', 'rating', 'pub_date', 'is_active')
    list_filter = ('level', 'category', 'pub_date', 'is_active')
    search_fields = ('name', 'description')
    filter_horizontal = ('instructors',)
    readonly_fields = ('total_enrollment',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'image', 'pub_date', 'category')
        }),
        ('Details', {
            'fields': ('level', 'duration', 'instructors', 'prerequisites', 'learning_outcomes', 'is_active')
        }),
        ('Statistics', {
            'fields': ('total_enrollment', 'rating', 'total_ratings'),
            'classes': ('collapse',)
        }),
    )

class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'duration', 'is_preview')
    list_filter = ('course', 'is_preview')
    search_fields = ('title', 'content')
    ordering = ('course', 'order')

class InstructorAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_time', 'total_learners', 'expertise')
    list_filter = ('full_time',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'expertise')
    readonly_fields = ('total_learners',)

class LearnerAdmin(admin.ModelAdmin):
    list_display = ('user', 'occupation', 'date_joined', 'total_courses_completed', 'completion_rate')
    list_filter = ('occupation', 'date_joined')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('date_joined', 'completion_rate', 'total_courses_completed')

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('content', 'course', 'question_type', 'difficulty_level', 'grade', 'is_active')
    list_filter = ('course', 'question_type', 'difficulty_level', 'is_active')
    search_fields = ('content',)

class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('content', 'question', 'is_correct')
    list_filter = ('question', 'is_correct')
    search_fields = ('content', 'question__content')

class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'mode', 'progress', 'completed', 'date_enrolled')
    list_filter = ('mode', 'completed', 'date_enrolled', 'course')
    search_fields = ('user__username', 'course__name')
    readonly_fields = ('date_enrolled',)

class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'grade', 'timestamp')
    list_filter = ('timestamp', 'grade', 'enrollment__course')
    readonly_fields = ('timestamp',)

class ExamSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'start_time', 'is_active', 'completed')
    list_filter = ('start_time', 'is_active', 'completed', 'course')
    readonly_fields = ('start_time',)

class ProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'progress_percentage', 'current_lesson', 'last_accessed')
    list_filter = ('last_accessed', 'progress_percentage', 'course')
    filter_horizontal = ('lesson_completed',)

class CertificateAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'issue_date', 'is_valid')
    list_filter = ('issue_date', 'is_valid', 'course')
    search_fields = ('user__username', 'course__name', 'certificate_id')


# Register the models with their custom admin configurations
admin.site.register(Course, CourseAdmin)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(Instructor, InstructorAdmin)
admin.site.register(Learner, LearnerAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice, ChoiceAdmin)
admin.site.register(Enrollment, EnrollmentAdmin)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(ExamSession, ExamSessionAdmin)
admin.site.register(Progress, ProgressAdmin)
admin.site.register(Certificate, CertificateAdmin)