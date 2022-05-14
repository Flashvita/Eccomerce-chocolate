from django.shortcuts import render
from django import views
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login
from .cart import Cart
from .models import Product, Category, Customer, Order, OrderItem, Notification
from .forms import ProductAddToCartForm, RegistrationForm, LoginForm, OrderCreateForm
from .utils import verify
from django.contrib.auth.views import LogoutView
from django.views.generic.list import ListView
from .tasks import order_created, new_customer
import braintree
from .mixins import NotificationsMixin


class BaseView(NotificationsMixin, views.View):
    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        products = Product.objects.filter(available=True)
        context = {
            'products': products,
            'categories': categories,
            'notifications': self.notifications(request.user)
        }
        return render(request, 'base.html', context)


class ProductAddToCartView(views.View):
    def post(self, request, pk, *args, **kwargs):
        cart = Cart(request)
        product = get_object_or_404(Product, id=pk)
        form = ProductAddToCartForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            cart.add(product=product,
                     quantity=cd['quantity'],
                     update_quantity=cd['update'])
        return HttpResponseRedirect(request.META['HTTP_REFERER'])


class ProductRemoveFromCartView(views.View):
    def post(self, request,  pk, *args, **kwargs):
        cart = Cart(request)
        product = get_object_or_404(Product, id=pk)
        cart.remove(product)
        return HttpResponseRedirect(request.META['HTTP_REFERER'])


    def get(self, request, pk, *args, **kwargs):
        cart = Cart(request)
        product = get_object_or_404(Product, pk=pk)
        cart.remove(product)
        return HttpResponseRedirect(request.META['HTTP_REFERER'])


class CartDetailView(views.View):
    def get(self, request, *args, **kwargs):
        cart = Cart(request)
        for item in cart:
            item['update_quantity'] = ProductAddToCartForm(
                initial={'quantity': item['quantity'],
                         'update': True})
        context = {
            'cart': cart,
        }
        return render(request, 'cart/cart-detail.html', context)


class CategoryView(views.View):
    def get(self, request, pk, *args, **kwargs):
        category = Category.objects.get(pk=pk)
        products = Product.objects.filter(category=category)
        context = {
            'products': products,

        }
        return render(request, 'catalog/category-detail.html', context)


class ProductDetailView(views.View):
    def get(self, request, pk, *args, **kwargs):
        product = get_object_or_404(Product, pk=pk)
        form = ProductAddToCartForm()
        context = {
            'product': product,
            'form': form
        }
        return render(request, 'catalog/product-detail.html', context)


class CustomerRegistrationView(views.View):
    """Регистрация для пользователя"""
    def get(self, request, *args, **kwargs):
        form = RegistrationForm(request.POST or None)
        context = {
            'form': form
        }
        return render(request, 'auth/registration.html', context)

    def post(self, request, *args, **kwargs):
        form = RegistrationForm(request.POST or None)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.username = form.cleaned_data['username']
            new_user.email = form.cleaned_data['email']
            new_user.first_name = form.cleaned_data['first_name']
            new_user.last_name = form.cleaned_data['last_name']
            new_user.save()
            new_user.set_password(form.cleaned_data['password'])
            new_user.save()
            Customer.objects.create(
                user=new_user,
            )
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            login(request, user)
            new_customer.delay(user.customer.id)
            return HttpResponseRedirect('/')
        context = {
            'form': form
        }
        return render(request, 'auth/registration.html', context)


class EmailVerifyView(views.View):
    pass


class LoginView(views.View):
    """Вход для пользователя"""
    def get(self, request, *args, **kwargs):
        form = LoginForm(request.POST or None)
        context = {
            'form': form
        }
        return render(request, 'accounts/login.html', context)

    def post(self, request, *args, **kwargs):
        form = LoginForm(request.POST or None)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                return HttpResponseRedirect('/')

        context = {'form': form}
        return render(request, 'accounts/login.html', context)


class LogoutUserView(LogoutView):
    next_page = 'base'
    template_name = 'base.html'


class OrderCreateView(views.View):
    def get(self, request, *args, **kwargs):
        form = OrderCreateForm(request.POST or None)
        context = {
            'form': form,
        }
        return render(request, 'cart/new-order.html', context)

    def post(self, request, *args, **kwargs):
        form = OrderCreateForm(request.POST)
        context = {
            'form': form,
        }
        if form.is_valid():
            order = form.save(commit=False)
            order.customer = request.user.customer
            order.address = form.cleaned_data['address']
            order.city = form.cleaned_data['city']
            order.buying_type = form.cleaned_data['buying_type']
            order.comment = form.cleaned_data['comment']
            order = form.save()
            cart = Cart(request)

            for item in cart:
                OrderItem.objects.create(
                    order=order, product=item['product'], price=item['price'], quantity=item['quantity']
                )
            cart.clear()
            order_created.delay(order.id)
            request.session['order_id'] = order.id
            return render(request, 'payment/process.html', context)

        return render(request, 'cart/new-order.html', context)


class PaymentView(views.View):
    def get(self, request, *args, **kwargs):
        order_id = request.session.get('order_id')
        order = get_object_or_404(Order, id=order_id)
        client_token = braintree.ClientToken.generate()
        return render(request,
                      'payment/process.html',
                      {'order': order,
                       'client_token': client_token})

    def post(self, request, *args, **kwargs):
        order_id = request.session.get('order_id')
        order = get_object_or_404(Order, id=order_id)
        nonce = request.POST.get('payment_method_nonce', None)
        # Создание и сохранение транзакции.
        result = braintree.Transaction.sale({
            'amount': '{:.2f}'.format(order.get_total_cost()),
            'payment_method_nonce': nonce,
            'options': {
                'submit_for_settlement': True
            }
        })
        if result.is_success:

            # Отметка заказа как оплаченного.
            order.paid = True
            # Сохранение ID транзакции в заказе.
            order.braintree_id = result.transaction.id
            order.save()
            return HttpResponseRedirect('/payment/done/')
        else:
            return HttpResponseRedirect('/payment/cancel/')


class PaymentDoneView(views.View):
    def get(self, request, *args, **kwargs):
        return render(request, 'process/done.html', {})


class PaymentCancelView(views.View):
    def get(self, request, *args, **kwargs):
        return render(request, 'process/cancel.html', {})

class ClearNotificationsView(views.View):

    @staticmethod
    def get(request, *args, **kwargs):
        Notification.objects.make_all_read(request.user.customer)
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
