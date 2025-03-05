from django.test import TestCase

from django.urls import reverse
from django.http import HttpResponse

from typing import List

from .models import Task

from bs4 import BeautifulSoup
from bs4 import Tag
from typing import Sequence


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
        soup: BeautifulSoup = BeautifulSoup(response.content)
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
        
    
    def test_task(self) -> None:
        """
        """
        pass