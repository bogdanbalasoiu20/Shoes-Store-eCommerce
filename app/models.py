from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.urls import reverse

class Brands(models.TextChoices):
    none="none", "None"
    nike="nike", "Nike"
    adidas="adidas", "Adidas"
    puma= "puma", "Puma"
    under_armour= "under armour", "Under Armour"
    reebok= "reebok", "Reebok"
    kipsta= "kipsta", "Kipsta"
    fila= "fila", "Fila"
    unknown='unknown','Unknown'
    
    
class Category(models.TextChoices):
    none="none", "None"
    sneakers='sneakers','Sneakers'
    football='football', 'Football'
    basketball='basketball', 'Basketball'
    tenis='tenis', 'Tenis'
    handball='handball','Handball'
    fitness='fitness','Fitness'
    cycling='cycling','Cycling'
    hiking='hiking','Hiking'
    
    

class Product(models.Model):
    name=models.CharField(max_length=100)
    description=models.TextField()
    price=models.DecimalField(max_digits=10,decimal_places=2)
    image=models.ImageField(upload_to='shoes/',blank=True,null=True)
    brand=models.CharField(max_length=50,choices=Brands.choices,default=Brands.none)
    category=models.CharField(max_length=50,choices=Category.choices,default=Category.none)
    supplier=models.ForeignKey('Supplier',on_delete=models.CASCADE,default=None)
    
    def __str__ (self):
        return self.name
    
    
    def get_absolute_url(self):
        return reverse('product_detail', args=[str(self.id)])
    
    

class Supplier(models.Model):
    name=models.CharField(max_length=100)
    country=models.CharField(max_length=50)
    contact_info=models.CharField(max_length=100,blank=True,null=True)
    address=models.TextField(blank=True,null=True)
    
    def __str__(self):
        return self.name
    

class Size(models.Model):
    size=models.DecimalField(max_digits=3,decimal_places=1)
    
    def __str__(self):
        return f"{self.size}"
    

class ReviewTitle(models.TextChoices):
    very_good='very good', "Very Good"
    good='good', 'Good'
    ok='ok','Ok'
    bad='bad',"Bad"
    very_bad="very bad","Very Bad"
   
class Review(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, default=None)
    title = models.CharField(max_length=20, choices=ReviewTitle.choices)
    message = models.TextField(blank=True, null=True)
    rating = models.PositiveIntegerField()
    date = models.DateField()

    def __str__(self):
        return f"{self.product} - {self.rating}/5"
    

class DiscountType(models.TextChoices):
    PERCENTAGE = 'percentage', 'Percentage'
    FIXED_AMOUNT = 'fixed_amount', 'Fixed Amount'



class Offer(models.Model):
    name = models.CharField(max_length=50)
    discount_type = models.CharField(
        max_length=50,
        choices=DiscountType.choices,
        default=DiscountType.PERCENTAGE
    )
    discount_value = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    product = models.ManyToManyField('Product', related_name='offers',blank=True)
    category = models.ManyToManyField('CategoryModel', related_name='offers',blank=True)

    def __str__(self):
        if self.discount_type == DiscountType.PERCENTAGE:
            discount_display = f"{self.discount_value}%"
        else:
            discount_display = f"{self.discount_value} LEI"

        return f"{self.name} ({discount_display})"

    def is_currently_active(self):
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date
    
    
    def get_absolute_url(self):
        return reverse("offer_detail", kwargs={"id": self.id})
    
    
    class Meta:  #clasa Meta are rolul de a adauga optiuni suplimentare legate clasa respectiva
        permissions=[
            ('can_view_offer','The user can view the offer')
        ]
    
    
class CustomUser(AbstractUser):
    phone_number=models.CharField(max_length=15)
    birth_date=models.DateField()
    profile_picture=models.ImageField(upload_to='profile/',blank=True,null=True)
    country=models.CharField(max_length=50)
    city=models.CharField(max_length=50,default='Bucharest')
    address=models.TextField()
    postal_code=models.CharField(max_length=10)
    code=models.CharField(max_length=100,null=True)
    email_confirmed=models.BooleanField(default=False)
    is_blocked=models.BooleanField(default=False)
    
    def __str__(self):
        return self.username
    
    

class Views(models.Model):
    user=models.ForeignKey('CustomUser', on_delete=models.CASCADE, default=None)
    product=models.ForeignKey('Product', on_delete=models.CASCADE, default=None)
    view_date=models.DateField(default=timezone.now)
    
    class Meta:
        ordering=['-view_date']  #filtrez vizualizarile dupa cele mai recente primite
        
    def __str__(self):
        return f"{self.user} - {self.product} - {self.view_date}"
    
    
class CategoryModel(models.Model):
    name=models.CharField(max_length=50)
    
    def __str__(self):
        return self.name
    
    
class DiscountCode(models.Model):
    code=models.CharField(max_length=5)
    end_date=models.DateField()
    lucky_user=models.CharField(max_length=100,default=None)
    
    def __str__(self):
        return self.code
    
    

class ProductSizeStock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    stock = models.PositiveIntegerField(default=0)  # Cantitatea de stoc disponibilă

    def __str__(self):
        return f"Product: {self.product.name}, Size: {self.size.size}, Stock: {self.stock}"
    
    
    
class Order(models.Model):
    user=models.ForeignKey('CustomUser', on_delete=models.CASCADE, default=None)
    order_date=models.DateField(default=timezone.now().date())
    
    def __str__ (self):
        return f"Order {self.id} - user {self.user} - order date {self.order_date}"
    
    
class OrderProduct(models.Model):
    order=models.ForeignKey('Order',on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity=models.PositiveIntegerField()
    
    def __str__ (self):
        return f"Order {self.order.id} - product {self.product.name} - quantity {self.quantity}"
    
    