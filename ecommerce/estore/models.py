# Imports
        
from django.conf import settings
from django.db import models
from django.shortcuts import reverse
from django.utils import timezone
from django.utils.text import slugify
from django_countries.fields import CountryField
from localflavor.us.models import USStateField
from decimal import Decimal
from django.core.exceptions import ValidationError





# Create your models here.

CATEGORY_CHOICES = (
    ('S', 'Shirt'),
    ('J', 'Jackets'),
    ('SN', 'Sneakers'),
    ('P', 'Pants'),
)

COUNTRY_CHOICES = [    
    ('AU', 'Australia'),
    ('CA', 'Canada'),
    ('DK', 'Denmark'),    
    ('FI', 'Finland'),    
    ('FR', 'France'),    
    ('DE', 'Germany'),
    ('IE', 'Ireland'),    
    ('IT', 'Italy'),    
    ('JP', 'Japan'),    
    ('LU', 'Luxembourg'),    
    ('NL', 'Netherlands'),    
    ('NZ', 'New Zealand'),    
    ('NO', 'Norway'),    
    ('PT', 'Portugal'),    
    ('SG', 'Singapore'),    
    ('KR', 'South Korea'),    
    ('ES', 'Spain'),    
    ('SE', 'Sweden'),    
    ('CH', 'Switzerland'),    
    ('GB', 'United Kingdom'),    
    ('US', 'United States'),]


LABEL_CHOICES = (
    ('P', 'primary'),
    ('S', 'secondary'),
    ('D', 'danger'),
)

GENDER_CHOICES = [
        ('M', 'Men'),
        ('F', 'Women'),
    ]

class Item(models.Model):
    title = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=0)
    discount_price = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=2, default='S')
    label = models.CharField(choices=LABEL_CHOICES, max_length=1, default='P')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='Men')
    image = models.ImageField(default='static/images/camoflagecargopants.png')
    id = models.AutoField(primary_key=True)
    slug = models.SlugField(default='', blank=True)
    description = models.TextField(default='This is description')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("product", kwargs={
            'slug': self.slug
        })

    def get_add_to_cart_url(self):
        return reverse("add-to-cart", kwargs={
            'slug': self.slug
        })

    def get_remove_from_cart_url(self):
        return reverse("remove-from-cart", kwargs={
            'slug': self.slug
        })


class OrderItem(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=None)
    ordered = models.BooleanField(default=False)
    quantity = models.PositiveIntegerField(default=1)
    discount = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)

    def __str__(self):
        return f"{self.quantity} of {self.item.title}"

    def get_total_item_price(self):
        return self.quantity * self.item.price

    def get_total_discount_item_price(self):
        return self.quantity * self.item.discount_price

    def get_amount_saved(self):
        return self.get_total_item_price() - self.get_total_discount_item_price()

    def get_final_price(self):
        if self.item.discount_price:
            return self.get_total_discount_item_price()
        return self.get_total_item_price()


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ordered_date = models.DateTimeField(auto_now_add=True)
    ordered = models.BooleanField(default=False)
    items = models.ManyToManyField(OrderItem)
    shipping_address = models.ForeignKey('Address', related_name='shipping_address', on_delete=models.SET_NULL, blank=True, null=True)
    billing_address = models.ForeignKey('Address', related_name='billing_address', on_delete=models.SET_NULL, blank=True, null=True)
    payment = models.ForeignKey('Payment', on_delete=models.SET_NULL, blank=True, null=True)
    coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL, blank=True, null=True)

    def get_total_discount_item_price(self):
        total = 0
        for item in self.items.all():
            if item.item.discount_price is not None:
                total += item.quantity * item.item.discount_price
            else:
                total += item.quantity * item.item.price
        return total

    def get_total_price(self):
        total = sum(item.get_total_item_price() for item in self.items.all())
        if self.coupon:
            discount = self.coupon.discount / Decimal('100')
            total_discount = sum(item.get_total_discount_item_price() for item in self.items.all() if item.item.discount_price is not None)
            total -= total_discount
            total *= (1 - discount)
        return total

    def get_amount_saved(self):
        return self.get_total_discount_item_price() - self.get_total_price()

class Coupon(models.Model):
    code = models.CharField(max_length=15, unique=True)
    discount = models.IntegerField(default=0)

    def __str__(self):
        return self.code

class Checkout(models.Model):
    street_address = models.CharField(max_length=100, blank=True)
    country = models.CharField(choices=COUNTRY_CHOICES, max_length=50)
    zip_code = models.CharField(max_length=10, blank=True)
    same_billing_address = models.BooleanField(default=False)
    save_as_default = models.BooleanField(default=False)


class Address(models.Model):
    PAYMENT_OPTIONS = (
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('bitcoin', 'Bitcoin'),
    )

    ADDRESS_CHOICES = (
        ('B', 'Billing'),
        ('S', 'Shipping'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=None)
    street_address = models.CharField(max_length=100, blank=True)
    apartment_address = models.CharField(max_length=100, blank=True)
    country = CountryField(multiple=False)
    zip_code = models.CharField(max_length=10, blank=True, default=0)  # Required for first zip code
    address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES)
    set_default_address = models.BooleanField(default=False)
    payment_option = models.CharField(choices=PAYMENT_OPTIONS, max_length=10, default='stripe')

    def __str__(self):
        return f'{self.user.username}, {self.street_address}, {self.apartment_address}, {self.country.name}, {self.zip_code}'

    def clean(self):
        # Check if all required fields are filled
        if not self.street_address or not self.country or not self.zip_code:
            raise ValidationError('All required fields must be filled.')

    class Meta:
        verbose_name_plural = 'Addresses'


class Payment(models.Model):
    stripe_charge_id = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.charge_id

