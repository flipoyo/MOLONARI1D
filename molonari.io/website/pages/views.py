from django.shortcuts import render


def home(request):
    return render(request, "pages/home.html")


def about(request):
    return render(request, "pages/about.html")


def hardware(request):
    return render(request, "pages/hardware.html")


def software(request):
    return render(request, "pages/software.html")


def contact(request):
    return render(request, "pages/contact.html")
