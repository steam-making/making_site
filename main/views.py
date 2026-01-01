from django.shortcuts import render

def home(request):
    return render(request, 'main/home.html')

def making_page(request):
    return render(request, 'main/making.html')