from django.db import models
from django.contrib.auth.models import (BaseUserManager,
                                        AbstractBaseUser,
                                        PermissionsMixin)
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from project import settings

class UserManager(BaseUserManager):
    def _create_user(self, username, email, password, **extra_fields):
        email = self.normalize_email(email)
        user = self.model(username=username, email=email,**extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_user(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(
            username=username,
            email=email,
            password=password,
            **extra_fields,
        )

    def create_superuser(self, username, email, password, **extra_fields):
        extra_fields['is_active'] = True
        extra_fields['is_staff'] = True
        extra_fields['is_superuser'] = True
        return self._create_user(
            username=username,
            email=email,
            password=password,
            **extra_fields,
        )

class User(AbstractBaseUser, PermissionsMixin):

    username = models.CharField(
        verbose_name=_("ユーザー名"),
        unique=True,
        max_length=10
    )
    email = models.EmailField(
        verbose_name=_("E-Mail"),
        unique=True
    )
    last_name = models.CharField(
        verbose_name=_("氏"),
        max_length=30,
        null=True,
        blank=False
    )
    first_name = models.CharField(
        verbose_name=_("名"),
        max_length=30,
        null=True,
        blank=False
    )
    is_superuser = models.BooleanField(
        verbose_name=_("is_superuser"),
        default=False
    )
    is_staff = models.BooleanField(
        verbose_name=_('staff status'),
        default=False,
    )
    is_active = models.BooleanField(
        verbose_name=_('active'),
        default=True,
    )
    created_at = models.DateTimeField(
        verbose_name=_("created_at"),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        verbose_name=_("updated_at"),
        auto_now=True
    )

    objects = UserManager()

    USERNAME_FIELD = 'username' # ログイン時、ユーザー名を使用
    REQUIRED_FIELDS = ['email']  # スーパーユーザー作成時にemailも設定する
    
    def __str__(self):
        return self.username

"""ユーザー別にトークンを作成"""
class UserToken(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"{self.user.username} - {self.token}"
