import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Тестовое имя')
        cls.author = User.objects.create_user(username='Тестовый автор')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
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
            text='Тестовый текст до редактирования',
            author=PostsFormsTests.author,
            group=PostsFormsTests.group,
            image=uploaded
        )
        cls.new_group = Group.objects.create(
            title='Новый тестовый заголовок',
            description='Новый тестовое описание',
            slug='new-test-slug'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_guest_client_not_create_post_form(self):
        """
        Guest client can't create post by using form
        """
        posts_number_before_new_post = Post.objects.count()
        redirect_url = reverse(
            'users:login'
        )
        text = 'Текст гостевого пользователя'
        create_form_data = {
            'text': text,
            'group': PostsFormsTests.group.pk,
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=create_form_data,
            follow=True
        )
        self.assertTrue(
            not Post.objects.filter(
                text=text,
            ).exists()
        )
        create_post_url = reverse('posts:post_create')
        self.assertRedirects(
            response,
            f'{redirect_url}?next={create_post_url}'
        )
        self.assertEqual(
            posts_number_before_new_post,
            Post.objects.count()
        )

    def test_authorized_client_create_post_form(self):
        """
        Authorized user uses correct post create form
        """
        self.client.force_login(PostsFormsTests.user)
        redirect_url = reverse(
            'posts:profile', kwargs={'username': PostsFormsTests.user.username}
        )
        text = 'Текст авторизованного пользователя'
        image_test = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='image_test.gif',
            content=image_test,
            content_type='image/gif'
        )
        create_form_data = {
            'text': text,
            'group': PostsFormsTests.group.pk,
            'image': uploaded
        }
        numbers_posts_before_create = Post.objects.count()
        response = self.client.post(
            reverse('posts:post_create'),
            data=create_form_data,
            follow=True,
            image='posts/image_test.gif'
        )
        new_post = Post.objects.latest('pub_date')
        self.assertTrue(
            Post.objects.filter(
                text=text,
                group=PostsFormsTests.group.pk,
                pk=new_post.pk,
                image='posts/image_test.gif',
            ).exists()
        )
        self.assertRedirects(response, redirect_url)
        self.assertEqual(
            Post.objects.count(),
            numbers_posts_before_create + 1,
        )

    def test_authorized_author_client_edit_post_form(self):
        """
        Authorized author user uses correct edit post form
        """
        self.client.force_login(PostsFormsTests.author)
        number_posts_before_edit = Post.objects.count()
        new_text = 'Отредактированный текст'
        new_image_test = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='image_test_new.gif',
            content=new_image_test,
            content_type='image/gif'
        )
        edit_form_data = {
            'text': new_text,
            'group': self.new_group.pk,
            'image': uploaded
        }
        edit_response = self.client.post(
            reverse(
                'posts:post_edit', kwargs={'post_id': PostsFormsTests.post.pk}
            ),
            data=edit_form_data,
            follow=True
        )
        self.assertTrue(
            Post.objects.filter(
                text=new_text,
                pk=PostsFormsTests.post.pk,
                group=PostsFormsTests.new_group.pk,
                author=PostsFormsTests.author,
                image='posts/image_test_new.gif'
            ).exists()
        )
        self.assertRedirects(
            edit_response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostsFormsTests.post.pk}
            ),
        )
        self.assertEqual(number_posts_before_edit, Post.objects.count())

    def test_guest_client_not_create_comment(self):
        """
        Guest user can't create comment
        """
        number_comments = Comment.objects.all().count()
        create_form_data = {
            'text': "Тест комментарий",
            'post': PostsFormsTests.post.pk
        }
        self.client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': PostsFormsTests.post.pk}
            ),
            data=create_form_data
        )
        self.assertEqual(
            Comment.objects.all().count(),
            number_comments
        )

    def test_authorized_client_create_comment(self):
        """
        Authorized client can create comment
        """
        self.client.force_login(PostsFormsTests.user)
        number_comments = Comment.objects.count()
        create_form_data = {
            'text': "Тест комментарий",
            'post': PostsFormsTests.post.pk
        }
        self.client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': PostsFormsTests.post.pk}
            ),
            data=create_form_data
        )
        self.assertEqual(
            Comment.objects.count(),
            number_comments + 1
        )
