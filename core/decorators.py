from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

def group_required(*group_names):
    """
    Decorator for views that checks that the user is in at least one of the
    given groups.
    """
    def check_groups(user):
        if user.groups.filter(name__in=group_names).exists() or user.is_superuser:
            return True
        raise PermissionDenied
    return user_passes_test(check_groups)

def group_forbidden(*group_names):
    """
    Decorator for views that checks that the user is NOT in any of the given
    groups.
    """
    def check_groups(user):
        if user.groups.filter(name__in=group_names).exists():
            raise PermissionDenied
        return True
    return user_passes_test(check_groups)