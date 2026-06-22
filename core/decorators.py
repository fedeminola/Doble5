from django.contrib.auth.decorators import user_passes_test

def group_required(group_name):
    """
    Decorator for views that checks that the user is in a certain group.
    """
    def check_group(user):
        return user.groups.filter(name=group_name).exists()
    return user_passes_test(check_group)
