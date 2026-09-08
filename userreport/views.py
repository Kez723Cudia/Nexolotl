from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from .forms import UserReportForm

User = get_user_model()
# Create your views here.
@login_required
def submit_user_report(request, username):
    reported_user = get_object_or_404(User, username = username)
    next_url = request.POST.get('next') or 'profile_view'
    
    if request.method == 'POST':
        form = UserReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reported_user = reported_user
            report.reporter = request.user
            report.save()
            messages.success(request, "Thanks! Your report has been submitted for review.")
        else:
            messages.error(request, "Error! Please try again.")

    if next_url == 'profile_view':
        return redirect('profile_view', username = username)
    return redirect(next_url)