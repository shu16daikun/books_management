from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path('signup/', views.SignupView.as_view(), name="signup"),
    path('login/', views.LoginView.as_view(), name="login"),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/<int:pk>/', views.Profile.as_view(), name='profile'),
    path('profile/<int:pk>/update', views.ProfileUpdate.as_view(), name='profile_update'),
    path('profile/<int:pk>/password', views.PasswordChange.as_view(), name='password'),  # 追記
    path('profile/<int:pk>/password/complete', views.PasswordChangeComplete.as_view(), name='password_complete'), 
    path('profile/<int:pk>/delete/',views.UserDeleteView.as_view(), name='delete')
]