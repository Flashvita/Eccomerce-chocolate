from django.urls import path
from django.views.generic import TemplateView
from . import views
from django.contrib.auth import views as auth_views
from .views import (
    BaseView,
    CartDetailView,
    ProductAddToCartView,
    CategoryView,
    ProductDetailView,
    CustomerRegistrationView,
    EmailVerifyView,
    LoginView,
    LogoutUserView,
    ProductRemoveFromCartView,
    OrderCreateView,
)


urlpatterns = [
    path('cart/cart_detail/', CartDetailView.as_view(), name='cart_detail'),
    path('add/<int:pk>/', ProductAddToCartView.as_view(), name='add-to-cart'),
    path('remove/<int:pk>/', ProductRemoveFromCartView.as_view(), name='remove-from-cart'),
    path('', BaseView.as_view(), name='base'),
    path('auth/verify-email/<uidb64>/<token>/', EmailVerifyView.as_view(), name='email-veryfi'),
    path('auth/verify-letter', TemplateView.as_view(template_name='auth/verify-letter.html'), name='verify'),
    path('auth/registration/', CustomerRegistrationView.as_view(), name='registration'),
    path('auth/logout/', LogoutUserView.as_view(), name='logout'),
    path('auth/password_reset/done/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('auth/password_reset_done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('auth/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('accounts/login/', LoginView.as_view(), name='login'),
    path('cart/cart-detail/', CartDetailView.as_view(), name='cart-detail'),
    path('add/<int:pk>/', ProductAddToCartView.as_view(), name='add_to_cart'),
    path('catalog/<int:pk>/', CategoryView.as_view(), name='category-detail'),
    path('catalog/product-detail/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('cart/new-order', OrderCreateView.as_view(), name='new-order'),

]
