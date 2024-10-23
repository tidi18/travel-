import schedule
import time
from django.utils import timezone
from datetime import datetime
from .models import AutoPostLift, PostLiftLog


def is_today_in_selected_days(selected_days):
    today = str(datetime.now().weekday())
    return today in selected_days


def get_posts_data():
    today = datetime.now().date()

    lifts = AutoPostLift.objects.filter(
        start_date__lte=today,
        end_date__gte=today
    )

    for lift in lifts:
        if lift.end_date == today:
            post = lift.post
            post.last_lifted_at = post.create_date
            post.save()
            PostLiftLog.objects.create(
                post=post,
                message=f'Пост "{post.subject}" поднят автоматически, last_lifted_at установлен на create_date.'
            )
            print(f'Подняли пост: {post.subject}, last_lifted_at установлен на {post.create_date}')

        if lift.days_of_week and is_today_in_selected_days(lift.days_of_week):
            lift_post(lift)
        elif not lift.days_of_week:
            lift_post(lift)

    AutoPostLift.objects.filter(end_date__lt=today).delete()


def lift_post(lift):
    post = lift.post

    post.last_lifted_at = timezone.now()
    post.save()

    PostLiftLog.objects.create(
        post=post,
        message=f'Пост "{post.subject}" поднят автоматически'
    )
    print(f'Подняли пост: {post.subject}')


def start_scheduler():
    print("Планировщик задач запущен")
    schedule.every().day.at("23:55").do(get_posts_data)

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Остановка планировщика...")


start_scheduler()
