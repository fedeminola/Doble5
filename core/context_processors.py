from django.conf import settings

def nombre_establecimiento_processor(request):
    """
    Añade la variable NOMBRE_ESTABLECIMIENTO al contexto de todas las plantillas.
    """
    return {'NOMBRE_ESTABLECIMIENTO': settings.NOMBRE_ESTABLECIMIENTO}