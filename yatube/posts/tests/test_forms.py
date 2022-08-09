import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')

        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )

        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

        cls.group = Group.objects.create(
            title='test-title',
            slug='test-slug',
            description='Описание группы для теста'
        )

        cls.group_other = Group.objects.create(
            title='test-title-other',
            slug='test-slug-other',
            description='Описание группы для нового теста'
        )

        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Проверочный тест',
            image=cls.uploaded
        )

        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_create(self):
        """При отправке валидной формы со страницы create
        создаётся новая запись в базе данных
        """

        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тест',
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:create_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.user.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тест',
                author=self.user,
                group=self.group
            ).exists()
        )

    def test_post_edit(self):
        """При отправке валидной формы со страницы post_edit
        происходит изменение поста с отправленным id в базе данных
        """

        form_data = {
            'text': 'Проверочный тест кода',
            'group': self.group_other.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        edit_post = response.context['post']
        self.assertTrue(
            Post.objects.filter(
                text=edit_post.text,
                author=self.user,
                group=self.group_other
            ).exists
        )

    def test_guest_client_posts_new_post(self):
        """Проверка перенаправления неавторизованного пользователя при попытке
        создать и опубликовать пост (через POST-запрос) на страницу
        авторизации, и что пост при этом не создаётся
        """

        posts_count = Post.objects.count()
        form_data = {
            'text': 'тестовый тескт для кода',
            'group': self.group.id
        }
        response = self.guest_client.post(
            reverse('posts:create_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, '/auth/login/?next=/create/')
        self.assertEqual(Post.objects.count(), posts_count)

    def test_create_comment(self):
        """Проверка формы создания нового
        комментария для авторизованного пользователя"""

        post = self.post
        comment_count = Comment.objects.filter(
            post=post.pk
        ).count()
        form_data = {
            'text': 'test comment'
        }
        self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.pk}
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(
            comment_count + 1,
            Comment.objects.filter(
                post=post.pk
            ).count()
        )

    def test_unauthorized_user_can_add_comment(self):
        """Проверка формы создания нового
        комментария для не авторизованного пользователя"""

        post = self.post
        comment_count = Comment.objects.filter(
            post=post.pk
        ).count()
        form_data = {
            'text': 'test comment'
        }
        self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.pk}
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(
            comment_count,
            Comment.objects.filter(
                post=post.pk
            ).count()
        )
