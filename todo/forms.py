from django import forms

from .models import Task


class TaskDetailForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            "title",
            "completed",
            "due_date",
            "description",
        ]