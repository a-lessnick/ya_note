from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note
from notes.tests.test_routes import User


class TestLogic(TestCase):

    NOTES_SUCCESS_URL = reverse('notes:success')

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатель простой')
        cls.user_client = Client()
        cls.user_client.force_login(cls.author)
        cls.other_client = Client()
        cls.other_client.force_login(cls.reader)
        cls.first_note = {
            'title': 'Заголовок',
            'text': 'Текст',
            'slug': 'note-slug-11',
            'author': cls.author,
        }
        cls.second_note = {
            'title': 'Заголовок',
            'text': 'Текст',
            'slug': 'note-slug-12',
        }
        cls.note = cls.user_client.post(
            reverse('notes:add'), data=cls.first_note
        )
        cls.edit_note_url = reverse(
            'notes:edit', args=(cls.first_note['slug'],)
        )
        cls.start_notes_count = Note.objects.count()

    def add_note(self, note_data):
        return self.user_client.post(
            reverse('notes:add'), data=note_data
        )

    def assert_note(self, note_data):
        note = Note.objects.get(slug=note_data['slug'])
        self.assertEqual(note.title, note_data['title'])
        self.assertEqual(note.text, note_data['text'])
        self.assertEqual(note.slug, note_data['slug'])
        self.assertEqual(note.author, self.author)

    def test_create_note_for_regular_user(self):
        """Тест создания заметки авторизованным пользователем."""
        self.assertRedirects(
            self.add_note(self.second_note), self.NOTES_SUCCESS_URL
        )
        self.assertEqual(Note.objects.count(), self.start_notes_count + 1)
        self.assert_note(self.second_note)

    def test_create_note_for_anon_user(self):
        """Тест создания заметки анонимным пользователем."""
        url = reverse('notes:add')
        response = self.client.post(url, data=self.second_note)
        login_url = reverse('users:login')
        self.assertRedirects(response, f'{login_url}?next={url}')
        self.assertEqual(Note.objects.count(), self.start_notes_count)

    def test_unique_slug(self):
        """Тестирование уникальности slug заметки."""
        add_note = self.add_note(self.first_note)
        slug = Note.objects.last().slug
        self.assertFormError(
            add_note, 'form', 'slug', errors=(slug + WARNING)
        )
        self.assertEqual(Note.objects.count(), self.start_notes_count)

    def test_empty_slug(self):
        """Тестирование невозможности создания заметки с пустым slug."""
        self.second_note.pop('slug')
        self.assertRedirects(
            self.add_note(self.second_note), self.NOTES_SUCCESS_URL
        )
        self.assertEqual(Note.objects.count(), self.start_notes_count + 1)
        new_note = Note.objects.last()
        expected_slug = slugify(self.second_note['title'])
        self.assertEqual(new_note.slug, expected_slug)

    def test_edit_note_by_author(self):
        """Тестирование возможности редактирования заметки автором."""
        response = self.user_client.post(self.edit_note_url, self.second_note)
        self.assertRedirects(response, self.NOTES_SUCCESS_URL)
        self.assert_note(self.second_note)

    def test_edit_note_by_reader(self):
        """Тестирование невозможности редактирования чужих заметок."""
        response = self.other_client.post(self.edit_note_url, self.first_note)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assert_note(self.first_note)

    def test_delete_note_by_author(self):
        """Тестирование возможности удаления заметки автором."""
        response = self.user_client.post(
            reverse('notes:delete', args=(self.first_note['slug'],))
        )
        self.assertRedirects(response, self.NOTES_SUCCESS_URL)
        self.assertEqual(Note.objects.count(), self.start_notes_count - 1)

    def test_delete_note_by_reader(self):
        """Тестирование невозможности редактирования чужих заметок."""
        url = reverse('notes:delete', args=(Note.objects.last().slug,))
        response = self.other_client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), self.start_notes_count)