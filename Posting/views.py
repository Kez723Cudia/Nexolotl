from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .models import Post
from .forms import PostForm

def feed_view(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            new_post = form.save(commit=False)
            if request.user.is_authenticated: Post.author = request.user
        else:
            default_user, _ = User.objects.get_or_create(username='Guest')
            Post.author = default_user 
            new_post.save()
            return redirect('feed')
    else:
        form = PostForm()

    posts = Post.objects.all() 
    return render(request, 'feed.html', {'form': form, 'posts': posts})