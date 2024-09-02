from django.contrib import admin
from django.contrib.auth.admin import UserAdmin 
from django.contrib.auth.models import Group

from .models import User

class CustomUserAdmin(UserAdmin):
    model = User
    # fields、fieldsets、excludeにdate_joinedが指定されている場合、削除します
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser',
                                     'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),  # 'date_joined' を削除
    )

admin.site.register(User, CustomUserAdmin)  # Userモデルを登録
admin.site.unregister(Group)  # Groupモデルは不要のため非表示にします