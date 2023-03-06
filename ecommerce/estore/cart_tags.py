from django import template
from .models import OrderItem
from django.utils import get_or_create_order

register = template.Library()

@register.simple_tag(takes_context=True)
def cart_item_count(context):
    request = context['request']
    order = get_or_create_order(request)
    order_item_count = OrderItem.objects.filter(order=order).count()
    return order_item_count

register.filter('cart_item_count', cart_item_count)

