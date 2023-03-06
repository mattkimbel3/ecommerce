from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from .models import Item, OrderItem, Order, Checkout, Address, Payment, Coupon
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django_countries import countries
from django.contrib import messages
from django_countries.fields import CountryField
from django.conf import settings
import http.client
import stripe
from django.http import JsonResponse
from django.forms import model_to_dict





# ... after processing the form data ...


# Create your views here.
def itemlist(request):
    order = Order.objects.get_or_create(user=request.user, ordered=False)[0]
    order_items = order.items.all()
    order_item_count = order_items.count()
    context = {
        'items': Item.objects.all(),
        'order_items': order_items,
        'order_item_count': order_item_count,
    }
    return render(request, "home.html", context)

@login_required
def cart(request):
    order = Order.objects.get_or_create(user=request.user, ordered=False)[0]
    order_items = order.items.all()
    order_item_count = order_items.count()
    context = {
        'order_items': order_items,
        'order_item_count': order_item_count,
        'order': order,
        'get_total_price': order.get_total_price()
    }
    return render(request, 'cart.html', context)


@login_required
def add_to_cart(request, product_id):
    item = get_object_or_404(Item, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__id=product_id).exists():
            order_item.quantity = quantity
            order_item.save()
        else:
            order_item.quantity = quantity
            order_item.save()
            order.items.add(order_item)
    else:
        order_date = timezone.now()
        order = Order.objects.create(user=request.user, ordered_date=order_date)
        order_item.quantity = quantity
        order_item.save()
        order.items.add(order_item)
    return redirect('cart')


@login_required
def remove_from_cart(request, product_id):
    item = get_object_or_404(Item, id=product_id)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__id=item.id).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
    return redirect('cart')


@login_required
def checkout(request):
    order = Order.objects.get(user=request.user, ordered=False)
    order_items = order.items.all()
    order_item_count = order_items.count()
    addresses = request.user.address_set.all()
    default_address = None
    has_default_address = Address.objects.filter(user=request.user, set_default_address=True).first()


    


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
        ('US', 'United States'),
    ]

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip_code = request.POST.get('zip_code')
        country = request.POST.get('country')
        same_billing_address = request.POST.get('same_billing_address') == 'on'
        save_as_default = request.POST.get('save_as_default') == 'on'
        use_default_address = request.POST.get('use_default_address') =='on'
        selected_payment_option = request.POST.get('selected_payment_option')
        print(selected_payment_option)

        payment_option = 'Stripe'

        if selected_payment_option == 'stripe':
            payment_option = 'Stripe'
        elif selected_payment_option == 'paypal':
            payment_option = 'PayPal'
        elif selected_payment_option == 'bitcoin':
            payment_option = 'Bitcoin'

        # functionality
        # same shipping address
        # Save info 

        # Billing Address
        billing_address = order.billing_address
        if billing_address:
            billing_address.street_address = request.POST.get('shipping_address')
            billing_address.apartment_address = request.POST.get('shipping_address2')
            billing_address.country = request.POST.get('country')
            billing_address.zip_code = request.POST.get('zip_code')
            billing_address.save()
        else:
            billing_address = Address.objects.create(
                user=request.user,
                street_address=request.POST.get('shipping_address'),
                apartment_address=request.POST.get('shipping_address2'),
                country=request.POST.get('country'),
                zip_code=request.POST.get('zip_code'),
                address_type='S'
            )

            order.billing_address = billing_address
            order.save()

        # Shipping Address
        if same_billing_address:
            shipping_address = Address.objects.create(
                user=request.user,
                street_address=billing_address.street_address,
                apartment_address=billing_address.apartment_address,
                country=billing_address.country,
                zip_code=billing_address.zip_code,
                address_type='B'
            )

            order.shipping_address = shipping_address
            order.save()
        else:
            shipping_address = order.shipping_address
            if shipping_address:
                shipping_address.street_address = request.POST.get('shipping_address')
                shipping_address.apartment_address = request.POST.get('shipping_address2')
                shipping_address.country = request.POST.get('country')
                shipping_address.zip_code = request.POST.get('zip_code')
                shipping_address.save()
            else:
                shipping_address = Address.objects.create(
                    user=request.user,
                    street_address=request.POST.get('billing_address'),
                    apartment_address=request.POST.get('billing_address2'),
                    country=request.POST.get('billing_country'),
                    zip_code=request.POST.get('billing_zip_code'),
                    address_type='B'
                )

                order.shipping_address = shipping_address
                order.save()

        # Check if user wants to save shipping address as default
        save_as_default_shipping = request.POST.get('save_as_default_shipping', False)  

        if save_as_default_shipping:
            print("Saving address as default...")
            
            # Check if there is an existing default address in the database
            if has_default_address:
                print("Found existing default address:", has_default_address.id)
                print(f"Here is the default address: {has_default_address}")
                if has_default_address.id != shipping_address.id:
                    has_default_address.set_default_address = False
                    has_default_address.save()
            else:
                shipping_address.set_default_address = True
                shipping_address.save()
                
            billing_default_address = Address.objects.filter(user=request.user, set_default_address=True, address_type='S').first()
            if billing_default_address:
                if billing_default_address.id != billing_address.id:
                    billing_default_address.set_default_address = False
                    billing_default_address.save()
            else:
                billing_address.set_default_address = True
                billing_address.save()
                
        else:
            print("Not saving address as default.")



        order.full_name = full_name
        order.address = address
        order.city = city
        order.state = state
        order.zip_code = zip_code
        order.country = country
        order.same_billing_address = same_billing_address
        order.set_default_address = save_as_default
        order.payment_option = payment_option
        order.save()


        return redirect('payment')


    # If the request method is not POST, render the checkout page with the form
    print(default_address) # Add this line to check if default_address is not None
    context = {
        'order': order,
        'order_item_count': order_item_count,
        'order_items': order_items,
        'addresses': addresses,
        'COUNTRY_CHOICES': COUNTRY_CHOICES,
        'default_address': default_address,
        'has_default_address': has_default_address,
        'DISPLAY_COUPON_FORM': True
    }
    messages.success(request, 'Your order has been submitted!')
    return render(request, "checkout.html", context)

