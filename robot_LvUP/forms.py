from django import forms
from .models import RobotLevelUp
from materials.models import Material

class RobotLevelUpForm(forms.ModelForm):
    class Meta:
        model = RobotLevelUp
        fields = [
            'year_month', 'material', 'section',
            'grade', 'class_no', 'student_no', 'student_name',
            'price', 'note'
        ]
        widgets = {
            'year_month': forms.TextInput(attrs={'type': 'month', 'class': 'form-control'}),
            'section': forms.TextInput(attrs={'class': 'form-control'}),
            'grade': forms.NumberInput(attrs={'class': 'form-control'}),
            'class_no': forms.NumberInput(attrs={'class': 'form-control'}),
            'student_no': forms.NumberInput(attrs={'class': 'form-control'}),
            'student_name': forms.TextInput(attrs={'class': 'form-control'}),
            'note': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # '로봇' 카테고리 교구만 선택 가능
        self.fields['material'].queryset = Material.objects.filter(vendor__vendor_type__name='로봇')
        self.fields['material'].widget.attrs.update({'class': 'form-select'})
