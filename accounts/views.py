# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm
from .models import User

def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()
            return redirect("login")  # after registration, go to login
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        identifier = request.POST.get("identifier")
        password = request.POST.get("password")

        # Try to find user by email or phone
        user_obj = None
        try:
            user_obj = User.objects.get(email=identifier)
        except User.DoesNotExist:
            try:
                user_obj = User.objects.get(phone_number=identifier)
            except User.DoesNotExist:
                pass

        user = None
        if user_obj:
            user = authenticate(request, username=user_obj.username, password=password)

        if user is not None:
            login(request, user)
            return redirect("home")   # later redirect to profile
        else:
            # Wrong credentials → show advisory
            return render(request, "accounts/login.html", {"error": "Invalid email or password"})

    # GET request → clean login page, no error
    return render(request, "accounts/login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def home_view(request):
    return render(request, "accounts/home.html")
