from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from .forms import TestimonialForm
from .models import testimonies
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView
from django.contrib.auth.decorators import login_required

User = get_user_model()

#Create View
class TestimonialCreateView(LoginRequiredMixin, CreateView):
    model = testimonies
    form_class = TestimonialForm
    template_name = 'testimonies/testimonial_form.html'

    def form_valid(self, form):
        # Set the author and recipient of the testimonial before saving 
        form.instance.author = self.request.user
        form.instance.recipient = get_object_or_404(User, username=self.kwargs['username'])
        return super().form_valid(form)
    def get_success_url(self):
        return reverse_lazy('profile_view', kwargs={'username': self.kwargs['username']})

#List View
class TestimonialListView(ListView):
    model = testimonies
    template_name = 'testimonials/testimonial_list.html'
    context_object_name = 'testimonials'

    def get_queryset(self):
        self.recipient_user = get_object_or_404(User, username=self.kwargs['username'])
        return testimonies.objects.filter(recipient=self.recipient_user, is_approved=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recipient_user'] = self.recipient_user
        return context

@login_required
def approve_testimonial(request, testimonial_id):
    testimonial = get_object_or_404(testimonies, id=testimonial_id)
    if request.user == testimonial.recipient:
        testimonial.is_approved = True
        testimonial.save()
    return redirect('testimonial_list', username=testimonial.recipient.username)