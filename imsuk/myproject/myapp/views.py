# myapp/views.py
from django.shortcuts import (
    render, redirect, get_object_or_404
)
from django.utils import timezone
from django.http import HttpResponse
from django.contrib.auth import (
    authenticate, login, logout, get_user_model
)
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.timezone import now
from django.contrib.auth.forms import UserCreationForm

from .models import (
    Profile, Address, PaymentMethod,
    Category, Restaurant, Menu,
    Deal, FlashMenu, FavoriteDeal,
    CartItem, Order, OrderItem
)

User = get_user_model()


def register_view(request):
    """สมัครสมาชิกใหม่"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "สมัครสมาชิกสำเร็จ กรุณาเข้าสู่ระบบ"
            )
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(
        request, 'register.html', {'form': form}
    )


def filter_view(request):
    """ค้นหาเมนู (filter.html)"""
    q = request.GET.get('q', '').strip()
    results = (
        Menu.objects.filter(title__icontains=q)
        if q else []
    )
    return render(request, 'filter.html', {
        'query': q,
        'results': results,
    })

def filter_view(request):
    allergy_list = ['ถั่ว', 'นม', 'ไข่', 'อาหารทะเล', 'กลูเตน']
    categories = Category.objects.all()
    return render(request, 'filter.html', {
        'categories': categories,
        'allergy_list': allergy_list,
    })



def address_delete(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    if request.method == 'POST':
        address.delete()
    return redirect('address_list')



def home(request):
    now_aware = timezone.now()
    now_local = timezone.localtime(now_aware)
    now_naive = now_local.replace(tzinfo=None)

    deals = Deal.objects.filter(
        is_active=True,
        start_time__lte=now_naive,
        end_time__gte=now_naive,
    ).order_by('start_time')[:5]

    current_time = now_local.time()
    flash_menus = FlashMenu.objects.filter(
        is_active=True,
        start_time__lte=current_time,
        end_time__gte=current_time,
    ).order_by('start_time')[:10]

    categories = Category.objects.all()

    query = request.GET.get('q', '')
    sort = request.GET.get('sort')

    menus = Menu.objects.all()
    restaurants = Restaurant.objects.all()

    if query:
        menus = menus.filter(title__icontains=query)
        restaurants = restaurants.filter(name__icontains=query)

    if sort == 'price_low':
        menus = menus.order_by('discount_price')
    elif sort == 'price_high':
        menus = menus.order_by('-discount_price')
    elif sort == 'discount_high':
        discount_amount = ExpressionWrapper(F('price') - F('discount_price'), output_field=DecimalField())
        menus = menus.annotate(discount_amount=discount_amount).order_by('-discount_amount')

    return render(request, 'home.html', {
        'deals': deals,
        'flash_menus': flash_menus,
        'categories': categories,
        'menus': menus,
        'restaurants': restaurants,
        'query': query,
    })

def search_suggestions(request):
    q = request.GET.get('q', '')
    if q:
        menus = list(Menu.objects.filter(title__icontains=q).values('id', 'title')[:5])
        restaurants = list(Restaurant.objects.filter(name__icontains=q).values('id', 'name')[:5])
        return JsonResponse({'menus': menus, 'restaurants': restaurants})
    return JsonResponse({'menus': [], 'restaurants': []})



def flash_all(request):
    """เมนูนาทีทองทั้งหมด"""
    current_time = now().time()
    flash_menus = FlashMenu.objects.filter(
        is_active=True,
        start_time__lte=current_time,
        end_time__gte=current_time
    )
    return render(request, 'flash_all.html', {
        'flash_menus': flash_menus,
    })


def login_view(request):
    """เข้าสู่ระบบ"""
    if request.method == 'POST':
        email    = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(
            request, username=email, password=password
        )
        if user:
            login(request, user)
            return redirect('home')
        messages.error(
            request, "อีเมลหรือรหัสผ่านไม่ถูกต้อง"
        )
    return render(request, 'login.html')


def logout_view(request):
    """ออกจากระบบ"""
    logout(request)
    return redirect('login')


@login_required
def profile(request):
    """โปรไฟล์ผู้ใช้"""
    default_address = Address.objects.filter(user=request.user, is_default=True).first()
    return render(request, 'profile.html', {
        'default_address': default_address
    })


@login_required
def address_list(request):
    """รายการที่อยู่"""
    addresses = Address.objects.filter(
        user=request.user
    )
    return render(request, 'address_list.html', {
        'addresses': addresses
    })


@login_required
def address_view(request):
    """เพิ่ม/แก้ไขที่อยู่"""
    if request.method == 'POST':
        text   = request.POST.get('text', '').strip()
        is_def = bool(request.POST.get('is_default'))
        if is_def:
            # เคลียร์ default เดิม
            Address.objects.filter(
                user=request.user
            ).update(is_default=False)
        Address.objects.create(
            user=request.user,
            text=text,
            is_default=is_def
        )
        return redirect('address_list')
    return render(request, 'address.html')


@login_required
def payment_methods(request):
    """วิธีชำระเงิน"""
    methods = request.user.payment_methods.all()
    return render(request, 'payment_methods.html', {
        'methods': methods
    })


def help_center(request):
    """ศูนย์ช่วยเหลือ"""
    return render(request, 'help_center.html')


@login_required
def toggle_favorite_restaurant(request, pk):
    """Toggle ร้านโปรด"""
    rest = get_object_or_404(Restaurant, pk=pk)
    user = request.user
    if user in rest.favorites.all():
        rest.favorites.remove(user)
        messages.info(
            request,
            f"ลบ {rest.name} ออกจากร้านโปรดแล้ว"
        )
    else:
        rest.favorites.add(user)
        messages.success(
            request,
            f"เพิ่ม {rest.name} เป็นร้านโปรดแล้ว"
        )
    return redirect('favorites')


@login_required
def toggle_favorite_menu(request, pk):
    """Toggle เมนูโปรด"""
    item = get_object_or_404(Menu, pk=pk)
    user = request.user
    if user in item.favorites.all():
        item.favorites.remove(user)
        messages.info(
            request,
            f"ลบ {item.title} ออกจากเมนูโปรดแล้ว"
        )
    else:
        item.favorites.add(user)
        messages.success(
            request,
            f"เพิ่ม {item.title} เป็นเมนูโปรดแล้ว"
        )
    return redirect('favorites')


@login_required
def toggle_favorite_deal(request, deal_id):
    """Toggle ดีลโปรด (HTMX)"""
    if request.method == 'POST':
        deal = get_object_or_404(Deal, id=deal_id)
        user = request.user
        fav  = FavoriteDeal.objects.filter(
            user=user, deal=deal
        ).first()
        if fav:
            fav.delete()
            messages.info(
                request,
                f"ลบ {deal.title} ออกจากดีลโปรดแล้ว"
            )
        else:
            FavoriteDeal.objects.create(
                user=user, deal=deal
            )
            messages.success(
                request,
                f"เพิ่ม {deal.title} เป็นดีลโปรดแล้ว"
            )
        return HttpResponse(status=200)
    return HttpResponse(status=405)


@login_required
def favorites_view(request):
    """ร้านโปรด, เมนูโปรด, ดีลโปรด"""
    fav_rests = request.user.favorite_restaurants.all()
    fav_menus = request.user.favorite_menus.all()
    fav_deals = FavoriteDeal.objects.filter(
        user=request.user
    ).select_related('deal')
    return render(request, 'favorites.html', {
        'favorite_restaurants': fav_rests,
        'favorite_menus'      : fav_menus,
        'favorite_deals'      : fav_deals,
    })


def shop_list(request, category_name):
    category = get_object_or_404(Category, name=category_name)
    menus = Menu.objects.filter(restaurant__category=category)
    return render(request, 'shop_list.html', {
        'category': category,
        'menus': menus,
    })



def restaurant_detail(request, restaurant_id):
    """รายละเอียดร้าน"""
    restaurant = get_object_or_404(
        Restaurant, id=restaurant_id
    )
    menus = restaurant.menus.all()
    return render(request, 'restaurant_detail.html', {
        'restaurant': restaurant,
        'menus'     : menus
    })


def menu_detail(request, menu_id):
    menu = get_object_or_404(Menu, pk=menu_id)
    return render(request, 'shop_detail.html', {
        'menu': menu
    })


@login_required
def add_to_cart(request, menu_id):
    """เพิ่มเมนูลงตะกร้า"""
    menu = get_object_or_404(Menu, id=menu_id)
    item, created = CartItem.objects.get_or_create(
        user=request.user,
        menu=menu
    )
    if not created:
        item.quantity += 1
        item.save()
    return redirect('cart')


@login_required
def cart_view(request):
    """ดูตะกร้า"""
    items = CartItem.objects.filter(user=request.user)
    total = sum(i.menu.price * i.quantity for i in items)
    shipping = 29
    return render(request, 'cart.html', {
        'cart_items'    : items,
        'total_price'   : total,
        'shipping_cost' : shipping
    })


@login_required
def update_cart(request, item_id):
    """ปรับจำนวนในตะกร้า (HTMX)"""
    item   = get_object_or_404(
        CartItem, id=item_id, user=request.user
    )
    action = request.POST.get('action')
    if action == 'increase':
        item.quantity += 1
    elif action == 'decrease' and item.quantity > 1:
        item.quantity -= 1
    item.save()
    return render(
        request, 'partials/cart_item.html', {'item': item}
    )


@login_required
def checkout(request):
    """เช็คเอาท์"""
    items    = CartItem.objects.filter(user=request.user)
    total    = sum(i.menu.price * i.quantity for i in items)
    shipping = 29
    return render(request, 'checkout.html', {
        'cart_items'    : items,
        'total_price'   : total,
        'shipping_cost' : shipping
    })


@login_required
def confirm_order(request):
    """ยืนยันสั่งซื้อ"""
    if request.method != 'POST':
        return redirect('checkout')

    items = CartItem.objects.filter(user=request.user)
    if not items.exists():
        messages.error(request, "ไม่มีสินค้าในตะกร้า")
        return redirect('cart')

    address = Address.objects.filter(
        user=request.user, is_default=True
    ).first()
    if not address:
        messages.error(
            request, "กรุณาเพิ่มที่อยู่ก่อนสั่งซื้อ"
        )
        return redirect('address_list')

    order = Order.objects.create(
        user        = request.user,
        address     = address,
        total_price = sum(i.menu.price * i.quantity for i in items),
        placed_at   = now(),
        is_paid     = True
    )
    for i in items:
        OrderItem.objects.create(
            order         = order,
            menu          = i.menu,
            quantity      = i.quantity,
            price_at_time = i.menu.price
        )
    items.delete()
    return redirect('order_success')


@login_required
def order_success(request):
    """หน้าสั่งซื้อสำเร็จ"""
    return render(request, 'order_success.html')


@login_required
def order_history(request):
    orders = request.user.orders.all().order_by('-placed_at')  # เรียงล่าสุดก่อน
    return render(request, 'order_history.html', {'orders': orders})

@login_required
def payment_method_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        details = request.POST.get('details')
        PaymentMethod.objects.create(
            user=request.user,
            name=name,
            details=details
        )
        return redirect('payment_method_list')  # หรือ path ที่แสดงรายการ
    return render(request, 'payment_method_add.html')

from django.shortcuts import get_object_or_404

@login_required
def payment_method_edit(request, pk):
    method = get_object_or_404(PaymentMethod, pk=pk, user=request.user)

    if request.method == "POST":
        # สมมติว่ามีฟอร์มแก้ไข
        method.name = request.POST.get('name')
        method.details = request.POST.get('details')
        method.save()
        return redirect('payment_methods')

    return render(request, 'payment_method_edit.html', {'method': method})

from django.shortcuts import get_object_or_404

@login_required
def payment_method_delete(request, pk):
    method = get_object_or_404(PaymentMethod, pk=pk, user=request.user)
    
    if request.method == "POST":
        method.delete()
        return redirect('payment_methods')

    return render(request, 'payment_method_delete_confirm.html', {'method': method})

@login_required
def payment_method_edit(request, pk):
    method = get_object_or_404(PaymentMethod, pk=pk, user=request.user)
    
    if request.method == "POST":
        method.name = request.POST.get('name')
        method.details = request.POST.get('details')
        method.save()
        return render(request, 'payment_method_edit.html', {'method': method, 'success': True})
    
    return render(request, 'payment_method_edit.html', {'method': method, 'success': False})

@login_required
def payment_method_delete(request, pk):
    method = get_object_or_404(PaymentMethod, pk=pk, user=request.user)

    if request.method == "POST":
        method.delete()
        return redirect('payment_methods')
    
    return render(request, 'payment_method_delete_confirm.html', {'method': method})


def address_set_default(request, address_id):
    if request.method == 'POST':
        address = get_object_or_404(Address, id=address_id, user=request.user)
        
        # ลบ default เดิมทั้งหมดก่อน
        Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
        
        # ตั้ง default ใหม่
        address.is_default = True
        address.save()

    return redirect('address_list')  # หรือชื่อ view ที่คุณแสดงรายการที่อยู่

def product_filter(request):
    """กรองสินค้า ตามหมวดหมู่ ราคา และตัวกรองแพ้อาหาร"""
    category = request.GET.get('category')
    price = request.GET.get('price')

    products = Menu.objects.all()

    # หมวดหมู่
    if category and category != '0':
        products = products.filter(restaurant__category__id=category)

    # ช่วงราคา
    if price:
        if price == '0':
            products = products.filter(price__lte=100)
        elif price == '1':
            products = products.filter(price__gt=100, price__lte=500)
        elif price == '2':
            products = products.filter(price__gt=500)

    # แพ้อาหาร (ตัวอย่าง)
    if request.GET.get('no_milk') == '1':
        products = products.exclude(description__icontains='นม')
    if request.GET.get('no_egg') == '1':
        products = products.exclude(description__icontains='ไข่')
    if request.GET.get('no_peanut') == '1':
        products = products.exclude(description__icontains='ถั่ว')

    context = {
        'products': products,
    }

    return render(request, 'filtered_products.html', context)