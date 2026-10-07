from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from profiles.forms import FriendListPrivacyForm, ProfileDisplaySettingsForm
from profiles.models import Profile, ProfileVisit
from .forms import (
    PrivateProfileViewingForm,
    ProfileViewingSettingsForm,
    RegisterForm,
)
from .models import User
from user_controls.models import Block

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

            if user.is_superuser:
                return redirect("dashboard_home")

            return redirect("post_feed")  # Redirect to the feed page after successful login
        else:
            return render(
                request, 
                "accounts/login.html", 
                {"error": "Invalid email or password"},
                )

    return render(request, "accounts/login.html")


@login_required
def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect("login")

    return render(request, "accounts/logout_confirm.html")


@login_required
def account_settings(request):
    user_profile = Profile.objects.get(user=request.user)
    blocked_users = Block.objects.filter(
        user=request.user,
    ).select_related("blocked_user")

    if request.method == "POST":
        was_private = request.user.private_profile_views
        settings_form = ProfileViewingSettingsForm(
            request.POST,
            instance=request.user,
        )
        friend_privacy_form = FriendListPrivacyForm(
            request.POST,
            instance=user_profile,
        )
        display_settings_form = ProfileDisplaySettingsForm(
            request.POST,
            instance=user_profile,
        )
        private_profile_form = PrivateProfileViewingForm(
            request.POST,
            instance=request.user,
        )

        if (
            settings_form.is_valid()
            and friend_privacy_form.is_valid()
            and display_settings_form.is_valid()
            and private_profile_form.is_valid()
        ):
            with transaction.atomic():
                settings_form.save()
                friend_privacy_form.save()
                display_settings_form.save()
                user = private_profile_form.save()
                if user.private_profile_views and not was_private:
                    ProfileVisit.objects.filter(viewer=user).update(viewer=None)
            return redirect("account_settings")
    else:
        settings_form = ProfileViewingSettingsForm(instance=request.user)
        friend_privacy_form = FriendListPrivacyForm(instance=user_profile)
        display_settings_form = ProfileDisplaySettingsForm(
            instance=user_profile,
        )
        private_profile_form = PrivateProfileViewingForm(instance=request.user)

    return render(
        request,
        "accounts/settings.html",
        {
            "form": settings_form,
            "friend_privacy_form": friend_privacy_form,
            "display_settings_form": display_settings_form,
            "private_profile_form": private_profile_form,
            "blocked_users": blocked_users,
        },
    )
