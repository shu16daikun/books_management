from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse
from django.views.generic import TemplateView, CreateView, DetailView, UpdateView, DeleteView
from django.shortcuts import redirect, resolve_url
from django.contrib.auth.views import LoginView as BaseLoginView,  LogoutView as BaseLogoutView, PasswordChangeView, PasswordChangeDoneView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from datetime import datetime
from .forms import SignUpForm, LoginFrom, AccountsUpdateForm
from .models import User, UserToken
from book.models import Lending
from django.contrib.auth import get_user_model
from django.views.decorators.cache import cache_control
from django.utils.decorators import method_decorator
from django.shortcuts import render
import secrets
from book.views import generate_user_token, get_user_token, search_user_token

def custom_permission_denied_view(request, exception=None):
    return render(request, '403.html', status=403)

class IndexView(TemplateView):
    """ ホームビュー """
    template_name = "index.html"

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            session_token = secrets.token_urlsafe()
            self.request.session['session_token'] = session_token  # トークンをセッションに保存
            print(self.request.session.get('session_token'))#デバック
            
            user_token = search_user_token(user)
            self.request.session['user_token'] = user_token
        return super().dispatch(request, *args, **kwargs)
    
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

    @method_decorator(cache_control(no_cache=True, must_revalidate=True, no_store=True))
    def dispatch(self, *args, **kwargs):
        # キャッシュ無効化のデコレーターを追加
        return super().dispatch(*args, **kwargs)
    
    def form_valid(self, form):
        # ユーザー作成後にそのままログイン状態にする設定
        response = super().form_valid(form)
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password1")
        user = authenticate(username=username, password=password)
        if user is not None:
            login(self.request, user)
        else:
            response = self.form_invalid(form)  # ユーザーが存在しない場合はエラー処理
        return response

# ログインビューを作成
class LoginView(BaseLoginView):
    form_class = LoginFrom
    template_name = "accounts/login.html"

    @method_decorator(cache_control(no_cache=True, must_revalidate=True, no_store=True))
    def dispatch(self, *args, **kwargs):
        # キャッシュ無効化のデコレーターを追加
        return super().dispatch(*args, **kwargs)
    
    def form_invalid(self, form):
        messages.error(self.request, 'メールアドレスかパスワードが間違っています。')
        return super().form_invalid(form)

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