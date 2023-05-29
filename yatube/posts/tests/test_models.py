from django.test import TestCase

from posts.models import Group, Post, User


class PostsModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост с длинными описанием',
        )

    def test_models_have_correct_object_names(self):
        """The object names of models are correct"""
        str_objects_atr_expected_values = {
            str(PostsModelTest.user): PostsModelTest.user.username,
            str(PostsModelTest.group): PostsModelTest.group.title,
            str(PostsModelTest.post): PostsModelTest.post.text[:15],
            len(str(PostsModelTest.post)): 15
        }
        for str_object, exp_value in str_objects_atr_expected_values.items():
            with self.subTest(str_object=str_object):
                self.assertEqual(str_object, exp_value)

    def test_models_fields_have_correct_verbose_names(self):
        # Group
        """The verbose names of the model fields are correct"""
        group_fields_verboses = {
            'title': 'Название группы',
            'description': 'Описание группы',
            'slug': 'Адрес группы'
        }
        for field, expected_value in group_fields_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    PostsModelTest.group._meta.get_field(field).verbose_name,
                    expected_value
                )
        # Post
        post_fields_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата создания',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in post_fields_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    PostsModelTest.post._meta.get_field(field).verbose_name,
                    expected_value
                )
