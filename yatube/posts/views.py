from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect

from .models import Post, Group
from .forms import PostForm

POSTS_PER_PAGE = 10
User = get_user_model()


def paginator(request, posts):
    paginator = Paginator(posts, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


def index(request):
    post_list = Post.objects.all()
    page_obj = paginator(request, post_list)
    template = 'posts/index.html'
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page_obj = paginator(request, post_list)
    template = 'posts/group_list.html'
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    page_obj = paginator(request, post_list)
    template = 'posts/profile.html'
    context = {
        'author': author,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    template = 'posts/post_detail.html'
    context = {
        'post': post,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
    if form.is_valid():
        post_create = form.save(commit=False)
        post_create.author = request.user
        post_create.save()
        return redirect('posts:profile', post_create.author)
    template = 'posts/post_create.html'
    context = {'form': form}
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    post_edit = get_object_or_404(Post, id=post_id)
    if request.user != post_edit.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST or None, instance=post_edit)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    template = 'posts/post_create.html'
    context = {'form': form, 'is_edit': True, 'post_id': post_id}
    return render(request, template, context)
