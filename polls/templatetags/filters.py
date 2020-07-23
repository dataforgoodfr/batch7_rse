from django.template import Library
import re
from django.utils.safestring import mark_safe

register = Library()


@register.filter(name='add_attr')
def add_attr(field, css):
    attrs = {}
    definition = css.split(',')

    for d in definition:
        if ':' not in d:
            attrs['class'] = d
        else:
            key, val = d.split(':')
            attrs[key] = val

    return field.as_widget(attrs=attrs)

@register.filter(name='percentage')
def percentage(value):
    return format(value, ".2%")

@register.filter
def highlight(text, search):
    highlighted = text
    for i in search:
        if i[1]<30:
            highlighted = highlighted.replace(i[0], '<span style="background-color: #fff9a3;">{}</span>'.format(i[0]))
        if i[1]<50:
            highlighted = highlighted.replace(i[0], '<span style="background-color: #fff56b;">{}</span>'.format(i[0]))
        else:
            highlighted = highlighted.replace(i[0], '<span style="background-color: ##ffc014;">{}</span>'.format(i[0]))

    return mark_safe(highlighted)