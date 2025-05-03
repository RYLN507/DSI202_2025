# myapp/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db.models import Sum

User = settings.AUTH_USER_MODEL

class Profile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile'
    )
    default_address = models.CharField("ที่อยู่เริ่มต้น", max_length=255, blank=True, default='')

    def __str__(self):
        return f"Profile ของ {self.user.username}"

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()

class Address(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    label = models.CharField("ชื่อที่อยู่", max_length=100, default='', blank=True)
    full_address = models.TextField("ที่อยู่", default='')
    subdistrict = models.CharField("ตำบล", max_length=100, blank=True)
    district    = models.CharField("อำเภอ", max_length=100, blank=True)
    province    = models.CharField("จังหวัด", max_length=100, blank=True)
    zipcode     = models.CharField("รหัสไปรษณีย์", max_length=10, blank=True)
    is_default  = models.BooleanField("ตั้งเป็นค่ามาตรฐาน", default=False)

    def __str__(self):
        return f"{self.user.username} — {self.label or self.full_address[:30]}"

class PaymentMethod(models.Model):
    user    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    name    = models.CharField("ชื่อบัตร/บัญชี", max_length=50)
    details = models.CharField("รายละเอียด", max_length=255)

    def __str__(self):
        return f"{self.user.username} — {self.name}"

class Category(models.Model):
    name         = models.SlugField("รหัสหมวด", max_length=50, unique=True)
    display_name = models.CharField("ชื่อหมวด", max_length=100)
    image        = models.ImageField("รูปหมวด", upload_to='categories/', blank=True)

    class Meta:
        verbose_name        = "หมวดหมู่อาหาร"
        verbose_name_plural = "หมวดหมู่อาหาร"

    def __str__(self):
        return self.display_name

class Restaurant(models.Model):
    name       = models.CharField("ชื่อร้าน", max_length=100)
    category   = models.ForeignKey(Category, on_delete=models.SET_NULL,
                                   null=True, related_name='restaurants')
    image      = models.ImageField("รูปภาพร้าน", upload_to='restaurants/', blank=True)
    description= models.TextField("คำอธิบาย", blank=True)
    favorites  = models.ManyToManyField(User,
                       blank=True,
                       related_name='favorite_restaurants',
                       verbose_name="ผู้ที่ชื่นชอบ")

    class Meta:
        verbose_name        = "ร้านอาหาร"
        verbose_name_plural = "ร้านอาหาร"

    def __str__(self):
        return self.name


class Menu(models.Model):
    restaurant      = models.ForeignKey(
        'Restaurant',
        on_delete=models.CASCADE,
        related_name='menus',
        verbose_name='ร้านอาหาร'
    )
    title           = models.CharField("ชื่อเมนู", max_length=100)
    image           = models.ImageField("รูปเมนู", upload_to='menus/', blank=True)
    description     = models.TextField("คำอธิบายสั้น", blank=True)
    details         = models.TextField("รายละเอียดเพิ่มเติม", blank=True)
    price           = models.DecimalField("ราคาปกติ", max_digits=8, decimal_places=2)
    discount_price = models.DecimalField(
    "ราคาหลังลด", max_digits=8, decimal_places=2,
    default=0.0,
    help_text="ถ้าไม่ลด ก็ใส่เท่ากับราคาปกติ"
    
    )
    start_time      = models.TimeField(
        "เวลาเริ่มขาย", default=timezone.now,
        help_text="เช่น 10:00:00"
    )
    end_time        = models.TimeField(
        "เวลาปิดขาย", default=timezone.now,
        help_text="เช่น 22:00:00"
    )
    favorites       = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='favorite_menus',
        verbose_name="ผู้ที่ชื่นชอบ"
    )

    class Meta:
        verbose_name        = "เมนู"
        verbose_name_plural = "เมนู"

    def __str__(self):
        return self.title

    @property
    def sold_count(self):
        """
        สมมติว่าคุณมี OrderItem model ที่มี
        ForeignKey ไปที่ Menu และ field ชื่อ 'quantity'
        """
        result = self.orderitem_set.aggregate(total=Sum('quantity'))['total']
        return result or 0
    sold_count.fget.short_description = "ขายแล้ว"

    def is_available(self, now=None):
        """
        ตรวจว่าเมนูนี้สามารถสั่งได้ในเวลาปัจจุบันหรือไม่
        """
        now = now or timezone.localtime().time()
        return self.start_time <= now <= self.end_time

    def __str__(self):
        return f"{self.title} ({self.restaurant.name})"
    


