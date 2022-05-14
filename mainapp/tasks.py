from OnlineShop.celery import app
from django.core.mail import send_mail
from .models import Order, Customer



@app.task
def order_created(order_id):
    """Задача отправки email-уведомлений при успешном оформлении заказа."""
    order = Order.objects.get(id=order_id)
    subject = 'Order nr. {}'.format(order.id)
    message = 'Дорогой {},\n\nВаш заказ успешно оформлен.\
    Номер заказа {}.'.format(order.customer, order.id)
    mail_sent = send_mail(subject, message, 'DjangoTestemail2022@gmail.com', [order.customer.user.email])
    return mail_sent


@app.task
def new_customer(customer_id):
    """Задача отправки email-уведомлений при регистрации."""
    customer = Customer.objects.get(id=customer_id)
    subject = 'Регистрация. {}'.format(customer.id)
    message = 'Дорогой {},\n\nВы успешно зарегестировались на OnlineShop.'.format(customer)
    mail_sent = send_mail(subject, message, 'DjangoTestemail2022@gmail.com', [customer.user.email])
    return mail_sent
