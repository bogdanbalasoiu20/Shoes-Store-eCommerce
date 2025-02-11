#Un sitemap este un fișier care listează toate paginile importante ale unui site web, oferind motoarelor de căutare (precum Google, Bing) o structură clară a site-ului. Rolul său principal este de a ajuta aceste motoare să descopere și să indexeze eficient paginile, ceea ce poate îmbunătăți SEO-ul site-ului.

from django.contrib.sitemaps import Sitemap
from .models import Product,Offer
from django.urls import reverse
from django.utils.timezone import now


class ProductSitemap(Sitemap):
    changefreq='monthly'  #paginile asociate produselor sunt actualizate lunar
    priority=1   #paginile asociate produselor au prioritate 1(maxima) pentru site
    
    def items(self):
        return Product.objects.all()  #returnez toate produsele mele, fiecare cu o intrare in sitemap
    
    def location(self,item):
        return reverse('product_detail',args=[item.id])  #se genereaza url-ul asociat fiecarui produs. Argumentul item.id este utilizat pentru a construi URL-ul specific fiecărui produs.
    
    

class OfferSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return [offer for offer in Offer.objects.all() if offer.is_currently_active()] 

    def lastmod(self, obj):
        return obj.end_date  #lastmod(self, obj): Indică ultima modificare a unei oferte, care este asociată cu data de încheiere a acesteia (obj.end_date).
    
 
   
class StaticViewSitemap(Sitemap):  #sitemap pentru paginile statice
    priority = 0.8
    changefreq = 'monthly'

    def items(self):
        return ['product_list','contact']     #Returnează o listă de view-uri statice (product_list, contact), care sunt definite în urls.py.

    def location(self, item):
        return reverse(item)  