@login_required
def use_default_address(request):
    default_address = Address.objects.filter(user=request.user, set_default_address=True).first()

    if default_address:
        order = Order.objects.get(user=request.user, ordered=False)
        order.shipping_address = default_address
        order.billing_address = default_address
        order.save()

    return redirect('payment')


def update_billing_address(request):
    billing_address = Address.objects.get(user=request.user)
    if request.method == 'POST':
        billing_address.street_address = request.POST.get('street_address')
        billing_address.apartment_address = request.POST.get('apartment_address')
        billing_address.countries = request.POST.getlist('countries')
        billing_address.zip_code = request.POST.get('zip_code')
        billing_address.save()
        print(billing_address()) # add this line

    return render(request, 'checkout.html', {'billing_address': billing_address})



@login_required
def payment(request):
    order = Order.objects.get(user=request.user, ordered=False)
    order_items = order.items.all()
    order_item_count = order_items.count()

    # filter coupons based on validity and other criteria
    coupons = Coupon.objects.filter()
    if order.billing_address:
        if request.method == 'POST':
            stripe.api_key = "sk_test_51Mf7OnIs6Ovye6isOnTLjG0NqNdvhepWRqdujJLObrtBblKUcYhpYUdFT0YHLb7OfAeT97E4wSZ7NQP3Wheuq6lq00axFgymEn"
            token = request.POST.get('stripeToken')
            amount = sum(item.get_final_price() for item in order_items) * 100
            coupon_code = request.POST.get('code')

            if coupon_code:
                try:
                    # get the coupon based on the code entered by the user
                    coupon = Coupon.objects.get(code=coupon_code)
                except Coupon.DoesNotExist:
                    messages.error(request, 'Invalid coupon code')
                    return redirect('payment')
                else:
                    # apply the coupon to the order
                    order.apply_coupon(coupon)

            try:
                charge = stripe.Charge.create(
                    amount=amount,
                    currency='usd',
                    source=token,
                    description='Order Payment'
                )

                payment = Payment.objects.create(
                    stripe_charge_id=charge.id,
                    user=request.user,
                    amount=amount / 100,
                )

                # assign the payment to the order
                order_items = order.items.all()
                order_items.update(ordered=True)
                for item in order_items:
                    item.save()

                order.ordered = True
                order.payment = payment
                order.save()

                messages.success(request, 'Your order was successful!')
                return redirect('checkout_success')

            except stripe.error.CardError as e:
                body = e.json_body
                err = body.get('error', {})
                messages.error(request, f"{err.get('message')}")
                return redirect('payment')

            except stripe.error.StripeError as e:
                messages.error(request, 'An error occurred while processing your payment. Please try again later.')
                return redirect('payment')

            except Exception as e:
                messages.error(request, 'Serious Error occured. Please try again later.')
                return redirect('payment')

        context = {
            'order': order,
            'order_items': order_items,
            'order_item_count': order_item_count,
            'coupons': coupons,
            'DISPLAY_COUPON_FORM': False
        }
        return render(request, 'payment.html', context)
    else:
        messages.error(request, 'You have not added you billing address')
        return redirect('checkout')



def search(request):
    query = request.GET.get('query')
    items = Item.objects.filter(title__icontains=query)
    context = {
        'items': items,
        'query': query
    }
    return render(request, "search_results.html", context)


def product(request, product_id):
    order = Order.objects.get_or_create(user=request.user, ordered=False)[0]
    item = get_object_or_404(Item, id=product_id)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
    )
    order_items = order.items.all()
    order_item_count = order_items.count()
    context = {
        'item': item,
        'order': order, 
        'order_items': order_items,
        'order_item_count': order_item_count
    }
    return render(request, "product.html", context)

def category(request):
    items = Item.objects.filter(category=category)
    order = Order.objects.get_or_create(user=request.user, ordered=False)[0]
    order_items = order.items.all()
    order_item_count = order_items.count()
    context = {
        'items': items,
        'order': order, 
        'order_items': order_items,
        'order_item_count': order_item_count
    }
    return render(request, "category.html", context)

def men(request):
    items = Item.objects.filter(gender='M')
    return render(request, "men.html", {'items': items})



def women(request):
    items = Item.objects.filter(gender='F')
    return render(request, "women.html", {'items': items})

@login_required
def place_order(request):
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        order.ordered = True
        order.save()
    return render(request, "cart.html", context)

def my_view(request):
    context = {
        'countries': countries,
        'states': STATE_CHOICES,
    }
    return render(request, "checkout.html", context)

def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except Coupon.DoesNotExist:
        return None

def add_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        try:
            order = Order.objects.get(user=request.user, ordered=False)
            coupon = Coupon.objects.get(code=code)
            order.coupon = coupon
            order.save()
            messages.success(request, 'Coupon applied successfully.')
        except ObjectDoesNotExist:
            messages.warning(request, 'Invalid coupon code.')
        return redirect('checkout')
    else:
        return redirect('checkout')

