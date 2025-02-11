from app.models import Product, Size, ProductSizeStock
import random

# Adaugă stocul 0 pentru fiecare combinație de produs și mărime
for product in Product.objects.all():
    for size in Size.objects.all():
        ProductSizeStock.objects.get_or_create(product=product, size=size, stock=random.randint(0,50))

print("Stock for all products and sizes has been set to random number between 0 and 50.")
