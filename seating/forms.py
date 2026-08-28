from django import forms


class GroupSeatForm(forms.Form):
    seat_rows = forms.IntegerField(
        min_value=1, max_value=8,
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm'})
    )
    seat_cols = forms.IntegerField(
        min_value=1, max_value=8,
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm'})
    )
