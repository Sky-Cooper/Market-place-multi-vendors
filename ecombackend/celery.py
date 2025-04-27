import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecombackend.settings")

app = Celery("ecombackend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'check-expired-claimed-orders-every-5-minutes': {
        'task': 'ecomapp.tasks.check_and_fail_expired_claimed_orders',
        'schedule': crontab(minute='*/5'),
    },
}
