from django.test import TestCase
from django.test import SimpleTestCase

from django.urls import reverse
from django.http import HttpResponse
from django.utils import timezone

from .models import Task
from .forms import DateTimeLocalInput
from .forms import TaskDetailForm

from typing import List
from typing import Sequence
from typing import Optional

from bs4 import BeautifulSoup
from bs4 import Tag
from bs4 import ResultSet


class ViewTests(TestCase):
    """Base class for testing views."""
    view_name: str


    def get_view_response(self, *, args: Sequence=()) -> HttpResponse:
        """Get an HttpResponse for the view."""
        return self.client.get(reverse(self.view_name, args=args))


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
            tasks.append(Task.objects.create(title=f"Task {i}"))
        
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
            checkbox: Tag = soup.select(f"input#task-{task.id}-checkbox")[0]
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
        response: HttpResponse = self.get_view_response(args=(0,))
        self.assertEqual(response.status_code, 404)
        
    
    def test_completed_and_incomplete_tasks(self) -> None:
        """
        Test that a task's title is shown in a textarea, its completed status
        is shown with a checkbox, its due_date is shown in a datetime field,
        and its description is shown in a textarea.

        This is done with both a complete and an incomplete task to test that
        the checkbox indicating completion is correct in both cases.
        """
        completed_task: Task = Task.objects.create(
            title="Completed task",
            completed=True,
            due_date=timezone.make_aware(timezone.datetime(2023, 3, 3, 5, 5)),
            description="This is a completed task.",
        )
        incomplete_task: Task = Task.objects.create(
            title="Incomplete task",
            completed=True,
            due_date=timezone.make_aware(timezone.datetime(2020, 6, 1, 1, 55)),
            description="This is an incomplete task.",
        )

        for task in completed_task, incomplete_task:
            response: HttpResponse = self.get_view_response(args=(task.pk,))
            self.assertEqual(response.status_code, 200)
            soup: BeautifulSoup = BeautifulSoup(response.content, "lxml")
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
            self.assertEqual(description_string, task.description)


class TaskDetailViewPostTests(ViewTests):
    """Tests for the task detail view with POST requests."""
    view_name = "todo:task-detail"


    def test_returns_404_for_nonexistent_task(self) -> None:
        """
        Test that the view returns a 404 not found for a nonexistent task.
        """
        data = TaskDetailForm(instance=Task(title="Test task")).data
        response = self.client.post(
            reverse(self.view_name, args=(1,)),
            data,
        )
        self.assertEqual(response.status_code, 404)


    def test_returns_redirect_for_existing_task(self) -> None:
        """Test that the view returns an HTTP redirect for an existing task."""
        task: Task = Task.objects.create(title="Task")
        self.assertRedirects(
            self.client.post(reverse(self.view_name, args=(task.pk,))),
            reverse(self.view_name, args=(task.pk,)),
            target_status_code=200,
        )
