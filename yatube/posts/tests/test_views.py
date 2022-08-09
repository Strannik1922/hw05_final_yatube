import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Comment, Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTest(TestCase):
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
            title='Тестовая подборка записей №',
            slug='test-slug',
            description='Тестирующая контекст подборка №'
        )

        cls.post = Post.objects.create(
            text='Проверочный текст',
            author=cls.user,
            pub_date='04.02.2022',
            group=cls.group,
            image=cls.uploaded
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def tearDown(self):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""

        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user.username}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': str(self.post.id)}
                    ): 'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}):
            'posts/create_post.html',
            reverse('posts:create_post'): 'posts/create_post.html'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def page_show_correct_context(self, post):
        text = post.text
        author = post.author.username
        group = post.group.title
        self.assertEqual(author, 'auth')
        self.assertEqual(text, 'Проверочный текст')
        self.assertEqual(group, 'Тестовая подборка записей №')

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""

        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.page_show_correct_context(first_object)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""

        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        first_object = response.context['page_obj'][0]
        self.page_show_correct_context(first_object)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""

        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        first_object = response.context['page_obj'][0]
        self.page_show_correct_context(first_object)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""

        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        first_object = response.context['post']
        self.page_show_correct_context(first_object)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""

        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""

        response = self.authorized_client.get(reverse('posts:create_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая подборка записей №',
            slug='test-slug',
            description='Тестирующая контекст подборка №',
        )
        for cls.post in range(1, 10):
            cls.post = Post.objects.create(
                author=cls.user,
                text='Проверочный текст',
                group=cls.group,
            )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index_first_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 9)

    def test_index_second_page_contains_three_records(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 9)

    def test_group_list_first_page_contains_ten_records(self):
        response = self.client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(len(response.context['page_obj']), 9)

    def test_group_list_second_page_contains_three_records(self):
        response = self.client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 9)

    def test_profile_first_page_contains_ten_records(self):
        response = self.client.get(
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(len(response.context['page_obj']), 9)

    def test_profile_second_page_contains_three_records(self):
        response = self.client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user.username}) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 9)


class NewPostTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group_list = Group.objects.create(
            title='Тестовая группа 1',
            slug='test-slug1',
            description='Тестовое описание1',
        )
        cls.group_profile = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug2',
            description='Тестовое описание2'
        )
        cls.post_list = Post.objects.create(
            author=cls.user,
            text='Текст поста',
            group=cls.group_list
        )
        cls.post_profile = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
            group=cls.group_profile
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_appears_on_the_home_page(self):
        """Если указать группу, то пост отображается на главной странице."""

        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 2)

    def test_post_appears_on_the_group_list_page(self):
        """Если указать группу,
        то пост отображается на странице выбранной группы."""

        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group_list.slug})
        )
        object = response.context['page_obj'][0]
        post_author = object.author.username
        post_text = object.text
        post_group = object.group.title
        self.assertEqual(post_author, 'auth')
        self.assertEqual(post_text, 'Текст поста')
        self.assertEqual(post_group, 'Тестовая группа 1')

    def test_post_appears_on_the_profile_page(self):
        """Если указать группу,
        то пост отображается в профайле пользователя."""

        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            )
        )
        object = response.context['page_obj'][0]
        post_author = object.author.username
        post_text = object.text
        post_group = object.group.title
        self.assertEqual(post_author, 'auth')
        self.assertEqual(post_text, 'Текст поста')
        self.assertEqual(post_group, 'Тестовая группа 1')

    def test_post_does_not_appears_on_the_wrong_group_list_page(self):
        """Пост не отображается в группе, для которой он не предназначен."""

        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group_profile.slug}
                    )
        )
        object = response.context['page_obj'][0]
        post_group_slug = object.group.slug
        post_text = object.text
        post_group = object.group.title
        self.assertNotEqual(post_group_slug, 'test-slug1')
        self.assertNotEqual(post_text, 'Текст поста')
        self.assertNotEqual(post_group, 'Тестовая группа 1')


class TestComment(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')

        cls.group = Group.objects.create(
            title='Тестовая подборка записей №',
            slug='test-slug',
            description='Тестирующая контекст подборка №'
        )
        cls.post = Post.objects.create(
            text='Проверочный текст',
            author=cls.user,
            pub_date='04.02.2022',
            group=cls.group
        )
        cls.comment = Comment.objects.create(
            text='Тестовый комментарий',
            post=cls.post,
            author=cls.user,
            created='29.02.2022'
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_unauthorized_user_cant_comment(self):
        """Проверяем, что  неавторизованный пользователь
        не может оставить комментарий"""

        form_data = {
            'text': 'Тест'
        }

        response = self.guest_client.post(reverse(
            'posts:add_comment',
            kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.post.pk}/comment/'
        )

    def test_added_comment_is_on_post_detail_page(self):
        """Проверяем, что комментарий отобразится на странице поста"""

        response = self.guest_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id})
        )
        test_comment_text = 'Тестовый комментарий'
        response_comment_text = response.context['comments'][0].text
        self.assertEqual(test_comment_text, response_comment_text)

    def test_cache_index_page(self):
        """Тестирование корректной работы кэширования для страницы index"""

        response = self.authorized_client.get(reverse('posts:index'))
        cache_check = response.content
        Post.objects.get(pk=self.post.pk)
        response_old = self.authorized_client.get(reverse('posts:index'))
        cache_old_check = response_old.content
        self.assertEqual(
            cache_old_check,
            cache_check,
            'Не возвращает кэшированную страницу'
        )
        cache.clear()
        response_new = self.authorized_client.get(reverse('posts:index'))
        cache_new_check = response_new.content
        self.assertNotEqual(
            cache_old_check,
            cache_new_check,
            'Нет сброса кэша'
        )


class FinalTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.author = User.objects.create_user(username='Ivan')
        cls.group = Group.objects.create(
            title='Тестовая группа 1',
            slug='test-slug1',
            description='Тестовое описание1',
        )
        cls.group_author = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug2',
            description='Тестовое описание2'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст поста',
            group=cls.group
        )
        cls.post_author = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
            group=cls.group_author
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_author = Client()
        self.post_author.force_login(self.author)

    def test_correct_follow_and_unfollow(self):
        """Проверяем, что подписка и отписка работают корректно"""

        follow_count = Follow.objects.filter(
            user=self.user,
            author=self.author).count()
        self.assertEqual(0, follow_count)
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.author.username})
        )
        follow_count = Follow.objects.filter(
            user=self.user,
            author=self.author).count()
        self.assertEqual(1, follow_count)
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.author.username})
        )
        follow_count = Follow.objects.filter(
            user=self.user,
            author=self.author).count()
        self.assertEqual(0, follow_count)

    def test_correct_follow_index_page_work(self):
        """Тестируем, что страница подписок работает корректно"""

        Post.objects.create(
            text='Тестовая группа',
            author=self.author,
            group=self.group_author
        )
        response = self.post_author.get(reverse('posts:follow_index'))
        posts_on_page = len(response.context['page_obj'])
        self.assertEqual(0, posts_on_page)
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.author.username})
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        last_post = response.context['page_obj'][0].text
        self.assertEqual('Тестовая группа', last_post)

    def test_unauthorized_client_cannot_follow(self):
        """Тестируем, что неавторизованный пользователь
        не может подписаться"""

        response = self.guest_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.author.username})
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/profile/{self.author.username}/follow/'
        )
