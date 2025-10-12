from rest_framework.permissions import BasePermission


class IsAuthor(BasePermission):

    def has_object_permission(self, request, view, obj):
        """Доступ только владельцу объекта."""
        return request.user == obj.owner and request.user.is_authenticated
