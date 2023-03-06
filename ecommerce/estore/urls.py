from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    path('', views.itemlist, name='item-list'),
    path('cart', views.cart, name='cart'),
    path('checkout', views.checkout, name='checkout'),
    path('checkout/use-default-address/', views.use_default_address, name='use_default_address'),
    path('product/<str:product_id>/', views.product, name='product'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('place_order', views.place_order, name='place_order'),
    path('add_coupon', views.add_coupon, name='add_coupon'),
    path('get_coupon/<int:code>/', views.get_coupon, name='get_coupon'),
    path('payment', views.payment, name='payment'),
    path('search', views.search, name='search'),
    path('category', views.category, name='category'),
    path('men', views.men, name='men'),
    path('women', views.women, name='women'),
]  + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


    