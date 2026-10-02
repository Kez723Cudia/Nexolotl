from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView
from .models import Post
from .forms import PostForm
from django.contrib.auth.decorators import login_required


@login_required
def post_feed_view(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, "Your post was published successfully!")
            return redirect('post_feed')
    else:
        form = PostForm()

    posts = Post.objects.all().order_by('-created_at')

    context = {
        'posts': posts,
        'form': form,
    }
    return render(request, 'feed.html', context)

def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    return render(request, 'post_detail.html', {'post': post})

@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, "Your post was published successfully!")
            return redirect('post_feed')
    else:
        form = PostForm()

    return render(request, 'create_post.html', {'form': form})

class PostListView(ListView):
    model = Post
    template_name = 'post_list.html'
    context_object_name = 'posts'
    ordering = ['-created_at']