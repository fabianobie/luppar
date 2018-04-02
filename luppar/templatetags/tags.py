
from django import template
from django.core.urlresolvers import reverse, NoReverseMatch

register = template.Library()


@register.simple_tag(takes_context=True)
def active(context, urlnames):
    listw = urlnames.split(',')
    try:
        for c in listw:
            if(c in context['request'].path):
                return 'active'
    except:
        return ''
    return ''