from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile, Campaign, House, ApartmentVisit


# Инлайн для телефона
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'телефон'
    fields = ['phone']


# Расширенная админка пользователя
class UserAdmin(BaseUserAdmin):
    inlines = [ProfileInline]


admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# -------- Новые регистрации для управления кампаниями --------
@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'created_at')
    search_fields = ('name', 'owner__username')

@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'city', 'street', 'house_number')
    search_fields = ('city', 'street')

@admin.register(ApartmentVisit)
class ApartmentVisitAdmin(admin.ModelAdmin):
    list_display = ('house', 'apartment_number', 'opened_door', 'visited_at')
    list_filter = ('opened_door', 'visited_at')

