from django.contrib.auth import login, authenticate
from django.views.generic import TemplateView, CreateView, DetailView, UpdateView, DeleteView
from django.shortcuts import redirect, resolve_url
from django.contrib.auth.views import LoginView as BaseLoginView,  LogoutView as BaseLogoutView, PasswordChangeView, PasswordChangeDoneView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from datetime import datetime
from .forms import SignUpForm, LoginFrom, AccountsUpdateForm
from .models import User
from book.models import Lending
from django.contrib.auth import get_user_model

class IndexView(TemplateView):
    """ ホームビュー """
    template_name = "index.html"
    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        if user.is_authenticated:
            user = self.request.user
            today = datetime.today().date()
            # 「返却期限が過ぎている物」
            overdue_lendings = Lending.objects.filter(
                user=user,
                return_date__isnull=True,
                scheduled_return_date__lt=today
            )
            # 「予約中のもので返却がまだされていないもの」
            not_returned = Lending.objects.filter(
                user=user,
                reservation_checkout_date__lte=today,
                cancel_date__isnull=True,
            )
            context['overdue_lendings'] = overdue_lendings
            context['not_returned'] = not_returned
        return context


class SignupView(CreateView):
    """ ユーザー登録用ビュー """
    form_class = SignUpForm # 作成した登録用フォームを設定
    template_name = "accounts/signup.html" 
    success_url = reverse_lazy("accounts:index") # ユーザー作成後のリダイレクト先ページ

    def form_valid(self, form):
        # ユーザー作成後にそのままログイン状態にする設定
        response = super().form_valid(form)
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password1")
        user = authenticate(username=username, password=password)
        login(self.request, user)
        return response

# ログインビューを作成
class LoginView(BaseLoginView):
    form_class = LoginFrom
    template_name = "accounts/login.html"

class LogoutView(BaseLogoutView):
    success_url = reverse_lazy("accounts:index")

""" ユーザ限定クラス """
class UserOnlyMixin(UserPassesTestMixin):
    raise_exception = True
    def test_func(self):
        user = self.request.user
        return user.pk == self.kwargs['pk'] or user.is_superuser

""" ユーザ情報表示ページ """
class Profile(UserOnlyMixin, DetailView):
    model = User
    template_name = 'accounts/profile.html'

""" ユーザ情報更新ページ """
class ProfileUpdate(UserOnlyMixin, UpdateView):
    model = User
    form_class = AccountsUpdateForm
    template_name = 'accounts/profile_update.html'
    success_url = reverse_lazy('accounts:profile') 
    def get_success_url(self):
        return reverse_lazy('accounts:profile', kwargs={'pk': self.object.pk})
    
    def get_object(self, queryset=None):
        return self.request.user

""" パスワード変更ページ """
class PasswordChange(UserOnlyMixin, PasswordChangeView):
    model = User
    template_name = 'accounts/password_change.html'
    def get_success_url(self):
        return resolve_url('accounts:password_complete', pk=self.kwargs['pk'])


""" パスワード変更完了 """
class PasswordChangeComplete(UserOnlyMixin, PasswordChangeDoneView):
    template_name = 'accounts/password_change_complete.html'

"""退会処理"""
class UserDeleteView(UserOnlyMixin, DeleteView):
    template_name = "accounts/delete.html"
    success_url = reverse_lazy("book:index")
    model = User

    def get_object(self, queryset=None):
        # 現在のユーザーオブジェクトを返す
        return self.request.user