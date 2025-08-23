from django.contrib import admin
from .models import User, Doctor
from hospitals.models import Hospital, Department, Service, DoctorDepartmentAssignment, DoctorService
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

class UserAdmin(BaseUserAdmin):
    model = User
    
    list_display = ("id","phone_number","first_name","last_name",
                    "role","is_active","is_staff","is_phone_verified",
                    "is_blacklisted",)
    list_filter = ("role","is_active","is_staff","is_blacklisted",)
    search_fields = ("phone_number","first_name","last_name",)
    ordering = ("id",)

    fieldsets = (
        (None, {"fields": ("phone_number","password"),}),
        ("Лични податоци",{"fields":("first_name","last_name","serial_number"),}),
        ("Улога",{"fields":("role",)}),
        ("Permissions", {"fields":("is_active","is_staff","is_phone_verified","is_superuser","groups","user_permissions"),}),
        ("Important dates",{"fields":("last_login","date_joined"),}),
        ("Blacklist", {"fields":("is_blacklisted",),}),
    )
    list_editable = ('is_blacklisted',)
    actions = ['blacklist_users','unblacklist_users']
    def blacklist_users(self, queryset):
        queryset.update(is_blacklisted=True)
    blacklist_users.short_description = "Blacklist selected users"

    def unblacklist_users(self, queryset):
        queryset.update(is_blacklisted=False)
    unblacklist_users.short_description = "Remove selected users from blacklist"
    add_fieldsets = (
        (None, {
            "classes": ("wide"),
            "fields":("phone_number","password1","password2","role","is_active","is_staff","is_blacklisted"),
        })
    )

@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "address","phone_number",)
    search_fields = ("name","address",)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("id","name","hospital","phone_number",)
    search_fields = ("name",)
    list_filter = ("hospital",)

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("id","name","department",)
    search_fields = ("name",)
    list_filter = ("department",)

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("id","user__first_name","user__last_name", "user", "specialization", "hospital", "approved","user__is_blacklisted",)
    search_fields = ("user__first_name", "user__last_name","specialization","hospital",)
    list_filter = ("hospital","approved",)

@admin.register(DoctorDepartmentAssignment)
class DoctorDepartmentAssignmentAdmin(admin.ModelAdmin):
    list_display = ("id","assignment_display","approved","requested_at","approved_at",)
    search_fields = ("doctor__user__first_name","doctor__user__last_name","department__name","department__hospital__name",)
    list_filter = ("department","department__hospital",)

    def assignment_display(self, obj):
        return str(obj)
    
    assignment_display.short_description = "Assignment"

@admin.register(DoctorService)
class DoctorServiceAdmin(admin.ModelAdmin):
    list_display = ("id", "doctor", "service",)
    search_fields = ("doctor__user__first_name","doctor__user__last_name","service__name","service__department__name","service__department__hospital__name",)
    list_filter = ("service",)

admin.site.register(User, UserAdmin)

# Register your models here.
