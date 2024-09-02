from django.contrib.auth.forms import UserCreationForm, AuthenticationForm # 追加
from django import forms
from django.utils import timezone
from .models import User

class DateInput(forms.DateInput):
    input_type = 'date'

class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "last_name",
            "first_name",
        )
        

# ログインフォーム
class LoginFrom(AuthenticationForm):
    class Meta:
        model = User

#アカウント情報修正フォーム
class AccountsUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            'username', 
            'email',
            'last_name', 
            'first_name',
        )
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'