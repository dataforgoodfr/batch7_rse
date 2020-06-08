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
    search = re.split((" "), search)
    highlighted = text
    for i in search:
        highlighted = highlighted.replace(i, '<span class="highlight">{}</span>'.format(i))

    return mark_safe(highlighted)