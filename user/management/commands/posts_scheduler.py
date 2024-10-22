from django.core.management.base import BaseCommand
from ...scheduler_posts import start_scheduler


class Command(BaseCommand):
    help = 'Starts the scheduler posts'

    def handle(self, *args, **options):
        start_scheduler()
        self.stdout.write(self.style.SUCCESS('Scheduler posts started successfully'))