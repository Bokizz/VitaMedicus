from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied

class NotBlacklisted(BasePermission):
    message = "Вашиот акаунт е блокиран од страна на администраторите. За повеќе информации контактирајте поддршка за корисници."
    def has_permission(self, request, view):
        user = request.user
        if user and user.is_authenticated and user.is_blacklisted:
            raise PermissionDenied(self.message)
        return True