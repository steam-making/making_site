from django import forms
from .models import DynamicLink

class DynamicLinkForm(forms.ModelForm):
    class Meta:
        model = DynamicLink
        fields = ["key", "url", "title", "is_active"]
        widgets = {
            "key": forms.TextInput(attrs={"class": "form-control", "placeholder": "예: recruit2025"}),
            "url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://..."}),
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "관리용 제목"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "key": "단축 키",
            "url": "연결 URL",
            "title": "제목",
            "is_active": "활성화",
        }
