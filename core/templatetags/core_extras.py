from django import template
from django.contrib.humanize.templatetags.humanize import intcomma

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter(name='human_decimal')
def human_decimal(value):
    if value is None:
        return "0,00"
    
    # Convierte a string con 2 decimales y reemplaza el punto por coma
    formatted_value = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return formatted_value