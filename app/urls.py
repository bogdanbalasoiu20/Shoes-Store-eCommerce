from django.urls import path
from . import views
from django.contrib.sitemaps.views import sitemap
from .sitemaps import OfferSitemap,ProductSitemap,StaticViewSitemap

sitemaps={
    'offers':OfferSitemap,
    'products':ProductSitemap,
    'static': StaticViewSitemap
}

urlpatterns = [
    path("test/", views.test, name="test"),
    path("products/",views.product_list,name="product_list"),
    path("contact/",views.contact,name="contact"),
    path("products/add/",views.create_product,name="create_product"),
    path("createuser/",views.create_user,name="create_user"),
    path("login/",views.custom_login,name='login'),
    path("logout/",views.custom_logout,name='logout'),
    path("profile/",views.profile,name="profile"),
    path("changepassword/",views.change_password,name="change_password"),
    path("email-confirmation/<str:code>/",views.email_confirmation,name='email_confirmation'),
    path('products/<int:product_id>/',views.product_detail,name="product_detail"),
    path('promotions/',views.create_promotion,name='create_promotion'),
    path('403/',views.view_403,name="error403"),
    path('grant_offer_permission/',views.grant_offer_permission,name='grant_offer_permission'),
    path('offer_page/',views.offer_page,name='offer_page'),
    path('offers/',views.all_offers,name='offers'),
    path('offer/<int:id>/',views.offer_detail,name='offer_detail'),
    path('sitemap.xml',sitemap,{'sitemaps':sitemaps},name='django.contrib.sitemaps.views.sitemap'),
    path('cart/',views.virtual_cart,name='virtual_cart'),
    path('order_sent/',views.order_sent,name='order_sent'),
    path('confirmation_order_sent/<int:order_id>/', views.confirmation_order_sent, name='confirmation_order_sent')

    
]
