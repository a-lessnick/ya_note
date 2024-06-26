# notes/tests/test_content.py
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note
from notes.tests.test_routes import User


class TestContent(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатель')
        cls.author_logged = Client()
        cls.reader_logged = Client()
        cls.author_logged.force_login(cls.author)
        cls.reader_logged.force_login(cls.reader)
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=cls.author,
        )
        cls.url_notes_list = reverse('notes:list')
        cls.url_notes_add = reverse('notes:add')
        cls.url_notes_edit = reverse('notes:edit', args=(cls.note.slug,))

    def test_notes_list_for_users(self):
        """
        Тест того, что в список заметок одного пользователя
        не попадают заметки другого пользователя.
        """
        users_list = (
            (self.author_logged, True),
            (self.reader_logged, False),
        )
        for user, status in users_list:
            with self.subTest():
                response = user.get(self.url_notes_list)
                object_list = response.context['object_list']
                self.assertEqual(self.note in object_list, status)

    def test_pages_contains_form(self):
        """
        Тестирование передачи формы на страницы создания
        и редактирования заметок.
        """
        urls = (self.url_notes_add, self.url_notes_edit)
        for url in urls:
            with self.subTest():
                response = self.author_logged.get(url)
                self.assertIn('form', response.context)