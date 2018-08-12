from django import template

register = template.Library()

@register.simple_tag
def relative_url(value, field_name, urlencode=None):
    url = '?{}={}'.format(field_name, value)
    if urlencode:
        querystring = urlencode.split('&')
        filtered_querystring = filter(lambda p: p.split('=')[0] != field_name, querystring)
        encoded_querystring = '&'.join(filtered_querystring)
        url = '{}&{}'.format(url, encoded_querystring)
    return url


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