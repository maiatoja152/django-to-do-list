from django.test import TestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from django.urls import reverse
from django.http import HttpResponse
from django.utils import timezone

from .models import Task
from .forms import DateTimeLocalInput
from .forms import TaskForm

from typing import List
from typing import Sequence
from typing import Optional

from bs4 import BeautifulSoup
from bs4 import Tag
from bs4 import ResultSet

from selenium import webdriver
from selenium.webdriver.common.by import By

import time


class ViewTests(TestCase):
    """Base class for testing views."""
    view_name: str


    def get_view_response(self, *, path_args: Sequence=()) -> HttpResponse:
        """Get an HttpResponse for a simple GET request to the view."""
        return self.client.get(reverse(self.view_name, args=path_args))


class TaskListViewTests(ViewTests):
    """Tests for the Task List view."""
    view_name = "todo:task-list"
    

    def test_no_tasks(self) -> None:
        """
        Test that an appropriate message is displayed when no tasks exist.
        """
        response: HttpResponse = self.get_view_response()
        self.assertContains(response, "You have no tasks.")
        self.assertQuerySetEqual(response.context["task_list"], [])
    

    def test_multiple_tasks(self) -> None:
        """
        Test the view when multiple tasks exist. The view should display the
        tasks' titles and checkboxes which are checked only for tasks that are
        completed.
        """
        tasks: List[Task] = []
        for i in range(5):
            tasks.append(Task.objects.create(
                title=f"Task {i}",
                completed=i % 2 == 0,
            ))
        
        response: HttpResponse = self.get_view_response()
        self.assertQuerySetEqual(
            response.context["task_list"],
            tasks,
            ordered=False,
        )
        soup: BeautifulSoup = BeautifulSoup(response.content, "lxml")
        for task in tasks:
            self.assertContains(response, task.title)
            # Test checkbox
            checkbox: Tag = soup.select(
                f"li[data-task-pk=\"{task.pk}\"] input.task-list-checkbox"
            )[0]
            if task.completed:
                self.assertIn("checked", checkbox.attrs)
            else:
                self.assertNotIn("checked", checkbox.attrs)


class TaskDetailViewTests(ViewTests):
    """Tests for the Task Detail view."""
    view_name = "todo:task-detail"


    def test_nonexistent_task(self) -> None:
        """
        Test that a 404 Not Found is returned for the detail view of a
        nonexistent task.
        """
        response: HttpResponse = self.get_view_response(path_args=(0,))
        self.assertEqual(response.status_code, 404)
        
    
    def test_post_returns_404_for_nonexistent_task(self) -> None:
        """
        Test that the view returns a 404 not found to a POST request for
        a nonexistent task.
        """
        response: HttpResponse = self.client.post(
            reverse(self.view_name, args=(1,))
        )
        self.assertEqual(response.status_code, 404)
    

    def test_existing_task_returns_ok(self) -> None:
        """
        Test that the view returns a 200 OK response to a GET request for
        an existing task.
        """
        task: Task = Task.objects.create(
            title="Test task",
            completed=True,
            due_date=timezone.now(),
            description="This is a test task.",
        )
        response: HttpResponse = self.get_view_response(path_args=(task.pk,))
        self.assertEqual(response.status_code, 200)
    

    def test_valid_post_request_returns_redirect(self) -> None:
        """
        Test that the view returns a redirect in response to a POST
        request that contains all TaskForm fields and refers to a task
        that exists.
        """
        task: Task = Task.objects.create(title="Test task")
        new_fields = {
            "title": "Modified task",
            "completed": True,
            "due_date": timezone.make_aware(
                timezone.datetime(2026, 4, 8, 13, 15)
            ),
            "description": "This is a modified task.",
        }
        response: HttpResponse = self.client.post(
            reverse(self.view_name, args=(task.pk,)),
            new_fields,
        )
        self.assertRedirects(
            response,
            reverse("todo:task-detail", args=(task.pk,)),
            status_code=302,
            target_status_code=200,
        )


    def test_valid_post_request_modifies_task(self) -> None:
        """
        Test that the view modifies a task in response to a POST
        request that contains all TaskForm fields and refers to a task
        that exists.
        """
        task: Task = Task.objects.create(
            title="Test task",
            completed=False,
            due_date=timezone.make_aware(
                timezone.datetime(2025, 4, 8, 5, 5)
            ),
            description="This is an unmodified task.",
        )
        new_fields = {
            "title": "Modified task",
            "completed": True,
            "due_date": timezone.make_aware(
                timezone.datetime(2026, 4, 8, 13, 15)
            ),
            "description": "This is a modified task.",
        }
        self.client.post(
            reverse(self.view_name, args=(task.pk,)),
            new_fields,
        )
        task.refresh_from_db()
        for field_name, new_value in new_fields.items():
            self.assertEqual(getattr(task, field_name), new_value)
    

    def test_invalid_post_request_does_not_modify_task(self) -> None:
        """
        Test that the view does not modify a task in response to a POST
        request that refers to a task that exists but is missing the
        required "title" field.
        """
        original_fields = {
            "title": "Test task",
            "completed": False,
            "due_date": timezone.make_aware(
                timezone.datetime(2025, 4, 8, 5, 5)
            ),
            "description": "This is an unmodified task.",
        }
        task: Task = Task.objects.create(**original_fields)
        new_fields = {
            "completed": True,
            "due_date": timezone.make_aware(
                timezone.datetime(2026, 4, 8, 13, 15)
            ),
            "description": "This is a modified task.",
        }
        self.client.post(
            reverse(self.view_name, args=(task.pk,)),
            new_fields,
        )
        # Assert that the task's fields were not modified.
        task.refresh_from_db()
        for field_name, new_value in new_fields.items():
            self.assertNotEqual(getattr(task, field_name), new_value)
        for field_name, original_value in original_fields.items():
            self.assertEqual(getattr(task, field_name), original_value)


