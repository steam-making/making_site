from django import forms
from .models import School

class SchoolForm(forms.ModelForm):
    class Meta:
        model = School
        fields = [
            "name",
            "student_count",
            "homepage",
            "zipcode",
            "address",
            "office_phone",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "student_count": forms.TextInput(attrs={"class": "form-control"}),
            "homepage": forms.URLInput(attrs={"class": "form-control"}),
            "zipcode": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "office_phone": forms.TextInput(attrs={"class": "form-control"}),
        }
