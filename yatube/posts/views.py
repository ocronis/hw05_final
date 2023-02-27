from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post

NUMBER_OF_POSTS_ON_PAGE = 10
User = get_user_model()


def get_page_obj(request, post_list):
    paginator = Paginator(post_list, NUMBER_OF_POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


@cache_page(20, key_prefix='index_cache')
def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.all().order_by('-pub_date')
    page_obj = get_page_obj(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    template = 'posts/group_list.html'
    post_list = Post.objects.filter(group=group).order_by('-pub_date')
    page_obj = get_page_obj(request, post_list)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    template = 'posts/profile.html'
    post_list = Post.objects.filter(author=author).order_by('-pub_date')
    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=author).exists()
    page_obj = get_page_obj(request, post_list)
    context = {
        'page_obj': page_obj,
        'author': author,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    comments = Comment.objects.filter(post=post).order_by('-created')
    template = 'posts/post_detail.html'
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        post = form.save(False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user.username)
    template = 'posts/create_post.html'
    context = {'form': form}
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    template = 'posts/create_post.html'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    if request.method == 'POST' and form.is_valid():
        post.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'post_id': post_id,
        'form': form,
        'is_edit': True
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    post_list = Post.objects.filter(
        author__following__user=request.user).order_by('-pub_date')
    page_obj = get_page_obj(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author == request.user:
        return redirect('posts:profile', username=request.user.username)
    Follow.objects.create(
        user=request.user,
        author=author
    )
    return redirect('posts:profile', username=request.user.username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if author == request.user:
        return redirect('posts:profile', username=request.user.username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=request.user.username)
