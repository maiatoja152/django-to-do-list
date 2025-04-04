from django import forms

from .models import Task

from typing import Any
from typing import Optional
import re


class DateTimeLocalInput(forms.widgets.Input):
    input_type = "datetime-local"


    def format_value(self, value: Any) -> Optional[str]:
        value = super().format_value(value)
        if value is None:
            return None
        else:
            datetime_pattern: str = \
                r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2})(:\d{2})$"
            match: Optional[re.Match] = re.match(datetime_pattern, value)
            if match is None:
                return None
            else:
                return match[1]

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            "title",
            "completed",
            "due_date",
            "description",
        ]
        widgets = {
            "title": forms.Textarea(attrs={
                "class": "task-title margin-top",
                "rows": 1,
                "cols": 60
            }),
            "due_date": DateTimeLocalInput(),
            "description": forms.Textarea(attrs={"rows": 10, "cols": 60}),
        }