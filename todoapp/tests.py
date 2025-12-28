from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .forms import UserRegistrationForm, UserLoginForm, TaskForm
from django.test import Client
from django.urls import reverse
from django.contrib.messages import get_messages
import json

class UserRegistrationFormTest(TestCase):
    def test_valid_form(self):
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'strongpass123',
            'confirm_password': 'strongpass123'
        }
        form = UserRegistrationForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_form_password_mismatch(self):
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'strongpass123',
            'confirm_password': 'differentpass'
        }
        form = UserRegistrationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)  # Non-field error

    def test_invalid_form_duplicate_username(self):
        User.objects.create_user(username='existing', password='pass')
        data = {
            'username': 'existing',
            'email': 'new@example.com',
            'password': 'strongpass123',
            'confirm_password': 'strongpass123'
        }
        form = UserRegistrationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

class UserLoginFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')

    def test_valid_form(self):
        data = {'username': 'testuser', 'password': 'testpass'}
        form = UserLoginForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_form_wrong_password(self):
        data = {'username': 'testuser', 'password': 'wrongpass'}
        form = UserLoginForm(data=data)
        self.assertFalse(form.is_valid())

class TaskFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')

    def test_valid_form(self):
        data = {
            'title': 'New Task',
            'description': 'Description',
            'status': 'pending',
            'due_date': (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
        }
        form = TaskForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_form_empty_title(self):
        data = {
            'title': '',
            'description': 'Description',
            'status': 'pending'
        }
        form = TaskForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_invalid_form_past_due_date(self):
        data = {
            'title': 'Task',
            'description': 'Description',
            'status': 'pending',
            'due_date': (timezone.now() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
        }
        form = TaskForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('due_date', form.errors)

class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')
        # Create a task via API
        response = self.client.post(reverse('api_tasks'), data=json.dumps({
            'title': 'Test Task',
            'description': 'Test Description',
            'status': 'pending'
        }), content_type='application/json')
        self.task_id = response.json()['id']

    def test_home_view_unauthenticated(self):
        self.client.logout()
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Welcome to the Todo App')

    def test_home_view_authenticated(self):
        self.client.login(username='testuser', password='testpass')
        # Create a task
        self.client.post(reverse('api_tasks'), data=json.dumps({
            'title': 'Test Task',
            'description': 'Test Description',
            'status': 'pending'
        }), content_type='application/json')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Task')

    def test_home_view_add_task(self):
        self.client.login(username='testuser', password='testpass')
        data = {
            'title': 'New Task',
            'description': 'New Description',
            'status': 'pending'
        }
        response = self.client.post(reverse('home'), data)
        self.assertEqual(response.status_code, 302)  # Redirect to home
        # Check via API
        response = self.client.get(reverse('api_tasks'))
        data = response.json()
        self.assertEqual(len(data['tasks']), 2)

    def test_register_view_get(self):
        self.client.logout()
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'User Registration')

    def test_register_view_authenticated_redirect(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))

    def test_register_view_post_valid(self):
        self.client.logout()
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'strongpass123',
            'confirm_password': 'strongpass123'
        }
        response = self.client.post(reverse('register'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_view_post_invalid(self):
        self.client.logout()
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'pass',
            'confirm_password': 'pass'
        }
        response = self.client.post(reverse('register'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='newuser').exists())

    def test_login_view_get(self):
        self.client.logout()
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'User Login')

    def test_login_view_authenticated_redirect(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))

    def test_login_view_post_valid(self):
        data = {'username': 'testuser', 'password': 'testpass'}
        response = self.client.post(reverse('login'), data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))

    def test_login_view_post_invalid(self):
        self.client.logout()
        data = {'username': 'testuser', 'password': 'wrong'}
        response = self.client.post(reverse('login'), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter a correct username and password')

    def test_logout_view(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))

    def test_edit_task_view_get(self):
        self.client.login(username='testuser', password='testpass')
        # Create a task
        response = self.client.post(reverse('api_tasks'), data=json.dumps({
            'title': 'Test Task',
            'description': 'Test Description',
            'status': 'pending'
        }), content_type='application/json')
        task_id = response.json()['id']
        response = self.client.get(reverse('edit_task', args=[task_id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Task')

    def test_edit_task_view_post_valid(self):
        self.client.login(username='testuser', password='testpass')
        # Create a task
        response = self.client.post(reverse('api_tasks'), data=json.dumps({
            'title': 'Test Task',
            'description': 'Test Description',
            'status': 'pending'
        }), content_type='application/json')
        task_id = response.json()['id']
        data = {
            'title': 'Updated Task',
            'description': 'Updated Description',
            'status': 'completed'
        }
        response = self.client.post(reverse('edit_task', args=[task_id]), data)
        self.assertEqual(response.status_code, 302)
        # Check via API
        response = self.client.get(reverse('api_task_detail', args=[task_id]))
        task_data = response.json()
        self.assertEqual(task_data['title'], 'Updated Task')

    def test_edit_task_view_wrong_user(self):
        # Create task for testuser
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(reverse('api_tasks'), data=json.dumps({
            'title': 'Test Task',
            'description': 'Test Description',
            'status': 'pending'
        }), content_type='application/json')
        task_id = response.json()['id']
        # Login as user2
        user2 = User.objects.create_user(username='user2', password='pass')
        self.client.login(username='user2', password='pass')
        response = self.client.get(reverse('edit_task', args=[task_id]))
        self.assertEqual(response.status_code, 404)

    def test_delete_task_view_get(self):
        self.client.login(username='testuser', password='testpass')
        # Create a task
        response = self.client.post(reverse('api_tasks'), data=json.dumps({
            'title': 'Test Task',
            'description': 'Test Description',
            'status': 'pending'
        }), content_type='application/json')
        task_id = response.json()['id']
        response = self.client.get(reverse('delete_task', args=[task_id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Delete Task')

    def test_delete_task_view_post(self):
        self.client.login(username='testuser', password='testpass')
        # Create a task
        response = self.client.post(reverse('api_tasks'), data=json.dumps({
            'title': 'Test Task',
            'description': 'Test Description',
            'status': 'pending'
        }), content_type='application/json')
        task_id = response.json()['id']
        response = self.client.post(reverse('delete_task', args=[task_id]))
        self.assertEqual(response.status_code, 302)
        # Check via API
        response = self.client.get(reverse('api_task_detail', args=[task_id]))
        self.assertEqual(response.status_code, 404)

    def test_delete_task_view_wrong_user(self):
        # Create task for testuser
        self.client.login(username='testuser', password='testpass')
        response = self.client.post(reverse('api_tasks'), data=json.dumps({
            'title': 'Test Task',
            'description': 'Test Description',
            'status': 'pending'
        }), content_type='application/json')
        task_id = response.json()['id']
        # Login as user2
        user2 = User.objects.create_user(username='user2', password='pass')
        self.client.login(username='user2', password='pass')
        response = self.client.post(reverse('delete_task', args=[task_id]))
        self.assertEqual(response.status_code, 404)

class APITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')
        # Create a task via API
        response = self.client.post(reverse('api_tasks'), data=json.dumps({
            'title': 'Test Task',
            'description': 'Test Description',
            'status': 'pending'
        }), content_type='application/json')
        self.task_id = response.json()['id']

    def test_api_tasks_get(self):
        response = self.client.get(reverse('api_tasks'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('tasks', data)
        self.assertEqual(len(data['tasks']), 1)

    def test_api_tasks_post(self):
        response = self.client.post(reverse('api_tasks'), data=json.dumps({
            'title': 'New Task',
            'description': 'New Description',
            'status': 'in_progress'
        }), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn('id', data)

    def test_api_task_detail_get(self):
        response = self.client.get(reverse('api_task_detail', args=[self.task_id]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['title'], 'Test Task')

    def test_api_task_detail_put(self):
        response = self.client.put(reverse('api_task_detail', args=[self.task_id]), data=json.dumps({
            'title': 'Updated Task',
            'description': 'Updated Description',
            'status': 'completed'
        }), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        # Verify update
        response = self.client.get(reverse('api_task_detail', args=[self.task_id]))
        data = response.json()
        self.assertEqual(data['title'], 'Updated Task')

    def test_api_task_detail_delete(self):
        response = self.client.delete(reverse('api_task_detail', args=[self.task_id]))
        self.assertEqual(response.status_code, 200)
        # Verify delete
        response = self.client.get(reverse('api_task_detail', args=[self.task_id]))
        self.assertEqual(response.status_code, 404)

    def test_api_unauthenticated(self):
        self.client.logout()
        response = self.client.get(reverse('api_tasks'))
        self.assertEqual(response.status_code, 401)
