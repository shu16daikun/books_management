from django import forms
from django.db import IntegrityError
from uuid import uuid4
from .models import Books, Storage, Lending, Review

class StorageForm(forms.ModelForm):
    class Meta:
        model = Storage
        fields = ['floor', 'area']

    def save(self, commit=True):
        try:
            return super().save(commit=commit)
        except IntegrityError:
            raise forms.ValidationError("この階数とエリアの組み合わせは既に存在します。")

class BookForm(forms.ModelForm):
    class Meta:
        model = Books
        fields =  '__all__'

    def clean_isbn(self):
        isbn = self.cleaned_data.get('isbn')
        return isbn

class BookReservationForm(forms.ModelForm):
    class Meta:
        model = Lending
        fields = ['reservation_checkout_date', 'reservation_scheduled_return_date']

class BookRentForm(forms.ModelForm):
    class Meta:
        model = Lending
        fields = ['checkout_date', 'scheduled_return_date','reservation_checkout_date', 'reservation_scheduled_return_date']
        widgets = {
            'reservation_checkout_date': forms.HiddenInput(),
            'reservation_scheduled_return_date': forms.HiddenInput(),
        }
    
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['comment']