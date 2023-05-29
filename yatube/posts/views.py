from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from posts.forms import CommentForm, PostForm
from posts.models import Comment, Follow, Group, Like, Post, User


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    template = 'posts/index.html'
    context = {
        'title': 'Главная страница',
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.filter(group=group)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    template = 'posts/group_list.html'
    context = {
        'title': group.title,
        'page_obj': page_obj,
        'group': group,
        'slug': group.slug,
        'post_list': post_list,
    }
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = Post.objects.filter(author=author)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    template = 'posts/profile.html'
    following = (
        request.user.is_authenticated
        and Follow.objects.filter(user=request.user, author=author).exists())
    context = {
        'title': 'Профиль пользователя',
        'author': author,
        'page_obj': page_obj,
        'number_posts': post_list.count(),
        'post_list': post_list,
        'following': following
    }
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    number_posts = Post.objects.filter(author=post.author).count()
    comments_list = Comment.objects.filter(post=post)
    paginator = Paginator(comments_list, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    form = CommentForm()
    template = 'posts/post_detail.html'
    context = {
        'title': post.text[:30],
        'number_posts': number_posts,
        'author': post.author,
        'post': post,
        'page_obj': page_obj,
        'form': form
    }
    return render(request, template, context)


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(
            request.POST,
            files=request.FILES or None
        )
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', post.author.username)
    form = PostForm()
    template = 'posts/create_post.html'
    context = {
        'form': form,
        'title': 'Новый пост'
    }
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm()
    if request.method == 'POST':
        form = PostForm(
            request.POST,
            files=request.FILES or None,
            instance=post)
        if form.is_valid():
            form.save()
        return redirect('posts:post_detail', post_id=post.pk)
    template = 'posts/create_post.html'
    context = {
        'title': 'Редактирование поста',
        'form': form,
        'is_edit': True,
        'post': post,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = get_object_or_404(Post, pk=post_id)
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    template = 'posts/follow.html'
    context = {
        'title': 'Избранные авторы',
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(
            user=request.user,
            author=author
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=username)


@login_required
def post_like_or_unlike(request, post_id):
    referer = request.META.get('HTTP_REFERER')
    post = get_object_or_404(Post, id=post_id)
    if Like.objects.filter(user=request.user, post=post).exists():
        like = Like.objects.get(user=request.user, post=post)
        like.delete()
        post.likes -= 1
        post.save()
        return redirect(referer)
    Like.objects.create(user=request.user, post=post)
    post.likes += 1
    post.save()
    return redirect(referer)
