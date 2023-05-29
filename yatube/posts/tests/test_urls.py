from http import HTTPStatus

from django.test import TestCase

from posts.models import Follow, Group, Post, User


class PostsUrlsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Тестовое имя')
        cls.follower = User.objects.create_user(username='Тествый подписчик')
        cls.author = User.objects.create_user(username='Автор')
        Follow.objects.get_or_create(
            user=PostsUrlsTests.follower,
            author=PostsUrlsTests.author
        )
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='test-slug'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
            group=cls.group
        )

    def test_unexisting_page(self):
        """Non-existent page returns error 404."""
        response = self.client.get('/nonexistentpage/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_unexisting_page_correct_template(self):
        """Non-existent page receives correct template"""
        response = self.client.get('/nonexistentpage/')
        self.assertTemplateUsed(response, 'core/404.html')

    def test_urls_uses_correct_template_guest_user(self):
        """Guest user, urls receives correct templates"""
        templates_url_names = {
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_correct_redirection_guest_user(self):
        """Guest user, urls receives correct redirect to the pages"""
        url_names = [
            '/create/',
            f'/posts/{PostsUrlsTests.post.pk}/edit/'
        ]
        for address in url_names:
            response = self.client.get(address, follow=True)
            self.assertRedirects(response, f'/auth/login/?next={address}')

    def test_urls_uses_correct_template_auth_user(self):
        """Authorized user, urls receives the correct templates by"""
        self.client.force_login(PostsUrlsTests.user)
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': f'/group/{PostsUrlsTests.group.slug}/',
            'posts/profile.html': f'/profile/{PostsUrlsTests.user.username}/',
            'posts/post_detail.html': f'/posts/{PostsUrlsTests.post.pk}/',
            'posts/create_post.html': '/create/',
            'posts/follow.html': '/follow/'
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_correct_redirection_authorized_user(self):
        """
        Authorized user
        Urls receives a correct redirect to the pages by url
        """
        self.client.force_login(PostsUrlsTests.user)
        urls_redirection_addresses = {
            f'/posts/{PostsUrlsTests.post.pk}/edit/':
            f'/posts/{PostsUrlsTests.post.pk}/',
            f'/posts/{PostsUrlsTests.post.pk}/comment/':
            f'/posts/{PostsUrlsTests.post.pk}/'
        }
        for url, address in urls_redirection_addresses.items():
            with self.subTest(address=address):
                response = self.client.get(url)
                self.assertRedirects(response, address)

    def test_urls_uses_correct_template_author_user(self):
        """
        User author of the post
        Urls receives the correct template for editing the post
        """
        self.client.force_login(PostsUrlsTests.author)
        response = (self.client.get(f'/posts/{PostsUrlsTests.post.pk}/edit/'))
        self.assertTemplateUsed(response, 'posts/create_post.html')
