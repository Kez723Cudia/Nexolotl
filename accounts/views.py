from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import RegisterForm
from .models import User

def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()
            return redirect("login")  
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        identifier = request.POST.get("identifier")
        password = request.POST.get("password")

        try:
            user_obj = User.objects.get(email__iexact=identifier)
        except User.DoesNotExist:
                user_obj = None

        user = None
        if user_obj:
            user = authenticate(request, username=user_obj.username, password=password)

        if user is not None:
            login(request, user)
            return redirect("daily_question_wall")
        else:
            return render(
                request, 
                "accounts/login.html", 
                {"error": "Invalid email or password"},
                )

    return render(request, "accounts/login.html")


def logout_view(request):
    logout(request)
    return redirect("login")

