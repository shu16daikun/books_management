from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import *

admin.site.register(Storage)  
admin.site.register(Review) 
admin.site.register(Lending) 
admin.site.register(Books)