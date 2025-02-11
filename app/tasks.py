
import django
import os
from .models import CustomUser, Product, DiscountCode
from django.utils import timezone
import logging
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string 
import random
from datetime import timedelta

# se incarca setarile proiectului
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()


logger=logging.getLogger('django')


def remove_unconfirmed_users():
    users = CustomUser.objects.filter(email_confirmed=False)
    for user in users:
        try:
            user.delete()
            logger.debug(f"User {user.username} has been removed due to email unconfirmation")
        except Exception as e:
            logger.error(f"Error deleting user {user.username}: {e}")

            

def send_newsletter():
    x=10
    now=timezone.now()
    users=CustomUser.objects.all()
    for user in users:
        if (now-user.date_joined).total_seconds() > x*60 and user.email_confirmed:
            email=EmailMessage(
                subject='New shoes on our site',
                body=render_to_string('newsletter.html',{'username':user.username,'domain':'http://127.0.0.1:8000'}),
                from_email='balasoiu.bogdan@gmail.com',
                to=[user.email],
            )
            email.content_subtype='html'
            
            try:
                email.send(fail_silently=False) #Trimite e-mailul.Parametrul fail_silently indică dacă erorile ar trebui să fie ignorate (True) sau afișate (False).
                logger.info('Newsletter was sent successfully1')
            except Exception as e:
                logger.critical(f"An error occurred while sending the newsletter: {e}")
    
  
  
def delete_products_without_image():
    products=Product.objects.filter(image="")
    
    for product in products:
        try:
            product.delete()
            logger.debug(f"The product with id {product.id} has been deleted because it has no image")
        except Exception as e:
            logger.debug(f"Error deleting product with id {product.id}: {e}")
              
    
    
def random_discount_code():
    discount_code=get_random_string(5)
    now=timezone.now() 
    
    #sterg din tabel codurile expirate 
    codes_to_delete=DiscountCode.objects.filter(end_date__lt=now)
    for code in codes_to_delete:
        code.delete()
        logger.info(f"Code with id {code.id} was deleted successfully")
    
    users=CustomUser.objects.all()
    
    #aleg random un user valid care va primi codul si i-l transmit prin email
    while True:
        lucky_user=random.choice(users)
        if lucky_user.email_confirmed:
            DiscountCode.objects.create(code=discount_code,end_date=now+timedelta(days=7),lucky_user=lucky_user.username) #adaug in tabel un nou cod
            logger.info(f"New cod {discount_code} genereted - lucky user: {lucky_user} - genereted at {now} - expires at {now + timedelta(days=7)} ")
            break
        
    email=EmailMessage(
        subject='Discount Code',
        body=render_to_string('discount_code.html',{'username':lucky_user.username,'domain':'http://127.0.0.1:8000','code':discount_code,'end_date':now+timedelta(days=7)}),
        from_email='balasoiu.bogdan@gmail.com',
        to=[lucky_user.email]
    )
    
    email.content_subtype='html'
    
    try:
        email.send(fail_silently=False)
        logger.info('Discount code email was sent successfully')
    except Exception as e:
        logger.critical(f'An error occurred while sending the email for discount code: {e}')
    