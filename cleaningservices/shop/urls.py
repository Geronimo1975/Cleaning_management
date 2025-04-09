from django.urls import path
from . import views

urlpatterns = [
    path('', views.shop_home, name='shop'),
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('products/<slug:slug>/review/', views.submit_product_review, name='submit_product_review'),
    path('categories/<slug:slug>/', views.category_view, name='product_category'),
    path('affiliate/redirect/', views.track_affiliate_click, name='affiliate_redirect'),
]