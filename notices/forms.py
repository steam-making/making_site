from django import forms
from .models import Notice

class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = ["title", "content", "audience", "status", "is_pinned", "attachment"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "제목"}),
            "content": forms.Textarea(attrs={"class": "form-control", "rows": 10, "placeholder": "내용"}),
            "audience": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "is_pinned": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "attachment": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
