from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.db import connection
from django.utils import timezone
import logging
import json

from .forms import UserRegistrationForm, UserLoginForm, TaskForm

logger = logging.getLogger(__name__)

# Raw SQL functions for Task CRUD
def create_task_table():
    """Create tasks table if it doesn't exist."""
    with connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                due_date DATETIME,
                status VARCHAR(20) DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES auth_user(id)
            )
        """)

def create_task(user_id, title, description, due_date, status):
    """Create a new task."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO tasks (user_id, title, description, due_date, status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, [user_id, title, description, due_date, status, timezone.now(), timezone.now()])
            return cursor.lastrowid
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise

def get_tasks(user_id):
    """Get all tasks for a user."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, title, description, due_date, status, created_at, updated_at
                FROM tasks
                WHERE user_id = %s
                ORDER BY created_at DESC
            """, [user_id])
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error getting tasks: {e}")
        raise

def get_task(task_id, user_id):
    """Get a specific task."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, title, description, due_date, status, created_at, updated_at
                FROM tasks
                WHERE id = %s AND user_id = %s
            """, [task_id, user_id])
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                return dict(zip(columns, row))
            return None
    except Exception as e:
        logger.error(f"Error getting task: {e}")
        raise

def update_task(task_id, user_id, title, description, due_date, status):
    """Update a task."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE tasks
                SET title = %s, description = %s, due_date = %s, status = %s, updated_at = %s
                WHERE id = %s AND user_id = %s
            """, [title, description, due_date, status, timezone.now(), task_id, user_id])
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error updating task: {e}")
        raise

def delete_task_db(task_id, user_id):
    """Delete a task."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM tasks
                WHERE id = %s AND user_id = %s
            """, [task_id, user_id])
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        raise

# Ensure table exists
create_task_table()

def home(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            form = TaskForm(request.POST)
            if form.is_valid():
                try:
                    create_task(
                        user_id=request.user.id,
                        title=form.cleaned_data['title'],
                        description=form.cleaned_data['description'],
                        due_date=form.cleaned_data['due_date'],
                        status=form.cleaned_data['status']
                    )
                    messages.success(request, 'Task added successfully.')
                    return redirect('home')
                except Exception as e:
                    messages.error(request, 'Error adding task.')
                    logger.error(f"Error in home POST: {e}")
        else:
            form = TaskForm()
        try:
            tasks = get_tasks(request.user.id)
        except Exception as e:
            tasks = []
            messages.error(request, 'Error loading tasks.')
            logger.error(f"Error in home GET: {e}")
        return render(request, "index.html", {'tasks': tasks, 'form': form})
    return render(request, "index.html")

def register(request):
    """
    Handle user registration with form validation, logging, and exception handling.
    """
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                messages.success(request, 'Registration successful. You are now logged in.')
                logger.info(f"User {user.username} registered successfully.")
                return redirect('home')
            except Exception as e:
                logger.error(f"Error during user registration: {str(e)}")
                messages.error(request, 'An error occurred during registration. Please try again.')
                form.add_error(None, 'Registration failed due to an internal error.')
        else:
            logger.warning(f"Invalid registration form submission: {form.errors}")
    else:
        form = UserRegistrationForm()
    
    return render(request, 'register.html', {'form': form})

def user_login(request):
    """
    Handle user login with form validation, logging, and exception handling.
    """
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                try:
                    login(request, user)
                    messages.success(request, f'Welcome back, {username}!')
                    logger.info(f"User {username} logged in successfully.")
                    return redirect('home')
                except Exception as e:
                    logger.error(f"Error during login for user {username}: {str(e)}")
                    messages.error(request, 'An error occurred during login. Please try again.')
            else:
                messages.error(request, 'Invalid username or password.')
                logger.warning(f"Failed login attempt for username: {username}")
        else:
            logger.warning(f"Invalid login form submission: {form.errors}")
    else:
        form = UserLoginForm()
    
    return render(request, 'login.html', {'form': form})

def user_logout(request):
    """
    Handle user logout with logging.
    """
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
        logger.info(f"User {username} logged out.")
    return redirect('home')

def delete_task(request, task_id):
    try:
        task = get_task(task_id, request.user.id)
        if not task:
            return HttpResponse('Task not found', status=404)
    except Exception as e:
        logger.error(f"Error getting task for delete: {e}")
        return HttpResponse('Error', status=500)
    
    if request.method == 'POST':
        try:
            delete_task_db(task_id, request.user.id)
            messages.success(request, 'Task deleted successfully.')
            return redirect('home')
        except Exception as e:
            messages.error(request, 'Error deleting task.')
            logger.error(f"Error in delete_task POST: {e}")
    return render(request, 'delete_confirm.html', {'task': task})

# API Endpoints
def api_tasks(request):
    """API endpoint for tasks: GET to list, POST to create."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    if request.method == 'GET':
        try:
            tasks = get_tasks(request.user.id)
            return JsonResponse({'tasks': tasks}, safe=False)
        except Exception as e:
            logger.error(f"Error in api_tasks GET: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            task_id = create_task(
                user_id=request.user.id,
                title=data['title'],
                description=data.get('description', ''),
                due_date=data.get('due_date'),
                status=data.get('status', 'pending')
            )
            return JsonResponse({'id': task_id, 'message': 'Task created'}, status=201)
        except (KeyError, json.JSONDecodeError) as e:
            return JsonResponse({'error': 'Invalid data'}, status=400)
        except Exception as e:
            logger.error(f"Error in api_tasks POST: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

def api_task_detail(request, task_id):
    """API endpoint for task detail: GET, PUT, DELETE."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        task = get_task(task_id, request.user.id)
        if not task:
            return JsonResponse({'error': 'Task not found'}, status=404)
    except Exception as e:
        logger.error(f"Error getting task in api_task_detail: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)
    
    if request.method == 'GET':
        return JsonResponse(task)
    
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            success = update_task(
                task_id=task_id,
                user_id=request.user.id,
                title=data['title'],
                description=data.get('description', ''),
                due_date=data.get('due_date'),
                status=data.get('status', 'pending')
            )
            if success:
                return JsonResponse({'message': 'Task updated'})
            else:
                return JsonResponse({'error': 'Update failed'}, status=400)
        except (KeyError, json.JSONDecodeError) as e:
            return JsonResponse({'error': 'Invalid data'}, status=400)
        except Exception as e:
            logger.error(f"Error in api_task_detail PUT: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)
    
    elif request.method == 'DELETE':
        try:
            success = delete_task_db(task_id, request.user.id)
            if success:
                return JsonResponse({'message': 'Task deleted'})
            else:
                return JsonResponse({'error': 'Delete failed'}, status=400)
        except Exception as e:
            logger.error(f"Error in api_task_detail DELETE: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

def edit_task(request, task_id):
    try:
        task = get_task(task_id, request.user.id)
        if not task:
            return HttpResponse('Task not found', status=404)
    except Exception as e:
        logger.error(f"Error getting task for edit: {e}")
        return HttpResponse('Error', status=500)
    
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            try:
                update_task(
                    task_id=task_id,
                    user_id=request.user.id,
                    title=form.cleaned_data['title'],
                    description=form.cleaned_data['description'],
                    due_date=form.cleaned_data['due_date'],
                    status=form.cleaned_data['status']
                )
                messages.success(request, 'Task updated successfully.')
                return redirect('home')
            except Exception as e:
                messages.error(request, 'Error updating task.')
                logger.error(f"Error in edit_task POST: {e}")
    else:
        form = TaskForm(initial=task)
    return render(request, 'edit_task.html', {'form': form, 'task': task})
