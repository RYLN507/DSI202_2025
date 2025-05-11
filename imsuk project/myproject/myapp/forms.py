from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Address

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = [
            'label',
            'full_address',
            'subdistrict',
            'district',
            'province',
            'zipcode',
            'is_default',
        ]
        widgets = {
            'label': forms.TextInput(
                attrs={
                    'class': 'w-full border rounded p-2',
                    'placeholder': _('เช่น บ้าน, ที่ทำงาน (ไม่บังคับ)')
                }
            ),
            'full_address': forms.Textarea(
                attrs={
                    'class': 'w-full border rounded p-2',
                    'rows': 3,
                    'placeholder': _('รายละเอียดที่อยู่ เช่น หมู่บ้าน ซอย ...')
                }
            ),
            'subdistrict': forms.TextInput(
                attrs={'class': 'w-full border rounded p-2', 'placeholder': _('ตำบล')}
            ),
            'district': forms.TextInput(
                attrs={'class': 'w-full border rounded p-2', 'placeholder': _('อำเภอ')}
            ),
            'province': forms.TextInput(
                attrs={'class': 'w-full border rounded p-2', 'placeholder': _('จังหวัด')}
            ),
            'zipcode': forms.TextInput(
                attrs={'class': 'w-full border rounded p-2', 'placeholder': _('รหัสไปรษณีย์')}
            ),
            'is_default': forms.CheckboxInput(
                attrs={'class': 'h-4 w-4 text-green-600 border-gray-300 rounded'}
            ),
        }
        labels = {
            'label':        _('ชื่อที่อยู่ (ไม่บังคับ)'),
            'full_address': _('ที่อยู่'),
            'subdistrict':  _('ตำบล'),
            'district':     _('อำเภอ'),
            'province':     _('จังหวัด'),
            'zipcode':      _('รหัสไปรษณีย์'),
            'is_default':   _('ตั้งเป็นค่ามาตรฐาน'),
        }

# myapp/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Order

class SlipUploadForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['slip']
        widgets = {
            'slip': forms.ClearableFileInput(attrs={
                'class': 'opacity-0 absolute inset-0 cursor-pointer',
            }),
        }
        labels = {
            'slip': _('Payment Slip'),
        }

    def clean_slip(self):
        slip = self.cleaned_data.get('slip')
        if not slip:
            raise forms.ValidationError(_("กรุณาอัปโหลดสลิป"))
        name = slip.name.lower()
        ext = name.rsplit('.', 1)[-1]
        allowed = ('jpg','jpeg','png','pdf')
        if ext not in allowed:
            raise forms.ValidationError(
                _("ไฟล์ต้องเป็น JPG, PNG หรือ PDF เท่านั้น")
            )
        max_size = 2 * 1024 * 1024  # 2MB
        if slip.size > max_size:
            raise forms.ValidationError(
                _("ขนาดไฟล์ต้องไม่เกิน 2MB")
            )
        return slip