class TaskFormTests(TestCase):
    """Tests for TaskForm."""
    def test_completed_and_incomplete_tasks(self) -> None:
        """
        Test that a task's title is shown in a textarea, its completed status
        is shown with a checkbox, its due_date is shown in a datetime field,
        and its description is shown in a textarea.

        This is done with both a complete and an incomplete task to test that
        the checkbox indicating completion is correct in both cases.
        """
        completed_task: Task = Task(
            title="Completed task",
            completed=True,
            due_date=timezone.make_aware(timezone.datetime(2023, 3, 3, 5, 5)),
            description="This is a completed task.",
        )
        incomplete_task: Task = Task(
            title="Incomplete task",
            completed=False,
            due_date=timezone.make_aware(timezone.datetime(2020, 6, 1, 1, 55)),
            description="This is an incomplete task.",
        )

        for task in completed_task, incomplete_task:
            form_html: str = str(TaskForm(instance=task))
            soup: BeautifulSoup = BeautifulSoup(form_html, "lxml")
            def get_tag_and_assert_only_one(selector: str) -> Tag:
                result_set: ResultSet = soup.select(selector)
                self.assertEqual(len(result_set), 1)
                return result_set[0]

            title: Tag = get_tag_and_assert_only_one("textarea#id_title")
            title_string: Optional[str] = title.string
            self.assertTrue(isinstance(title_string, str))
            self.assertEqual(title_string.strip(), task.title)

            checkbox: Tag = get_tag_and_assert_only_one(
                "input[type='checkbox']#id_completed"
            )
            if task.completed:
                self.assertIn("checked", checkbox.attrs)
            
            due_date: Tag = get_tag_and_assert_only_one(
                "input[type='datetime-local']#id_due_date"
            )
            date_value = DateTimeLocalInput().format_value(str(task.due_date))
            if date_value is not None:
                self.assertEqual(due_date["value"], date_value)

            description: Tag = get_tag_and_assert_only_one(
                "textarea#id_description"
            )
            description_string: Optional[str] = description.string
            self.assertTrue(isinstance(description_string, str))
            self.assertEqual(description_string.strip(), task.description)


