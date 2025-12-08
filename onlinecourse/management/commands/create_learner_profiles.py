from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from onlinecourse.models import Learner


class Command(BaseCommand):
    help = 'Creates Learner profiles for existing users without profiles'

    def handle(self, *args, **options):
        users_without_learner = User.objects.exclude(learner__isnull=False)
        
        created_count = 0
        for user in users_without_learner:
            Learner.objects.create(user=user, occupation='student')
            created_count += 1
            self.stdout.write(f'Created learner profile for user: {user.username}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} learner profiles'
            )
        )