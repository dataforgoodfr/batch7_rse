from django.template import Library
import math
from django.utils.safestring import mark_safe
from polls import nlp
from polls.models import Sentence

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
    return format(value, ".1%")


@register.filter
def highlight(text, search):
    search_pairs = [(word, nlp(word).vector) for word, _ in search]
    text_words = set(text.split())
    words_scores = []
    for w in text_words:
        for search_w, search_v in search_pairs:
            if search_w != w:
                sim = Sentence.similarity_vector(search_v, nlp(w).vector)
                if sim > 0.5:
                    words_scores.append((w, sim))
    words_scores = sorted(words_scores, key=lambda x: x[1], reverse=True)[:3]
    search = search + words_scores
    print(search)
    for i in search:
        text = text.replace(i[0], '<span style="background-color: rgba(255,255,0,{});">{}</span>'.format(i[1], i[0]))
    return mark_safe(text)
