# core/admin.py
from django.contrib import admin
from .models import Company, UserProfile, Review
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'perfil'
    fields = ('role', 'company',)

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role')

    def get_role(self, obj):
        return obj.profile.get_role_display() if hasattr(obj, 'profile') else 'N/A'
    get_role.short_description = 'Rol'

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'sector', 'is_active')
    search_fields = ('name', 'location', 'sector')
    list_filter = ('is_active', 'sector', 'location')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('company', 'job_title', 'modality', 'overall_rating', 'is_approved', 'submission_date')
    list_filter = ('is_approved', 'modality', 'company__name', 'submission_date')
    search_fields = ('company__name', 'job_title', 'pros', 'cons')
    actions = ['approve_reviews', 'disapprove_reviews']

    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
    approve_reviews.short_description = "Aprobar reseñas seleccionadas"

    def disapprove_reviews(self, request, queryset):
        queryset.update(is_approved=False)
    disapprove_reviews.short_description = "Desaprobar reseñas seleccionadas"