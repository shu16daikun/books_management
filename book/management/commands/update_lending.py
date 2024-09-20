from django.core.management.base import BaseCommand
from datetime import date
from ...models import Lending, Books
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Update book lending status'

    def handle(self, *args, **kwargs):
        today = date.today()
        lendings = Lending.objects.filter(
            reservation_checkout_date__lte=str(today), 
            cancel_date__isnull=True,
            return_date__isnull=True,
            )
        
        for lending in lendings:
            book = lending.books
            if book.is_lend_out == False:
                lending.checkout_date = lending.reservation_checkout_date
                lending.scheduled_return_date = lending.reservation_scheduled_return_date
                lending.reservation_checkout_date = None
                lending.reservation_scheduled_return_date = None
                lending.save()
                book.is_lend_out = True
                book.save()
                print(f'Updated book {book.pk}.{book.title}')
            else:
                print(f'Skip id:{book.pk}.{book.title}')


