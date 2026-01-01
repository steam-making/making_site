from django import forms
from .models import Material
from .models import Material, Vendor, VendorType, Order, Receipt, MaterialRelease, MaterialReleaseItem, MaterialOrderItem
from django.contrib.auth.models import User
from teachers.models import TeachingInstitution

class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ['name', 'vendor_type', 'contact', 'address']
        labels = {
            'name': '거래처명',
            'vendor_type': '종류',
            'contact': '연락처',
            'address': '주소',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'vendor_type': forms.Select(attrs={'class': 'form-select'}),
            'contact': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
        }



class VendorTypeForm(forms.ModelForm):
    class Meta:
        model = VendorType
        fields = ['name']
        labels = {'name': '종류명'}
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '예: 로봇, 과학 등'}),
        }

        
class MaterialUploadForm(forms.Form):
    file = forms.FileField(label='엑셀 파일 업로드')


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['teacher', 'institution', 'material', 'quantity', 'expected_date']  # 연도/월은 자동 처리

    teacher = forms.ModelChoiceField(
        queryset=User.objects.filter(profile__user_type='teacher'),
        label='강사',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    institution = forms.ModelChoiceField(
        queryset=TeachingInstitution.objects.all(),
        label='출강장소',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    expected_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False,
        label='예상 입고일'
    )

    def __init__(self, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class ReceiptForm(forms.ModelForm):
    class Meta:
        model = Receipt
        fields = ['received_quantity']
        
class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = '__all__'
        
class MaterialReleaseForm(forms.ModelForm):
    class Meta:
        model = MaterialRelease
        fields = ['teacher', 'institution', 'order_month', 'expected_date', 'release_method']
        widgets = {
            'release_method': forms.Select(attrs={'class': 'form-select'}),
        }       
        
# ✅ 견적서 정보 수정(제목/비고)
class MaterialReleaseEstimateForm(forms.ModelForm):
    class Meta:
        model = MaterialRelease
        fields = ["title", "notes"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "예: 2025-09 기관 납품 견적"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "특이사항/납기/계좌 등"}),
        }

# ✅ 교구재 포함/제외 체크
class MaterialReleaseItemIncludeForm(forms.ModelForm):
    class Meta:
        model = MaterialReleaseItem
        fields = ["included"]
        widgets = {
            "included": forms.CheckboxInput(attrs={"class": "form-check-input"})
        }
        
class MaterialReleaseItemIncludeForm(forms.ModelForm):
    class Meta:
        model = MaterialReleaseItem
        fields = ['included', 'group_name']   # ✅ 품명도 같이 수정
        widgets = {
            'included': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'group_name': forms.TextInput(attrs={
                'class': 'form-control form-control-sm text-muted',
                'placeholder': '그룹명',
            }),
        }
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.group_name:  # ✅ 그룹명 비어 있으면 원래 교구재명 사용
            instance.group_name = instance.material.name
        if commit:
            instance.save()
        return instance
    
class MaterialOrderItemForm(forms.ModelForm):
    class Meta:
        model = MaterialOrderItem
        fields = ["vendor", "material", "quantity", "receive_type"]
        labels = {
            "vendor": "거래처",
            "material": "교구재명",
            "quantity": "수량",
            "receive_type": "입고 종류",
        }
        widgets = {
            "vendor": forms.Select(attrs={"class": "form-select"}),
            "material": forms.Select(attrs={"class": "form-select"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "receive_type": forms.Select(attrs={"class": "form-select"}),
        }