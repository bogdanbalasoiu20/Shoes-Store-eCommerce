from django.contrib import admin
from .models import Product 
from .models import Supplier
from .models import Size
from .models import Review
from .forms import ReviewAdminForm
from .models import Offer
from .models import CustomUser
from .models import Views
from .models import CategoryModel
from .models import DiscountCode
from .models import ProductSizeStock, Order, OrderProduct
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
# Register your models here.

class ReviewAdmin(admin.ModelAdmin):
    form = ReviewAdminForm

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    fields=['name', 'description', 'price','image', 'brand','category','supplier']
    search_fields=['name']
    list_display=['name','price']
    
    list_filter = [
        'id',
        'name',
        'price',
        'brand',        
        'category',      
        'supplier',   
    ]
    
    #afiseaza 10 produse pe pagina
    list_per_page = 10
@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    search_fields=['name']
    fieldsets=(
        ('Main',{
            'fields':('name','country')
        }),
        ('Extra Details',{
            'fields':('contact_info','address')
        }),
    )
    list_display=['id','name','country']
    
@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    search_fields=['size']
    list_display=['size']
    ordering=['size']
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    search_fields=['product__name']
    list_display = ['id','product', 'rating', 'date']
@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    search_fields=['name']
    list_display=['id','name','start_date','end_date']
    
    
admin.site.site_header="Shoes Store Administration"
admin.site.site_title="Admin Panel - Shoes Store"
admin.site.index_title="Welcome to Admin Panel"


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('phone_number', 'birth_date', 'profile_picture', 'country','city', 'address', 'postal_code','code','email_confirmed','is_blocked')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('phone_number', 'birth_date', 'profile_picture', 'country','city' ,'address', 'postal_code','code','email_confirmed','is_blocked')}),
    )   
    
    list_display=['id','username','first_name','last_name','is_staff','is_blocked']
    
    #aceasta metoda face parte din clasa ModelAdmin si este folosita pentru a specifica campurile care vor fi doar in modul readonly(adica nu pot fi editate) in interfata Django Admin
    def get_readonly_fields(self, request, obj = None): #self - instanta clasei admin(CustomUserAdmin); request- obiectul cererii HTTP ce contine informatii despre utilizatorul logat; obj- obiectul curent care este editat in Admin, daca este None inseamna ca este crreat un obiect nou
        if request.user.groups.filter(name='Moderators').exists(): #verifica daca userul curent apartine de grupul Moderators
            return [field.name for field in self.model._meta.fields if field.name not in ('first_name','last_name','email','is_blocked')] #creeaza o lista cu numele tutror campurilor din CustomUser care nu sunt fisrt_name,last_name,email sau is_blocked; self.model._meta.fields returneaza toate campurile modelului CustomUser
        return super().get_readonly_fields(request,obj) #daca utilizatorul logat nu este un moderator atunci se apelaza implementarea implicita din clasa parinte(UserAdmin)
    
    #super() este folosit pentru a apela metode din clasa parinte, fie pentru a extinde comportamentul acestora, fie pentru a evita duplicarea codului.
    

        


@admin.register(Views)
class ViewsAdmin(admin.ModelAdmin):
    list_display=['user','product','view_date']
    
    
@admin.register(CategoryModel)
class CategoryModelAdmin(admin.ModelAdmin):
    list_display=['id','name']
    
    
@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    list_display=['id','code']
    ordering=['id']    
    
    
@admin.register(ProductSizeStock)
class ProductSizeStock(admin.ModelAdmin):
    list_display=['id','product','size','stock']
    ordering=['id']
    list_filter=['product__name','size__size']
    search_fields=['product__name']
    
    
    
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display=['id','user__id','order_date']
    ordering=['-order_date']
    
    
@admin.register(OrderProduct)
class OrderProductAdmin(admin.ModelAdmin):
    list_display=['order__id', 'product__name','quantity']
    