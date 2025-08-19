from django.contrib import admin
from .models import User, Doctor
from hospitals.models import Hospital, Department, Service, DoctorDepartmentAssignment, DoctorService

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ("id","phone_number","first_name","last_name","role","is_active","is_staff","is_phone_verified",)
    list_filter = ("role","is_active","is_staff",)
    search_fields = ("phone_number","first_name","last_name",)
    ordering = ("id",)

    fieldsets = (
        (None, {"fields": ("phone_number","password"),}),
        ("Лични податоци",{"fields":("first_name","last_name","serial_number"),}),
        ("Улога",{"fields":("role",)}),
        ("Permissions", {"fields":("is_active","is_staff","is_phone_verified","is_superuser","groups","user_permissions"),}),
        ("Important dates",{"fields":("last_login","date_joined"),})
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide"),
            "fields":("phone_number","password1","password2","role","is_active","is_staff"),
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
    list_display = ("id", "user", "specialization", "hospital", "approved",)
    search_fields = ("user__first_name", "user__last_name","specialization","hospital",)
    list_filter = ("hospital","approved",)

@admin.register(DoctorDepartmentAssignment)
class DoctorDepartmentAssignmentAdmin(admin.ModelAdmin):
    list_display = ("id","doctor","department",)
    search_fields = ("doctor__user__first_name","doctor__user__last_name","department__name","department__hospital__name",)
    list_filter = ("department","department__hospital")

@admin.register(DoctorService)
class DoctorServiceAdmin(admin.ModelAdmin):
    list_display = ("id", "doctor", "service",)
    search_fields = ("doctor__user__first_name","doctor__user__last_name","service__name","service__department__name","service__department__hospital__name",)
    list_filter = ("service",)

admin.site.register(User, UserAdmin)

# Register your models here.
