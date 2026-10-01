from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from .models import testimonial
from .forms import testimonialForm

User = get_user_model()


# Create View
class TestimonialCreateView(LoginRequiredMixin, CreateView):
    model = testimonial
    form_class = testimonialForm
    template_name = 'testimonials/testimonial_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['username'] = self.kwargs['username']
        return context

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.recipient = get_object_or_404(User, username=self.kwargs['username'])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('profile', kwargs={'username': self.kwargs['username']})


# List View
class TestimonialListView(ListView):
    model = testimonial
    template_name = 'testimonials/testimonial_list.html'
    context_object_name = 'testimonials'

    def get_queryset(self):
        self.recipient_user = get_object_or_404(User, username=self.kwargs['username'])
        return testimonial.objects.filter(recipient=self.recipient_user, is_approved=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recipient_user'] = self.recipient_user
        context['profile'] = self.recipient_user.profile  # testimonial_list.html expects "profile"
        return context


@login_required
def approve_testimonial(request, testimonial_id):
    obj = get_object_or_404(testimonial, id=testimonial_id)
    if request.user == obj.recipient:
        obj.is_approved = True
        obj.save()
    return redirect('profile', username=request.user.username)