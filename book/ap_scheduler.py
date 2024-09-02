from apscheduler.schedulers.background import BackgroundScheduler
from django.core.management import call_command

def update_books_is_lend_out():
    call_command('update_lending')

def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_books_is_lend_out, 'interval', minutes=1, max_instances=3)
    scheduler.start()