class Deal(models.Model):
    """ ดีลอาหารมื้อเย็น """
    title            = models.CharField("ชื่อดีล", max_length=100)
    image            = models.ImageField("รูปดีล", upload_to='deals/')
    original_price   = models.DecimalField("ราคาต้นฉบับ", max_digits=8, decimal_places=2)
    discounted_price = models.DecimalField("ราคาหลังลด",   max_digits=8, decimal_places=2)
    start_time       = models.TimeField("เริ่ม (HH:MM)", default=timezone.now)  # <-- ใช้ TimeField
    end_time         = models.TimeField("จบ (HH:MM)",   default=timezone.now)
    is_active        = models.BooleanField("เปิดใช้งาน", default=True)

    menus = models.ManyToManyField(Menu, blank=True)

    class Meta:
        verbose_name        = "ดีล (มื้อเย็น)"
        verbose_name_plural = "ดีล (มื้อเย็น)"

    def __str__(self):
        return self.title

# เพิ่มโมเดล FavoriteDeal
class FavoriteDeal(models.Model):
    """ รายการโปรดสำหรับดีล """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_deals')
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField("เพิ่มเมื่อ", default=timezone.now)

    class Meta:
        unique_together = ('user', 'deal')  # ป้องกันการเพิ่มดีลซ้ำในรายการโปรดของผู้ใช้
        verbose_name        = "ดีลโปรด"
        verbose_name_plural = "ดีลโปรด"

    def __str__(self):
        return f"{self.user.username} ชื่นชอบ {self.deal.title}"

class FlashMenu(models.Model):
    """ เมนูนาทีทอง """
    title            = models.CharField("ชื่อเมนู", max_length=100)
    image            = models.ImageField("รูปเมนู", upload_to='flash_menus/')
    original_price   = models.DecimalField("ราคาต้นฉบับ", max_digits=8, decimal_places=2)
    discounted_price = models.DecimalField("ราคาหลังลด",   max_digits=8, decimal_places=2)
    start_time       = models.TimeField("เริ่ม (HH:MM)")
    end_time         = models.TimeField("จบ (HH:MM)")
    is_active        = models.BooleanField("เปิดใช้งาน", default=True)

    class Meta:
        verbose_name        = "เมนูนาทีทอง"
        verbose_name_plural = "เมนูนาทีทอง"

    def __str__(self):
        return self.title

class CartItem(models.Model):
    """ ตะกร้าสินค้า """
    user     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    menu     = models.ForeignKey(Menu, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField("จำนวน", default=1)

    class Meta:
        unique_together = ('user', 'menu')
        verbose_name        = "รายการในตะกร้า"
        verbose_name_plural = "รายการในตะกร้า"

    def __str__(self):
        return f"{self.menu.title} x{self.quantity}"

class Order(models.Model):
    """ คำสั่งซื้อ """
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    address     = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True)
    total_price = models.DecimalField("ราคารวม", max_digits=10, decimal_places=2)
    placed_at   = models.DateTimeField("สั่งเมื่อ", default=timezone.now)
    is_paid     = models.BooleanField("ชำระเงินแล้ว", default=False)

    class Meta:
        verbose_name        = "ออร์เดอร์"
        verbose_name_plural = "ออร์เดอร์"

    def __str__(self):
        return f"Order#{self.id} ของ {self.user.username}"

class OrderItem(models.Model):
    """ รายการย่อยในออร์เดอร์ """
    order         = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu          = models.ForeignKey(Menu, on_delete=models.SET_NULL, null=True)
    quantity      = models.PositiveIntegerField("จำนวน", default=1)
    price_at_time = models.DecimalField("ราคาต่อหน่วย", max_digits=8, decimal_places=2)

    class Meta:
        verbose_name        = "สินค้าภายในออร์เดอร์"
        verbose_name_plural = "สินค้าภายในออร์เดอร์"

    def __str__(self):
        return f"{self.menu.title} x{self.quantity}"