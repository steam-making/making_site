from django import forms
from .models import Student

from django import forms

class StudentForm(forms.Form):
    """학생 등록/수정용 일반 폼"""
    DIVISION_CHOICES = [
        ('1부', '1부'),
        ('2부', '2부'),
        ('3부', '3부'),
        ('미수강', '미수강'),
    ]

    division = forms.ChoiceField(
        choices=DIVISION_CHOICES,
        label="부서",
        widget=forms.Select(attrs={'class': 'form-select', 'style': 'max-width:250px;'})
    )
    grade = forms.CharField(label='학년', max_length=2, widget=forms.TextInput(
        attrs={'class': 'form-control text-center', 'style': 'width:70px;', 'placeholder': '1'}))
    class_name = forms.CharField(label='반', max_length=2, widget=forms.TextInput(
        attrs={'class': 'form-control text-center', 'style': 'width:70px;', 'placeholder': '1'}))
    number = forms.CharField(label='번호', max_length=3, widget=forms.TextInput(
        attrs={'class': 'form-control text-center', 'style': 'width:70px;', 'placeholder': '1'}))
    name = forms.CharField(label='학생이름', max_length=50, widget=forms.TextInput(
        attrs={'class': 'form-control', 'style': 'max-width:350px;', 'placeholder': '이름을 입력하세요'}))
    parent_contact = forms.CharField(label='학부모연락처', max_length=20, widget=forms.TextInput(
        attrs={'class': 'form-control', 'style': 'max-width:350px;', 'placeholder': '010-0000-0000'}))
