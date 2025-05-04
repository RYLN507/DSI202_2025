# myapp/admin.py
from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import (
    Profile, Address, PaymentMethod,
    Category, Restaurant, Menu,
    Deal, FlashMenu,
    CartItem, Order, OrderItem
)

User = get_user_model()


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display        = ('user', 'default_address')
    search_fields       = ('user__username',)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display  = ('user', 'label', 'is_default')
    list_filter   = ('is_default',)
    search_fields = ('user__username', 'label', 'full_address')


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display        = ('user', 'name', 'details')
    search_fields       = ('user__username', 'name')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display        = ('display_name', 'name')
    prepopulated_fields = {'name': ('display_name',)}
    search_fields       = ('display_name',)


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display        = ('name', 'category')
    list_filter         = ('category',)
    search_fields       = ('name',)
    raw_id_fields       = ('category',)
    filter_horizontal   = ('favorites',)
    # ถ้าต้องการใช้งาน horizontal widget


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    # แสดงคอลัมน์หลักบน list view
    list_display = (
        'title',
        'restaurant',
        'restaurant_category',  # ฟิลด์ช่วยให้เห็นหมวดหมู่ด้วย
        'sold_count',
        'start_time',
        'end_time',
        'price',
        'discount_price',
    )

    # ฟิลเตอร์ข้าง ๆ
    list_filter = (
        'restaurant__category',
        'start_time',
        'end_time',
    )

    # ค้นหาได้ตามชื่อเมนู และชื่อร้าน
    search_fields = (
        'title',
        'restaurant__name',
    )

    # ถ้าเรามี many-to-many field ชื่อ favorites ให้เลือกด้วย horizontal widget
    filter_horizontal = ('favorites',)

    # ใช้ raw-id สำหรับ fk restaurant
    raw_id_fields = ('restaurant',)

    # ถ้า sold_count เป็น property/read-only field ก็ยกให้ appear ใน detail แต่ไม่แก้ไขได้
    readonly_fields = ('sold_count',)

    # ช่วยให้เห็น category บน list_display โดยไม่ต้องลงซ้ำ ๆ ใน model
    def restaurant_category(self, obj):
        return obj.restaurant.category.display_name
    restaurant_category.short_description = 'หมวดหมู่'

    # ถ้าต้องการ default ordering (เช่น เรียงตามหมวด+ชื่อเมนู)
    ordering = ('restaurant__category__name', 'title')


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display        = ('title', 'original_price', 'discounted_price', 'start_time', 'end_time', 'is_active')
    list_filter         = ('is_active',)
    search_fields       = ('title',)
    filter_horizontal = ('menus',)  # ถ้าใช้ ManyToMany


@admin.register(FlashMenu)
class FlashMenuAdmin(admin.ModelAdmin):
    list_display  = ('title', 'menu', 'original_price', 'discounted_price', 'start_time', 'end_time', 'is_active')
    list_filter   = ('is_active',)
    search_fields = ('title', 'menu__title')
    fields        = ('title', 'menu', 'image', 'original_price', 'discounted_price', 'start_time', 'end_time', 'is_active')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display        = ('user', 'menu', 'quantity')
    search_fields       = ('user__username', 'menu__title')
    raw_id_fields       = ('user', 'menu')


class OrderItemInline(admin.TabularInline):
    model               = OrderItem
    readonly_fields     = ('menu', 'quantity', 'price_at_time')
    extra               = 0
    show_change_link    = False
    can_delete          = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display        = ('id', 'user', 'address', 'total_price', 'placed_at', 'is_paid')
    list_filter         = ('is_paid', 'placed_at')
    raw_id_fields       = ('user', 'address')
    search_fields       = ('user__username', 'id')
    date_hierarchy      = 'placed_at'
    inlines             = (OrderItemInline,)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display        = ('order', 'menu', 'quantity', 'price_at_time')
    raw_id_fields       = ('order', 'menu')
    search_fields       = ('order__id', 'menu__title')