# myapp/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('filter/', views.filter_view, name='filter'),

    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Profile & Users
    path('profile/', views.profile, name='profile'),
    path('favorites/', views.favorites_view, name='favorites'),
    path('favorite/restaurant/<int:pk>/', views.toggle_favorite_restaurant, name='toggle_favorite_restaurant'),
    path('favorite/menu/<int:pk>/', views.toggle_favorite_menu, name='toggle_favorite_menu'),

    # Addresses
    path('addresses/', views.address_list, name='address_list'),
    path('addresses/add/', views.address_view, name='address_add'),
    path('addresses/<int:address_id>/delete/', views.address_delete, name='address_delete'),

    # Payment Methods & Help Center
    path('payment-methods/', views.payment_methods, name='payment_methods'),
    path('help-center/', views.help_center, name='help_center'),

    # Flash Deals & Hot Menus
    path('flash/', views.flash_all, name='flash_all'),

    # Shop & Menus
    path('shop/<str:category_name>/', views.shop_list, name='shop_list'),
    path('restaurant/<int:restaurant_id>/', views.restaurant_detail, name='restaurant_detail'),
    path('menu/<int:menu_id>/', views.menu_detail, name='menu_detail'),
    path('menu/<int:menu_id>/add/', views.add_to_cart, name='add_to_cart'),

    # Cart & Checkout
    path('cart/', views.cart_view, name='cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/confirm/', views.confirm_order, name='confirm_order'),

    # Order Success
    path('order/success/', views.order_success, name='order_success'),

    # Toggle Favorite Deal
    path('deals/<int:deal_id>/toggle-favorite/', views.toggle_favorite_deal, name='toggle_favorite_deal'),
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='registration/password_change_form.html'), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'), name='password_change_done'),

    path('order-history/', views.order_history, name='order_history'),

    path('payment-methods/add/', views.payment_method_add, name='payment_method_add'),
    path('payment-methods/<int:pk>/edit/', views.payment_method_edit, name='payment_method_edit'),
    path('payment-methods/<int:pk>/delete/', views.payment_method_delete, name='payment_method_delete'),



    
]
