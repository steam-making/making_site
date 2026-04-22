from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    return render(request, 'main/home.html')

def making_page(request):
    return render(request, 'main/making.html')