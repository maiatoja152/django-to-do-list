from django.db import models


class Task(models.Model):
    completed = models.BooleanField(
        help_text="Whether the task has been completed.",
        db_default=False,
    )
    title = models.TextField(
        help_text="The title of the task. (e.g. \"Do laundry\")",
    )
    description = models.TextField(
        help_text="A longer description of the task.",
        blank=True,
    )
    due_date = models.DateTimeField(
        help_text="The date and time at which the task is due for completion.",
        null=True,
    )

    def __str__(self) -> str:
        return str(self.title)
    

    def due_date_as_html_input_value(self) -> str:
        return self.due_date.strftime("%Y-%m-%dT%H:%M")
