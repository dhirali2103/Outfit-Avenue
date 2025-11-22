from django.contrib import admin
from django.urls import path,include
from.import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns=[
    path('', views.index, name='shopHome'),
    path('search/', views.search, name='Search'),
    path("products/<int:myid>", views.productView, name="ProductView"),
    path('mencat/', views.mencat, name='MensCategory'),
    path('womencat/', views.womencat, name='WomensCategory'),
    path('kidscat/', views.kidscat, name='KidsCategory'),
    path('cart/', views.cart, name='Cart'),
    path('checkout/', views.checkout, name='Checkout'),
    path('upi-payment-success/', views.upi_payment_success, name='UPIPaymentSuccess'),
    path('card-payment-success/', views.card_payment_success, name='CardPaymentSuccess'),
    path('order-success/', views.order_success, name='OrderSuccess'),
    path('tracker/', views.tracker, name='TrackingStatus'),
    path('about/', views.about, name='AboutUs'),
    path('contact/', views.contact, name='ContactUs'),
    path('login/', views.login, name='Login'),
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)