class CreateTaskViewTests(ViewTests):
    view_name = "todo:create-task"


    def test_get_request_not_allowed(self) -> None:
        """
        Test that the view returns a 405 Method Not Allowed for a GET request.
        """
        response: HttpResponse = self.get_view_response()
        self.assertEqual(response.status_code, 405)
    

    def test_valid_post_request(self) -> None:
        """
        Test that the view creates a new Task in response to a valid POST
        request.
        """
        task_title = "Test task"
        response: HttpResponse = self.client.post(
            reverse(self.view_name),
            {
                "title": task_title,
                "completed": True,
                "due_date": timezone.now(),
                "description": "This task should be created",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(Task.objects.all()), 1)
    

    def test_invalid_post_request(self) -> None:
        """
        Test that the view returns a 400 Bad Request in response to a POST
        request specifying no title for the task.
        """
        response: HttpResponse = self.client.post(
            reverse(self.view_name),
            {
                "completed": True,
                "due_date": timezone.now(),
                "description": "This task should not be created.",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(Task.objects.all()), 0)


class EditTaskCompletedViewTests(ViewTests):
    view_name = "todo:edit-task-completed"


    def test_get_request_not_allowed(self) -> None:
        """
        Test that the view returns a 405 Method Not Allowed for a GET request.
        """
        task: Task = Task.objects.create(title="Test task")
        response: HttpResponse = self.get_view_response(path_args=(task.pk,))
        self.assertEqual(response.status_code, 405)

    
    def test_not_found_for_nonexistent_task(self) -> None:
        """
        Test that the view returns a 404 Not Found in response to a POST
        request for a nonexistent task.
        """
        response: HttpResponse = self.client.post(
            reverse(self.view_name, args=(1,)),
        )
        self.assertEqual(response.status_code, 404)
    

    def test_post_request_no_completed_field(self) -> None:
        """
        Test that the view returns a 400 Bad Request for a POST request
        lacking a "completed" field.
        """
        task: Task = Task.objects.create(title="Test task")
        response: HttpResponse = self.client.post(
            reverse(self.view_name, args=(task.pk,)),
            {},
        )
        self.assertEqual(response.status_code, 400)
    
    def test_set_task_completed(self) -> None:
        """
        Test that a task's completed field is set to True in response
        to a POST request containing completed=True.
        """
        task: Task = Task.objects.create(title="Test task", completed=False)
        self.assertFalse(task.completed)
        response: HttpResponse = self.client.post(
            reverse(self.view_name, args=(task.pk,)),
            { "completed": True },
        )
        self.assertEqual(response.status_code, 200)
        task.refresh_from_db()
        self.assertTrue(task.completed)


    def test_set_task_not_completed(self) -> None:
        """
        Test that a task's completed field is set to False in response
        to a POST request containing completed=False.
        """
        task: Task = Task.objects.create(title="Test task", completed=True)
        self.assertTrue(task.completed)
        response: HttpResponse = self.client.post(
            reverse(self.view_name, args=(task.pk,)),
            { "completed": False },
        )
        self.assertEqual(response.status_code, 200)
        task.refresh_from_db()
        self.assertFalse(task.completed)


class DeleteTaskViewTests(ViewTests):
    view_name = "todo:delete-task"


    def test_get_returns_not_allowed(self) -> None:
        """
        Test that the view returns a 405 Method Not Allowed in
        response to a GET request for an existing task.
        """
        response: HttpResponse = self.get_view_response(path_args=(1,))
        self.assertEqual(response.status_code, 405)
    

    def test_nonexistent_task_returns_not_found(self) -> None:
        """
        Test that the view returns a 404 Not Found in response to
        a POST request for a nonexistent task.
        """
        response: HttpResponse = self.client.post(
            reverse(self.view_name, args=(1,)),
        )
        self.assertEqual(response.status_code, 404)
    

    def test_deletes_task(self) -> None:
        """
        Test that the view deletes a task in response to a POST
        request for the task.
        """
        Task.objects.create(title="Test task")
        self.assertEqual(len(Task.objects.all()), 1)
        response: HttpResponse = self.client.post(
            reverse(self.view_name, args=(1,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(Task.objects.all()), 0)


class SeleniumTests(StaticLiveServerTestCase):
    """Tests using Selenium."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.chrome_driver = webdriver.Chrome()
        cls.chrome_driver.implicitly_wait(5)


    @classmethod
    def tearDownClass(cls):
        cls.chrome_driver.quit()


    def test_add_tasks_from_list_view(self) -> None:
        """
        Test that tasks are successfully created and displayed after
        using the "Add a new task" input from the task-list view.
        """
        self.chrome_driver.get(
            self.live_server_url + reverse("todo:task-list")
        )
        tasks_created: List[str] = []
        for i in range(5):
            task_title: str = f"Test task {i}"
            add_task_input = self.chrome_driver.find_element(
                By.ID,
                "add-task-input"
            )
            add_task_input.send_keys(task_title, webdriver.Keys.ENTER)
            tasks_created.append(Task.objects.get(title=task_title))
            # Test that the new task and all past tasks are displayed.
            for task in tasks_created:
                list_item = self.chrome_driver.find_element(
                    By.CSS_SELECTOR,
                    f"li[data-task-pk=\"{task.pk}\"]",
                )
                self.assertEqual(
                    list_item.find_element(By.TAG_NAME, "a").text,
                    task.title,
                )

    
    def test_checkbox_from_list_view(self) -> None:
        """
        Test that checking a task's checkbox completes the task and
        unchecking it sets the task to incomplete.
        """
        task: Task = Task.objects.create(title="Test task", completed=False)
        self.chrome_driver.get(
            self.live_server_url + reverse("todo:task-list")
        )
        checkbox = self.chrome_driver.find_element(
            By.CSS_SELECTOR,
            f"li[data-task-pk='{task.pk}'] input.task-list-checkbox"
        )
        self.assertIsNone(checkbox.get_attribute("checked"))
        self.assertEqual(task.completed, False)

        checkbox.click()
        self.assertIsNotNone(checkbox.get_attribute("checked"))
        task.refresh_from_db(fields=["completed"])
        self.assertEqual(task.completed, True)

        checkbox.click()
        self.assertIsNone(checkbox.get_attribute("checked"))
        task.refresh_from_db(fields=["completed"])
        self.assertEqual(task.completed, False)


    def test_delete_task_from_detail_view(self) -> None:
        """
        Test that the delete button in the task-detail view deletes
        the task and changes the page to the task-list page.
        """
        task_pk: int = Task.objects.create(title="Test task").pk
        self.chrome_driver.get(
            self.live_server_url + reverse("todo:task-detail", args=(task_pk,))
        )
        self.chrome_driver.find_element(
            By.CSS_SELECTOR,
            "button.task-detail-delete-button"
        ).click()
        # Give some time for the app to delete the task.
        time.sleep(0.5)
        self.assertRaises(Task.DoesNotExist, Task.objects.get, pk=task_pk)
        self.assertEqual(
            self.chrome_driver.current_url,
            self.live_server_url + reverse("todo:task-list"),
        )