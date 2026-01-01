from django import forms
from .models import SourceSite


class SourceSiteForm(forms.ModelForm):
    class Meta:
        model = SourceSite
        fields = [
            "area",
            "name",
            "url",
            "collector",        # ⭐ 추가
            "request_method",
            "extra_params",
            "list_selector",
            "title_selector",
            "link_selector",
            "date_selector",
            "active",
        ]

        widgets = {
            "collector": forms.Select(
                attrs={"class": "form-select"}
            ),
            "request_method": forms.Select(
                attrs={"class": "form-select"}
            ),
            "extra_params": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": '{"bbsId":"12558","mi":"12558"}'
                }
            ),
        }
