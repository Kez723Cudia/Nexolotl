from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Profile
from .forms import ProfileForm

#to view a user's profile
def profile_view(request, username):
    user_profile = get_object_or_404(Profile, user__username=username)
    return render(request, 'profiles/profile.html', {'profile': user_profile})

#to edit a own user's profile pero logged in user lang 
@login_required
def profile_edit(request):
    user_profile = get_object_or_404(Profile, user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            return redirect('profile_view', username=request.user.username)
    else:
        form = ProfileForm(instance=user_profile)
    return render(request, 'profiles/template/profile_edit.html', {'form': form})
