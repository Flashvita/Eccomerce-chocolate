from datetime import timezone
from datetime import datetime
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.safestring import mark_safe
from django.db.models.signals import post_save, pre_save
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.urls import reverse

User = get_user_model()


class Category(models.Model):
    title = models.CharField(max_length=50, verbose_name='Заголовок')
    slug = models.SlugField()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('category-detail', args=[self.id])

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class Product(models.Model):
    title = models.CharField(max_length=50, verbose_name='Название')
    slug = models.SlugField()
    description = models.TextField(max_length=300,  null=True, blank=True, verbose_name='Описание')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Категория')
    image = models.ImageField(upload_to='products/', null=True, blank=True, verbose_name='Изображение')
    price = models.DecimalField(max_digits=5, decimal_places=0, verbose_name='Цена')
    manufacturer = models.CharField(max_length=100, null=True, blank=True, verbose_name='Производитель')
    weight = models.DecimalField(max_digits=5, decimal_places=0, null=True, blank=True, verbose_name='Вес')
    available = models.BooleanField(default=True, verbose_name='Наличие товара')
    quantity = models.DecimalField(max_digits=999, decimal_places=0, verbose_name='Количество')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('product-detail', args=[self.id])

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    customer_orders = models.ManyToManyField(Product, blank=True,
                                             verbose_name='Заказы покупателя',
                                             related_name='related_customer'
                                             )
    phone = models.CharField(max_length=11, verbose_name='номер телефона')
    address = models.TextField(null=True, blank=True, verbose_name='адресс')
    favourite = models.ManyToManyField(Product, verbose_name='Избранное')
    id = models.AutoField(primary_key=True)
    email_verify = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

    class Meta:
        verbose_name = 'Покупатель'
        verbose_name_plural = 'Покупатели'


class Order(models.Model):

    STATUS_NEW = 'new'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_READY = 'is_ready'
    STATUS_COMPLETED = 'completed'

    BUYING_TYPE_SELF = 'self'
    BUYING_TYPE_DELIVERY = 'delivery'

    STATUS_CHOICES = (
        (STATUS_NEW, 'Новый заказ'),
        (STATUS_IN_PROGRESS, 'Заказ в обработке'),
        (STATUS_READY, 'Заказ готов'),
        (STATUS_COMPLETED, 'Заказ получен покупателем')
    )

    BUYING_TYPE_CHOICES = (
        (BUYING_TYPE_SELF, 'Самовывоз'),
        (BUYING_TYPE_DELIVERY, 'Доставка')
    )
    customer = models.ForeignKey('Customer', verbose_name='Покупатель', related_name='orders', on_delete=models.CASCADE)
    city = models.CharField(max_length=100, verbose_name='Город')
    address = models.CharField(max_length=300, verbose_name='Адрес', null=True, blank=True)
    status = models.CharField(max_length=100, verbose_name='Статус заказа', choices=STATUS_CHOICES, default=STATUS_NEW)
    buying_type = models.CharField(max_length=100, verbose_name='Тип заказа', choices=BUYING_TYPE_CHOICES)
    comment = models.TextField(verbose_name='Комментарий к заказу', null=True, blank=True)
    created_at = models.DateField(verbose_name='Дата создания заказа', auto_now=True)
    postal_code = models.CharField(max_length=50)
    braintree_id = models.CharField(max_length=150, blank=True)
    paid = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return 'Заказ {}'.format(self.id)

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='сумма заказа')
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return '{}'.format(self.id)

    def get_cost(self):
        return self.price * self.quantity


class NotificationManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset()

    def all(self, recipient):
        return self.get_queryset().filter(
            recipient=recipient,
            read=False
        )

    def make_all_read(self, recipient):
        qs = self.get_queryset().filter(recipient=recipient, read=False)
        qs.update(read=True)


class Notification(models.Model):
    """Уведомления"""

    recipient = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name='Получатель')
    text = models.TextField()
    read = models.BooleanField(default=False)
    objects = NotificationManager()

    def __str__(self):
        return f"Уведомление для {self.recipient.user} | id={self.id}"

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'


def send_notification(instance, **kwargs):
    if instance.status:
        order_customer = Order.objects.get(id=instance.id)
        if order_customer:
            Notification.objects.create(
                recipient=order_customer.customer,
                text=mark_safe(f'Вас заказ оформлен.Статус заказа {instance.status}'),
            )

post_save.connect(send_notification, sender=Order)


