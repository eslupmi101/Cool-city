from urllib.parse import urlencode

from django import forms
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post, User


class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        """
        user - is client without following
        follower - is client follower of author
        """
        cls.user = User.objects.create_user(username='Тестовое имя')
        cls.follower = User.objects.create_user(username='Тестовый подписчик')
        cls.author = User.objects.create_user(username='Тестовый автор')
        # user is folllower of author
        Follow.objects.get_or_create(
            user=PostsViewsTests.follower,
            author=PostsViewsTests.author
        )
        cls.group = Group.objects.create(
            title='Тестовый длинный заголовок для тестов',
            description='Тестовое описание',
            slug='test-slug'
        )
        image_test = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='image_test_old.gif',
            content=image_test,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый очень очень длинный текст для тестов',
            author=cls.author,
            image=uploaded
        )
        cls.post_with_group = Post.objects.create(
            text='Тестовый очень очень длинный текст для тестов',
            author=cls.author,
            group=cls.group,
            image=uploaded
        )
        cls.comment = Comment.objects.create(
            text="Тестовый комментарий",
            post=PostsViewsTests.post,
            author=PostsViewsTests.author
        )

    def setUp(self):
        # PostForm
        self.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ModelChoiceField,
        }
        # Create new 13 posts
        posts = [
            Post(
                text='Тестовый текст',
                author=PostsViewsTests.author,
                group=PostsViewsTests.group,
                image=PostsViewsTests.post.image,
            ) for i in range(13)
        ]
        Post.objects.bulk_create(posts)
        # Number posts
        self.number_posts = Post.objects.count()
        # Latest posts
        self.last_post = Post.objects.latest('pub_date')
        self.last_post_with_group = (
            Post.objects.filter(group=self.group).latest('pub_date')
        )
        self.last_post_author = (
            Post.objects.filter(author=self.author).latest('pub_date')
        )

    def test_index_cache(self):
        """
        Index page is cached correctly
        """
        new_post = Post.objects.create(
            text='Тестовый текст, кешированного поста',
            author=PostsViewsTests.author,
        )
        response = self.client.get(reverse('posts:index'))
        new_post_index = response.context['page_obj'][0]
        new_post.delete()
        self.assertEqual(
            response.context['page_obj'][0].pk,
            new_post_index.pk
        )
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        self.assertNotEqual(
            response.context['page_obj'][0].pk,
            new_post_index.pk
        )

    def test_guest_client_not_following_author(self):
        """
        Guest user can't following author
        """
        self.client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': PostsViewsTests.user.username}
            )
        )
        self.assertFalse(
            Follow.objects.filter(
                author=PostsViewsTests.user
            ).exists()
        )

    def test_authorized_client_following_author(self):
        """
        Authorized client can following author
        """
        self.client.force_login(PostsViewsTests.user)
        self.client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': PostsViewsTests.author.username}
            )
        )
        self.assertTrue(
            Follow.objects.filter(
                user=PostsViewsTests.user,
                author=PostsViewsTests.author
            ).exists()
        )

    def test_authorized_client_unfollowing_author(self):
        """
        Authorized client can unfollowing author
        """
        self.client.force_login(PostsViewsTests.follower)
        self.client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': PostsViewsTests.author.username}
            )
        )
        self.assertFalse(
            Follow.objects.filter(
                user=PostsViewsTests.follower,
                author=PostsViewsTests.author
            ).exists()
        )

    def test_pages_uses_correct_template_guest_user(self):
        """
        Guest user, pages uses correct templates
        """
        templates_pages_address = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse(
                'posts:group_posts',
                kwargs={'slug': PostsViewsTests.group.slug}
            ),
            'posts/profile.html': reverse(
                'posts:profile',
                kwargs={'username': PostsViewsTests.user.username}
            ),
            'posts/post_detail.html': reverse(
                'posts:post_detail',
                kwargs={'post_id': PostsViewsTests.post.pk}
            )
        }
        for template, address in templates_pages_address.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertTemplateUsed(response, template)

    def test_pages_correct_redirection_guest_user(self):
        """
        Guest user, pages correct redirections
        """
        page_addresses = [
            reverse('posts:post_create'),
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostsViewsTests.post.pk}
            ),
            reverse(
                'posts:add_comment',
                kwargs={'post_id': PostsViewsTests.post.pk}
            ),
            reverse(
                'posts:profile_follow',
                kwargs={'username': PostsViewsTests.user.username},
            ),
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': PostsViewsTests.user.username},
            )
        ]
        for address in page_addresses:
            with self.subTest(address=address):
                response = self.client.get(address)
                excepted_url = (reverse('users:login')
                                + '?' + urlencode({'next': address}))
                self.assertRedirects(
                    response,
                    excepted_url
                )

    def test_pages_uses_correct_template_authorized_user(self):
        """
        Authorized client, pages uses correct template
        """
        self.client.force_login(PostsViewsTests.user)
        templates_pages_address = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse(
                'posts:group_posts',
                kwargs={'slug': PostsViewsTests.group.slug}
            ),
            'posts/profile.html': reverse(
                'posts:profile',
                kwargs={'username': PostsViewsTests.user.username}
            ),
            'posts/post_detail.html': reverse(
                'posts:post_detail',
                kwargs={'post_id': PostsViewsTests.post.pk}
            ),
            'posts/create_post.html': reverse('posts:post_create')
        }
        for template, address in templates_pages_address.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertTemplateUsed(response, template)

    def test_pages_correct_redirection_authorized_user(self):
        """
        Authorized client, pages correct redirections
        """
        self.client.force_login(PostsViewsTests.user)
        address = reverse(
            'posts:post_edit',
            kwargs={'post_id': PostsViewsTests.post.pk}
        )
        response = self.client.get(address)
        self.assertRedirects(
            response,
            reverse('posts:post_detail',
                    kwargs={'post_id': PostsViewsTests.post.pk})
        )

    def test_pages_uses_correct_template_author_user(self):
        """
        Authorized author client, pages uses correct templates
        """
        self.client.force_login(PostsViewsTests.author)
        address = reverse(
            'posts:post_edit',
            kwargs={'post_id': PostsViewsTests.post.pk}
        )
        response = self.client.get(address)
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_follow_index_show_correct_context_with_following(self):
        """
        Follow index page show correct context
        Follower client follow author
        """
        self.client.force_login(PostsViewsTests.follower)
        new_post = Post.objects.create(
            text='Тестовый текст',
            author=PostsViewsTests.author
        )
        response = self.client.get(reverse('posts:follow_index'))
        page_obj = response.context['page_obj']
        context_values_expect_values = {
            response.context['title']: 'Избранные авторы',
            page_obj[0].pk: new_post.pk,
        }
        for value, expected in context_values_expect_values.items():
            with self.subTest(expected=expected):
                self.assertEqual(value, expected)
        Post.objects.filter(pk=new_post.pk).delete()

    def test_follow_index_show_correct_context_not_following(self):
        """
        Follow index page show correct context
        Follower client does not follow author
        """
        self.client.force_login(PostsViewsTests.user)
        response = self.client.get(reverse('posts:follow_index'))
        page_obj = response.context['page_obj']
        context_values_expect_values = {
            response.context['title']: 'Избранные авторы',
            len(page_obj): 0
        }
        for value, expected in context_values_expect_values.items():
            with self.subTest(expected=expected):
                self.assertEqual(value, expected)

    def test_index_page_show_correct_context(self):
        """
        Index page show correct context
        """
        response = self.client.get(reverse('posts:index'))
        page_obj = response.context['page_obj']
        context_values_expect_values = {
            response.context['title']: 'Главная страница',
            page_obj[0].pk: self.last_post.pk,
            page_obj[0].image: self.last_post.image
        }
        for value, expected in context_values_expect_values.items():
            with self.subTest(expected=expected):
                self.assertEqual(value, expected)

    def test_group_posts_page_show_correct_context(self):
        """
        Group posts page show correct context
        """
        response = self.client.get(
            reverse(
                'posts:group_posts',
                kwargs={'slug': PostsViewsTests.group.slug}
            )
        )
        self.assertEqual(response.status_code, 200)
        context_values_expect_values = {
            response.context['title']: 'Тестовый длинный заголовок для тестов',
            response.context['page_obj'][0].pk: self.last_post.pk,
            response.context['group']: PostsViewsTests.group,
            response.context['slug']: 'test-slug',
            response.context['post_list'][0].pk: self.last_post_with_group.pk,
            response.context['post_list'][0].image:
            self.last_post_with_group.image,
        }
        for value, expected in context_values_expect_values.items():
            with self.subTest(expected=expected):
                self.assertEqual(value, expected)

    def test_profile_page_show_correct_context(self):
        """
        Profile page show correct context
        """
        response = self.client.get(
            reverse(
                'posts:profile',
                kwargs={'username': PostsViewsTests.author.username}
            )
        )
        self.assertEqual(response.status_code, 200)
        context_values_expect_values = {
            response.context['title']: 'Профиль пользователя',
            response.context['author'].username:
            PostsViewsTests.author.username,
            response.context['page_obj'][0].pk: self.last_post_author.pk,
            response.context['number_posts']: self.number_posts,
            response.context['page_obj'][0].image: self.last_post_author.image,
        }
        for value, expected in context_values_expect_values.items():
            with self.subTest(expected=expected):
                self.assertEqual(value, expected)

    def test_post_detail_page_show_correct_context(self):
        """
        Post detail page show correct context
        """
        address = reverse(
            'posts:post_detail',
            kwargs={'post_id': PostsViewsTests.post.pk}
        )
        response = self.client.get(address)
        context_values_expect_values = {
            response.context['title']: 'Тестовый очень очень длинный т',
            response.context['post'].pk: 1,
            response.context['number_posts']: self.number_posts,
            response.context['author']: PostsViewsTests.post.author,
            response.context['post'].pk: PostsViewsTests.post.pk,
            response.context['page_obj'][0].pk: PostsViewsTests.comment.pk,
            response.context['post'].image: PostsViewsTests.post.image,
            response.context['post'].image: PostsViewsTests.post.image,
        }
        for value, expected in context_values_expect_values.items():
            with self.subTest(expected=expected):
                self.assertEqual(value, expected)

    def test_post_create_page_show_correct_context(self):
        """
        Post create page show correct context
        """
        self.client.force_login(PostsViewsTests.user)
        address = reverse('posts:post_create')
        response = self.client.get(address)
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertEqual(response.context['title'], 'Новый пост')

    def test_post_edit_page_show_correct_context(self):
        """
        Post edit page show correct context
        """
        self.client.force_login(PostsViewsTests.author)
        address = reverse(
            'posts:post_edit', kwargs={'post_id': PostsViewsTests.post.pk}
        )
        response = self.client.get(address)
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        context_values_expect_values = {
            response.context['title']: 'Редактирование поста',
            response.context['post'].pk: PostsViewsTests.post.pk,
            response.context['is_edit']: True,
        }
        for value, expected in context_values_expect_values.items():
            with self.subTest(expected=expected):
                self.assertEqual(value, expected)

    def test_post_with_group_exist_in_index(self):
        """
        Post with group field exist in index page
        """

        number_pages = Post.objects.all().count() // 10
        for page in range(number_pages):
            response = self.client.get(
                reverse('posts:index'),
                {'page': page}
            )
            page_obj = response.context['page_obj']
            post_exist = False
            for post in page_obj:
                if post.pk == PostsViewsTests.post_with_group.pk:
                    post_exist = True
                    break
            if post_exist:
                break
        self.assertEqual(post_exist, True)

    def test_post_with_group_exist_in_group_posts(self):
        """
        Post with group wild exist in group posts page
        """
        number_pages = (Post.objects
                        .filter(group=PostsViewsTests.group).count() // 10)
        post_exist = False
        for page in range(number_pages):
            address = (
                reverse(
                    'posts:group_posts',
                    kwargs={'slug': PostsViewsTests.group.slug}
                )
            )
            response = self.client.get(address)
            post_list = response.context['post_list']
            post_exist = False
            for post in post_list:
                if post.pk == PostsViewsTests.post_with_group.pk:
                    post_exist = True
                    break
                if post_exist:
                    break
        self.assertEqual(post_exist, True)

    def test_post_with_group_exist_in_profile(self):
        """
        Post with group field exist in profile page
        """
        address = reverse(
            'posts:profile',
            kwargs={'username': PostsViewsTests.author.username}
        )
        response = self.client.get(address)
        post_list = response.context['post_list']
        post_exist = False
        for post in post_list:
            if post.pk == PostsViewsTests.post_with_group.pk:
                post_exist = True
                break
            if post_exist:
                break
        self.assertEqual(post_exist, True)
