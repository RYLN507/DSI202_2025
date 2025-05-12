from django.urls import path
from . import views
from .views import confirm_order
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.urls import include 

urlpatterns = [
    path('', views.home, name='home'),
    path('filter/', views.filter_view, name='filter'),  # ใช้ filter_view เป็นหลัก
    # path('filter/', views.product_filter, name='product_filter'),  # ลบ path ซ้ำ
    path('filter-results/', views.product_filter, name='product_filter'),

    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Profile & Users
    path('profile/', views.profile, name='profile'),
    path('favorites/', views.favorites_view, name='favorites'),
    path('favorite/restaurant/<int:pk>/', views.toggle_favorite_restaurant, name='toggle_favorite_restaurant'),
    path('favorite/menu/<int:pk>/', views.toggle_favorite_menu, name='toggle_favorite_menu'),
    path('profile/reset_image/', views.reset_profile_image, name='reset_profile_image'),

    # Addresses
    path('addresses/', views.address_list, name='address_list'),
    path('addresses/add/', views.address_add, name='address_add'),
    path('addresses/<int:pk>/edit/', views.address_edit, name='address_edit'),          
    path('addresses/<int:pk>/delete/', views.address_delete, name='address_delete'),
    path('addresses/<int:pk>/up/', views.address_move_up, name='address_move_up'),
    path('addresses/<int:pk>/down/', views.address_move_down, name='address_move_down'),
    path('addresses/<int:pk>/set-default/', views.address_set_default, name='address_set_default'),

    # Payment Methods & Help Center
    path('payment-methods/', views.payment_methods, name='payment_methods'),
    path('help-center/', views.help_center, name='help_center'),

    # Flash Deals & Hot Menus
    path('flash/', views.flash_all, name='flash_all'),
    path('flash-menu/<int:pk>/', views.flash_menu_detail, name='flash_menu_detail'),
    path('deals/', views.deal_all, name='deal_all'),
    path('deals/<int:deal_id>/', views.deal_menu_detail, name='deal_menu_detail'),

    # Shop & Menus
    #path('shop/<str:category_name>/', views.shop_list, name='shop_list'),
    path('restaurant/<int:restaurant_id>/', views.restaurant_detail, name='restaurant_detail'),
    path('menu/<int:menu_id>/', views.menu_detail, name='menu_detail'),
    path('menu/<int:menu_id>/add/', views.add_to_cart, name='add_to_cart'),

    # Cart & Checkout
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('cart/', views.cart_view, name='cart'),
    path('checkout/', views.checkout, name='checkout'),

    path('checkout/payment/',       views.choose_payment_method,      name='choose_payment'),
    path('checkout/confirm/',       views.confirm_order,              name='checkout_confirm'),

    # ฟอร์ม POST สร้าง Order จริง → ต้องไม่ชนกับ checkout/confirm/
    path('checkout/place-order/',   views.place_order,                name='place_order'),

    # ยืนยันคำสั่งซื้อซ้ำ (นำกลับมาชำระอีกครั้ง)
    path('checkout/confirm/<int:order_id>/', views.confirm_checkout_again, name='confirm_checkout_again'),
    path('order/<int:order_id>/upload-slip/', views.upload_slip, name='upload_slip'),
    path('order-history/', views.order_history, name='order_history'),
    path('orders/<int:order_id>/order-again/', views.checkout_again, name='checkout_again'),

    # Order Success
    path('order/success/<int:order_id>/', views.order_success, name='order_success'),

    path('payment-methods/add/', views.payment_method_add, name='payment_method_add'),
    path('payment-methods/<int:pk>/edit/', views.payment_method_edit, name='payment_method_edit'),
    path('payment-methods/<int:pk>/delete/', views.payment_method_delete, name='payment_method_delete'),
    path('payment-methods/', views.payment_methods, name='payment_method_list'),
    path('checkout_again/<int:order_id>', views.checkout_again, name='checkout_again'),
    path('confirm_checkout_again/<int:order_id>', views.confirm_checkout_again, name='confirm_checkout_again'),

    # Toggle Favorite Deal
    path('deals/<int:deal_id>/toggle-favorite/', views.toggle_favorite_deal, name='toggle_favorite_deal'),
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='registration/password_change_form.html'), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'), name='password_change_done'),

    path('oauth/', include('social_django.urls', namespace='social')),

    path('community/',               views.board_list,   name='community_board'),
    path('community/create/',        views.create_post,  name='create_post'),
    path('community/post/<int:pk>/', views.post_detail,  name='post_detail'),
    path('community/post/<int:pk>/edit/',   views.edit_post,    name='edit_post'),
    path('community/post/<int:pk>/delete/', views.delete_post,  name='delete_post'),
    path('post/<int:pk>/like/', views.like_post, name='like_post'),

    path('shop/', views.shop_list, name='shop_list'),
    #path('shop/<slug:category_slug>/', views.shop_list, name='shop_list'),

    path('shop/<int:category_id>/', views.shop_list, name='shop_list'),

    path('menu-shorts/', views.menu_shorts, name='menu_shorts'),
    

]

if settings.DEBUG:
    # เสิร์ฟ MEDIA
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # เสิร์ฟ STATIC ของแอปเราด้วย
    urlpatterns += static(
        settings.STATIC_URL, 
        document_root=settings.BASE_DIR / 'myapp' / 'static'
    )
