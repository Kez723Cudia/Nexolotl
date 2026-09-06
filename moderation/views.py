from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from .forms import ReportForm

def report_post_view(request):
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('report_success')
    else:
        form = ReportForm()
    
    return render(request, 'report_post.html', {'form': form})