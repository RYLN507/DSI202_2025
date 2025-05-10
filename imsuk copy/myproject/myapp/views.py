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
from django.views.decorators.http import require_POST
from django.utils.translation import gettext_lazy as _
from .forms  import SlipUploadForm
from django.contrib.auth import login
from .models import (
    Profile, Address, PaymentMethod,
    Category, Restaurant, Menu,
    Deal, FlashMenu, FavoriteDeal,
    CartItem, Order, OrderItem
)
from django.shortcuts import render, redirect

User = get_user_model()


def register_view(request):
    """สมัครสมาชิกใหม่ และล็อกอินอัตโนมัติ"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()               # สร้าง user ใหม่
            login(request, user)             # ล็อกอินทันที
            messages.success(
                request,
                "ยินดีต้อนรับเข้าสู่ IMSUK ค่ะ"  # ข้อความต้อนรับ
            )
            return redirect('home')          # เปลี่ยนเป็น URL name ของหน้าแรกคุณ
    else:
        form = UserCreationForm()

    return render(request, 'register.html', {'form': form})


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

from django.shortcuts import get_object_or_404, render
from .models import FlashMenu

def flash_menu_detail(request, pk):
    flash_menu = get_object_or_404(FlashMenu, pk=pk)

    # คำนวณ % ส่วนลด
    try:
        discount_pct = round(
            (flash_menu.original_price - flash_menu.discounted_price)
            / flash_menu.original_price * 100
        )
    except (TypeError, ZeroDivisionError):
        discount_pct = 0

    # แยก description เป็นลิสต์วัตถุดิบ
    ingredients = []
    if flash_menu.menu and flash_menu.menu.description:
        ingredients = [ing.strip() for ing in flash_menu.menu.description.split(',') if ing.strip()]

    context = {
        'flash_menu': flash_menu,
        'discount_pct': discount_pct,
        'ingredients': ingredients,
    }
    return render(request, 'flash_detail.html', context)


from django.utils import timezone

def deal_all(request):
    now = timezone.localtime().time()
    all_deals = Deal.objects.filter(is_active=True).order_by('start_time')
    filtered = all_deals.filter(start_time__lte=now, end_time__gte=now)

    # เตรียมข้อมูลดีบักส่งเข้า template
    debug_list = [
        {
          'title': d.title,
          'start': d.start_time.strftime("%H:%M"),
          'end':   d.end_time.strftime("%H:%M"),
        }
        for d in all_deals
    ]

    return render(request, 'deal_all.html', {
        'deals': filtered,
        'now_time': now.strftime("%H:%M"),
        'debug_list': debug_list,
    })


def deal_menu_detail(request, deal_id):
    deal_menu = get_object_or_404(Deal, id=deal_id, is_active=True)
    return render(request, 'deal_menu_detail.html', {
        'deal_menu': deal_menu,
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


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Address, Profile

@login_required
def profile(request):
    """โปรไฟล์ผู้ใช้"""
    profile = request.user.profile
    default_address = Address.objects.filter(
        user=request.user, is_default=True
    ).first()

    if request.method == 'POST':
        # ถ้ากดลบรูป
        if 'remove_image' in request.POST:
            if profile.image:
                profile.image.delete(save=False)
                profile.image = None
                profile.save()
            return redirect('profile')

        # ถ้ามีไฟล์ใหม่อัพโหลดเข้ามา
        if 'image' in request.FILES:
            profile.image = request.FILES['image']
            profile.save()
            return redirect('profile')

    return render(request, 'profile.html', {
        'default_address': default_address,
        'profile': profile,
    })


import os
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

@login_required
def reset_profile_image(request):
    if request.method == 'POST':
        profile = request.user.profile
        if profile.image:
            # full path ที่แท้จริงของรูป
            image_path = os.path.join(settings.MEDIA_ROOT, profile.image.name)

            # ลบจาก ImageField ก่อน
            profile.image.delete(save=False)

            # ลบจาก disk (ถ้ามีจริง ๆ)
            if os.path.exists(image_path):
                os.remove(image_path)

            # set เป็น None แล้ว save
            profile.image = None
            profile.save()

    return redirect('profile')



@login_required
def address_list(request):
    """รายการที่อยู่"""
    addresses = Address.objects.filter(user=request.user).order_by('order')
    return render(request, 'address_list.html', {
        'addresses': addresses
    })


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Address

@login_required
def address_view(request):
    """เพิ่ม/แก้ไขที่อยู่"""
    if request.method == 'POST':
        label         = request.POST.get('label', '').strip()
        full_address  = request.POST.get('full_address', '').strip()
        is_def        = bool(request.POST.get('is_default'))

        if is_def:
            Address.objects.filter(user=request.user).update(is_default=False)

        Address.objects.create(
            user=request.user,
            label=label,
            full_address=full_address,
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


from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from .models import Menu, CartItem

@login_required
def add_to_cart(request, menu_id):
    """เพิ่มเมนูลงตะกร้า เก็บราคาหลังลดลงใน CartItem.price_at_time"""
    menu = get_object_or_404(Menu, id=menu_id)

    # ถ้ายังไม่มีรายการนี้ในตะกร้า ให้สร้างขึ้นพร้อมราคาหลังลด ณ ปัจจุบัน
    item, created = CartItem.objects.get_or_create(
        user=request.user,
        menu=menu,
        defaults={'price_at_time': menu.discount_price}
    )

    if not created:
        # มีอยู่แล้วก็เพิ่มจำนวน
        item.quantity += 1

    # อัปเดตราคาล่าสุดเผื่อส่วนลดเปลี่ยน
    item.price_at_time = menu.discount_price
    item.save()

    return redirect('cart')

# myapp/views.py

import base64
from decimal import Decimal
from io import BytesIO

import qrcode
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import CartItem

# Replace with your actual PromptPay ID
PROMPTPAY_ID = "0982784097"

def _generate_promptpay_payload(pp_id: str, amount: Decimal) -> str:
    """
    Simplified PromptPay payload builder.
    For real production, use a library or full EMV spec.
    """
    # Format amount as string without trailing zeros, e.g. "123.45"
    amt_str = f"{amount:.2f}"
    # This is just a minimal illustration—real payload must follow EMVCo spec exactly!
    return f"00020101021127{pp_id}5303THB54{amt_str}5802TH6304XXXX"

@login_required
def cart_view(request):
    items = CartItem.objects.filter(user=request.user)
    subtotal = sum(item.menu.discount_price * item.quantity for item in items)
    delivery_fee = Decimal('29.00') if items else Decimal('0.00')
    grand_total = subtotal + delivery_fee

    # Generate QR code image if there are items
    qr_b64 = None
    if items:
        payload = _generate_promptpay_payload(PROMPTPAY_ID, grand_total)
        img = qrcode.make(payload)
        buf = BytesIO()
        img.save(buf, format='PNG')
        qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    return render(request, 'cart.html', {
        'cart_items': items,
        'subtotal': subtotal,
        'delivery_fee': delivery_fee,
        'grand_total': grand_total,
        'qr_b64': qr_b64,
    })

@login_required
def update_cart(request, item_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    print(f"Received request for item_id: {item_id}")  # ดีบัก
    try:
        data = json.loads(request.body)
        action = data.get('action')
        print(f"Received action: {action}")  # ดีบัก
    except json.JSONDecodeError:
        print("JSON Decode Error")  # ดีบัก
        return HttpResponse(status=400)
    if action == 'increase':
        item.quantity += 1
        item.save()
    elif action == 'decrease':
        if item.quantity > 1:
            item.quantity -= 1
            item.save()
    elif action == 'remove':
        item.delete()
        return HttpResponse(status=204)
    else:
        return HttpResponse(status=400)
    return render(request, 'partials/cart_item.html', {'item': item})


from decimal import Decimal
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import CartItem, Address
from .models import Order, CartItem, Address

@login_required
def checkout(request):
    pending = Order.objects.filter(
        user=request.user,
        is_paid=False,
        payment_method='promptpay',
        slip__isnull=True
    ).first()
    if pending:
        return redirect('upload_slip', order_id=pending.id)

    cart_items   = CartItem.objects.filter(user=request.user)
    total_price  = sum(i.menu.discount_price * i.quantity for i in cart_items)
    delivery_fee = Decimal('29.00') if cart_items else Decimal('0.00')
    grand_total  = total_price + delivery_fee
    default_address = Address.objects.filter(user=request.user, is_default=True).first()

    method = request.session.get('payment_method', 'visa')
    qr_image_url = None
    if method == 'promptpay':
        # put your static file under static/images/…
        qr_image_url = 'images/promptpay_sample.png'

    return render(request, 'checkout.html', {
        'cart_items':    cart_items,
        'total_price':   total_price,
        'delivery_fee':  delivery_fee,
        'grand_total':   grand_total,
        'default_address': default_address,
        'method':        method,
        'qr_image_url':  qr_image_url,
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


from decimal import Decimal
from django.shortcuts       import render, redirect, get_object_or_404
from django.urls            import reverse
from django.contrib.auth.decorators import login_required
from django.utils           import timezone

from .models import CartItem, Address, Order, OrderItem

@login_required
def place_order(request):
    # ให้รองรับเฉพาะ POST เท่านั้น
    if request.method != 'POST':
        return redirect('checkout')

    # 1) ดึงสินค้าในตะกร้า
    items = CartItem.objects.filter(user=request.user)
    if not items.exists():
        # ถ้าตะกร้าว่าง → กลับไปหน้า checkout
        return redirect('checkout')

    # 2) คำนวณยอด
    subtotal    = sum(i.menu.discount_price * i.quantity for i in items)
    delivery    = Decimal('29.00')
    grand_total = subtotal + delivery

    # 3) หาที่อยู่จัดส่งเริ่มต้น
    default_address = Address.objects.filter(
        user=request.user,
        is_default=True
    ).first()
    if default_address is None:
        # ถ้าไม่มี address → ไปหน้าเพิ่ม/เลือก address
        return redirect('address_list')

    # 4) อ่านวิธีจ่ายเงินจาก session
    method = request.session.get('payment_method', 'visa')
    is_paid = (method == 'visa')

    # 5) สร้าง Order
    order = Order.objects.create(
        user=request.user,
        address=default_address,
        total_price=subtotal,
        delivery_fee=delivery,
        grand_total=grand_total,
        placed_at=timezone.now(),
        is_paid=is_paid,
        payment_method=method,
    )

    # 6) สร้าง OrderItem แต่ละตัว
    for ci in items:
        OrderItem.objects.create(
            order=order,
            menu=ci.menu,
            quantity=ci.quantity,
            price_at_time=ci.price_at_time,

        )

    # 7) ล้างตะกร้า
    items.delete()

    # 8) Redirect ตามวิธีจ่ายเงิน
    if method == 'promptpay':
        # ยังต้องอัปโหลดสลิปก่อนยืนยันการชำระ
        return redirect('upload_slip', order_id=order.id)
    else:
        # จ่ายด้วย VISA (ถือว่าเรียบร้อย)
        return redirect('order_success', order_id=order.id)


    # 3) Create OrderItems
    for ci in items:
        OrderItem.objects.create(
            order=order,
            menu=ci.menu,
            quantity=ci.quantity,
            unit_price=ci.menu.discount_price
        )

    # 4) Clear cart
    items.delete()

    # 5) Redirect to the slip-upload page
    return redirect('upload_slip', order_id=order.id)

from django.shortcuts           import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Order
from .forms  import SlipUploadForm

@login_required
def upload_slip(request, order_id):
    # ดึงออร์เดอร์ที่ยังไม่ถูกจ่ายของ user
    order = get_object_or_404(Order, pk=order_id, user=request.user)

    if request.method == 'POST':
        # bind form กับ order instance
        form = SlipUploadForm(request.POST, request.FILES, instance=order)
        if form.is_valid():
            # บันทึกไฟล์ slip เข้า order.slip
            form.save()
            # mark ว่าจ่ายแล้ว
            order.is_paid = True
            order.save()
            # กลับมาแสดงหน้า upload อีกครั้งเพื่อ preview
            return redirect('upload_slip', order_id=order.id)
    else:
        # GET ก็ bind form ด้วย instance เหมือนกัน เผื่อมี slip เดิมๆ
        form = SlipUploadForm(instance=order)

    return render(request, 'upload_slip.html', {
        'order': order,
        'form':  form,
    })



@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'order_success.html', {
        'order': order
    })


# myapp/views.py
from decimal import Decimal
from django.shortcuts import render
from .models import Order

def order_history(request):
    orders = (
        Order.objects
        .filter(user=request.user)
        .prefetch_related('items__menu')
    )
    orders_data = []

    for order in orders:
        # subtotal คำนวณจาก price_at_time เสมอ
        subtotal = sum(
            item.price_at_time * item.quantity
            for item in order.items.all()
        )

        # ค่าส่งจากฟิลด์ delivery_fee
        shipping = order.delivery_fee

        # grand total = subtotal + shipping
        grand_total = subtotal + shipping

        orders_data.append({
            'order': order,
            'subtotal': subtotal,
            'shipping': shipping,
            'grand_total': grand_total,
        })

    return render(request, 'order_history.html', {
        'orders_data': orders_data,
    })





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
    # รับค่าจาก GET parameters
    category_list = request.GET.getlist('category')  # รับได้หลายหมวดหมู่
    price = request.GET.get('price')

    products = Menu.objects.all()

    # กรองหมวดหมู่ (หลายหมวด)
    if category_list:
        products = products.filter(restaurant__category__name__in=category_list)

    # กรองราคาสินค้า
    if price == '0':
        products = products.filter(discount_price__lte=100)
    elif price == '1':
        products = products.filter(discount_price__gt=100, discount_price__lte=500)
    elif price == '2':
        products = products.filter(discount_price__gt=500)

    # ตัวกรองแพ้อาหาร
    if request.GET.get('no_milk') == '1':
        products = products.exclude(description__icontains='นม')
    if request.GET.get('no_egg') == '1':
        products = products.exclude(description__icontains='ไข่')
    if request.GET.get('no_peanut') == '1':
        products = products.exclude(description__icontains='ถั่ว')
    if request.GET.get('no_gluten') == '1':
        products = products.exclude(description__icontains='กลูเตน')
    if request.GET.get('no_seafood') == '1':
        products = products.exclude(description__icontains='ทะเล')
    if request.GET.get('no_fish') == '1':
        products = products.exclude(description__icontains='ปลา')

    return render(request, 'filtered_products.html', {'products': products})


from decimal import Decimal
from django.shortcuts      import render, redirect, get_object_or_404
from django.utils          import timezone
from django.contrib.auth.decorators import login_required

from .models import Order, OrderItem, Address

@login_required
def checkout_again(request, order_id):
    pending = Order.objects.filter(
        user=request.user,
        is_paid=False,
        payment_method='promptpay',
        slip__isnull=True
    ).first()
    if pending:
        return redirect('upload_slip', order_id=pending.id)

    # ดึงออร์เดอร์เดิม
    old_order = get_object_or_404(Order, id=order_id, user=request.user)

    # ค่าจัดส่งตายตัว
    delivery_fee = Decimal('29.00')

    # คำนวณ subtotal จากราคาหลังลดในเมนูเดิม
    subtotal = sum(
        item.menu.discount_price * item.quantity
        for item in old_order.items.all()
    )
    # คำนวณยอดสุทธิ
    grand_total = subtotal + delivery_fee

    if request.method == 'POST':
        # รับ address ที่ผู้ใช้เลือกจากฟอร์ม
        address_id = request.POST.get('address_id')
        address    = get_object_or_404(Address, id=address_id, user=request.user)

        # สร้าง Order ใหม่ (ยังไม่ชำระเงิน)
        new_order = Order.objects.create(
            user        = request.user,
            address     = address,
            total_price = subtotal,      # เฉพาะสินค้า
            delivery_fee= delivery_fee,  # ค่าส่ง
            grand_total = grand_total,   # สินค้า+ส่ง
            placed_at   = timezone.now(),
            is_paid     = False,
        )

        # คัดลอกรายการสินค้าเดิม
        for item in old_order.items.all():
            OrderItem.objects.create(
                order         = new_order,
                menu          = item.menu,
                quantity      = item.quantity,
                price_at_time = item.menu.discount_price,
            )

        # ไปหน้าชำระเงินปกติของ Order ใหม่
        return redirect('checkout', order_id=new_order.id)

    # GET — แสดงฟอร์มยืนยันการสั่งอีกครั้ง
    default_address = Address.objects.filter(user=request.user, is_default=True).first()
    return render(request, 'checkout_again.html', {
        'old_order':      old_order,
        'subtotal':       subtotal,
        'delivery_fee':   delivery_fee,
        'grand_total':    grand_total,
        'default_address': default_address,
    })



# myapp/views.py
from decimal import Decimal
from django.shortcuts      import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http    import require_POST
from django.utils import timezone
from django.contrib import messages

from .models import Order, OrderItem, Address

@require_POST
@login_required
def confirm_checkout_again(request, order_id):
    pending = Order.objects.filter(
        user=request.user,
        is_paid=False,
        payment_method='promptpay',
        slip__isnull=True
    ).first()
    if pending:
        return redirect('upload_slip', order_id=pending.id)
    
    old_order   = get_object_or_404(Order, id=order_id, user=request.user)

    # ดึงค่าจากฟอร์ม
    address_id  = request.POST.get('address_id')
    wants_spoon = 'wants_spoon' in request.POST
    wants_sauce = 'wants_sauce' in request.POST

    address = get_object_or_404(Address, id=address_id, user=request.user)

    # คำนวณราคารวมสินค้าจาก OrderItem ของออร์เดอร์เก่า
    total_price = sum(item.quantity * item.price_at_time for item in old_order.items.all())

    # กำหนดค่าจัดส่ง
    delivery_fee = Decimal('29.00') if total_price > 0 else Decimal('0.00')
    grand_total  = total_price + delivery_fee

    # สร้างออร์เดอร์ใหม่ พร้อมฟิลด์ที่เพิ่งเพิ่ม
    new_order = Order.objects.create(
        user         = request.user,
        address      = address,
        total_price  = total_price,
        delivery_fee = delivery_fee,
        grand_total  = grand_total,
        placed_at    = timezone.now(),
        is_paid      = True,
        wants_spoon  = wants_spoon,
        wants_sauce  = wants_sauce,
    )

    # คัดลอกรายการสินค้า
    for item in old_order.items.all():
        OrderItem.objects.create(
            order         = new_order,
            menu          = item.menu,
            quantity      = item.quantity,
            price_at_time = item.price_at_time,
        )

    messages.success(request, "สั่งซื้ออีกครั้งสำเร็จ! ระบบได้บันทึกคำสั่งซื้อของคุณแล้ว")
    return redirect('order_history')



# myapp/views.py
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from .models import Address

@login_required
def address_move_up(request, pk):
    address = get_object_or_404(Address, id=pk, user=request.user)
    above = (
        Address.objects
        .filter(user=request.user, order__lt=address.order)
        .order_by('-order')
        .first()
    )
    if above:
        with transaction.atomic():
            address.order, above.order = above.order, address.order
            address.save()
            above.save()
    return redirect('address_list')


@login_required
def address_move_down(request, pk):
    address = get_object_or_404(Address, id=pk, user=request.user)
    below = (
        Address.objects
        .filter(user=request.user, order__gt=address.order)
        .order_by('order')
        .first()
    )
    if below:
        with transaction.atomic():
            address.order, below.order = below.order, address.order
            address.save()
            below.save()
    return redirect('address_list')


@login_required
def reset_address_order(request):
    addresses = Address.objects.filter(user=request.user).order_by('id')
    for idx, a in enumerate(addresses):
        a.order = idx
        a.save()
    messages.success(request, "เรียงลำดับใหม่แล้วเรียบร้อย")
    return redirect('address_list')

from django.shortcuts import render, get_object_or_404, redirect
from .models import Address
from .forms import AddressForm

def address_edit(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            return redirect('address_list')
    else:
        form = AddressForm(instance=address)
    return render(request, 'address_form.html', {
        'form': form,
        'title': _('Edit Address'),
    })

@login_required
def address_add(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            # set default ordering (append to end)
            last = Address.objects.filter(user=request.user).order_by('-order').first()
            address.order = last.order + 1 if last else 0
            address.save()
            return redirect('address_list')
    else:
        form = AddressForm()
    return render(request, 'address_form.html', {
        'form': form,
        'title': _('Add Address')
    })

@login_required
def address_move_up(request, pk):
    addr = get_object_or_404(Address, pk=pk, user=request.user)
    prev = Address.objects.filter(
        user=request.user, order__lt=addr.order
    ).order_by('-order').first()
    if prev:
        addr.order, prev.order = prev.order, addr.order
        addr.save(); prev.save()
    return redirect('address_list')

@login_required
def address_move_down(request, pk):
    addr = get_object_or_404(Address, pk=pk, user=request.user)
    nxt = Address.objects.filter(
        user=request.user, order__gt=addr.order
    ).order_by('order').first()
    if nxt:
        addr.order, nxt.order = nxt.order, addr.order
        addr.save(); nxt.save()
    return redirect('address_list')


from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required

@login_required
def choose_payment_method(request):
    next_url = request.GET.get('next', reverse('checkout'))
    if request.method == 'POST':
        method = request.POST.get('payment_method')
        if method in ('visa', 'promptpay'):
            request.session['payment_method'] = method
        return redirect(next_url)
    return render(request, 'choose_payment.html', {'next': next_url})


from django.shortcuts           import render, redirect
from django.urls                import reverse
from django.contrib.auth.decorators import login_required

@login_required
def choose_payment_method(request):
    """
    Show the “choose Visa / PromptPay” page, then save the choice and
    redirect straight into our final confirm_checkout view.
    """
    # Where to go once they've chosen?
    next_url = request.GET.get('next') or reverse('confirm_checkout')

    if request.method == 'POST':
        method = request.POST.get('payment_method')
        if method in ('visa', 'promptpay'):
            request.session['payment_method'] = method
        return redirect(next_url)

    return render(request, 'choose_payment.html', {
        'next': next_url
    })


# myapp/views.py (continuing)
import qrcode, io, base64

@login_required
def confirm_checkout(request):
    # read back the method
    method = request.session.get('payment_method', 'visa')
    items = CartItem.objects.filter(user=request.user)
    subtotal    = sum(i.menu.discount_price * i.quantity for i in items)
    delivery    = Decimal('29.00') if items else Decimal('0.00')
    grand_total = subtotal + delivery

    qr_b64 = None
    if method == 'promptpay':
        data = "0982784097"  # your real PromptPay payload here
        img = qrcode.make(data)
        buf = io.BytesIO(); img.save(buf, format='PNG')
        qr_b64 = base64.b64encode(buf.getvalue()).decode()

    return render(request, 'confirm_checkout.html', {
      'cart_items':  items,
      'total_price': subtotal,
      'delivery_fee': delivery,
      'grand_total': grand_total,
      'method':       method,
      'qr_b64':       qr_b64,
    })


