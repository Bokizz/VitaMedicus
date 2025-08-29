from django.contrib import admin
from .models import User, Doctor
from hospitals.models import *
from appointments.models import Appointment
from ratings.models import Rating
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone
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
            "fields":("phone_number","password1",
                    "password2","role","is_active",
                    "is_staff","is_blacklisted"),
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

@admin.action(description="Authorize doctors")
def authorize_doctors(modeladmin, request, queryset):
    for doctor in queryset:
        doctor.authorize()
        doctor.save() 
@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("id","first_name","last_name",
                     "user", "specialization", "hospital",
                       "authorized_display","is_blacklisted",)
    search_fields = ("user__first_name", "user__last_name",
                     "specialization","hospital",)
    list_filter = ("hospital","authorized",)
    def first_name(self, obj):
        return obj.user.first_name
    first_name.admin_order_field = "user__first_name"
    first_name.short_description = "First Name"

    def last_name(self, obj):
        return obj.user.last_name
    last_name.admin_order_field = "user__last_name"
    last_name.short_description = "Last Name"

    def is_blacklisted(self, obj):
        return obj.user.is_blacklisted
    is_blacklisted.short_description = "Blacklisted"

    actions = ['authorize_doctors',]
    def save_model(self, request, obj, form, change):
        if change and 'authorized' in form.changed_data and obj.authorized:
            obj.authorized = True
        super().save_model(request, obj, form, change)
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.authorized:
            return ("authorized_display",)
        return super().get_readonly_fields(request, obj)
    
    def authorized_display(self, obj):
        return "Authorized" if obj.authorized else "Not Authorized"
    authorized_display.short_description = "Authorized"

@admin.action(description="Approve selected doctor department assignments")
def approve_assignments(modeladmin, request, queryset):
    for assignment in queryset:
        assignment.approve()
        assignment.approved_at = timezone.now()
        assignment.save()  
@admin.register(DoctorDepartmentAssignment)
class DoctorDepartmentAssignmentAdmin(admin.ModelAdmin):
    list_display = ("id","assignment_display",
                    "approved_display","requested_at",
                    "approved_at",)
    search_fields = ("doctor__user__first_name","doctor__user__last_name",
                     "department__name","department__hospital__name",)
    list_filter = ("department","department__hospital",)

    # list_editable = ("approved_display",)
    actions = ['approve_assignments',]
    
    def save_model(self, request, obj, form, change):
        if change:
            if 'approved' in form.changed_data and obj.approved and not obj.approved_at:
                obj.approved_at = timezone.now()
        super().save_model(request, obj, form, change)
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.approved:
            return ("approved_display", "approved_at")
        return super().get_readonly_fields(request, obj)

    def approved_display(self, obj):
        return "Approved" if obj.approved else "Not Approved"
    approved_display.short_description = "Approved"
    
    def assignment_display(self, obj):
        return str(obj)
    assignment_display.short_description = "Assignment"

@admin.register(DoctorServiceAssignment)
class DoctorServiceAdmin(admin.ModelAdmin):
    list_display = ("id", 
                    "doctor", 
                    "service",
                    "approved_display","requested_at",
                    "approved_at")
    search_fields = ("doctor__user__first_name","doctor__user__last_name",
                     "service__name","service__department__name",
                     "service__department__hospital__name",)
    list_filter = ("service",)
    actions = ['approve_assignments',]
    
    def save_model(self, request, obj, form, change):
        if change:
            if 'approved' in form.changed_data and obj.approved and not obj.approved_at:
                obj.approved_at = timezone.now()
        super().save_model(request, obj, form, change)
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.approved:
            return ("approved_display", "approved_at")
        return super().get_readonly_fields(request, obj)

    def approved_display(self, obj):
        return "Approved" if obj.approved else "Not Approved"
    approved_display.short_description = "Approved"
    
    def assignment_display(self, obj):
        return str(obj)
    assignment_display.short_description = "Assignment"

    @admin.register(Appointment)
    class AppointmentAdmin(admin.ModelAdmin):
        list_display = ("id",
                        "patient",
                        "doctor",
                        "department",
                        "hospital",
                        "service",
                        "date",
                        "start_time",
                        "end_time",
                        "created_at",
                        "status")
        search_fields = ("patient__id",
        "doctor__id",
        "status")
        list_filter = (
            "hospital__name",
            "department__name",
            "status")

admin.site.register(User, UserAdmin)

# Register your models here.
