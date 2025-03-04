from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpRequest

from .models import Task


def task_list(request: HttpRequest) -> HttpResponse:
    return render(request, "todo/task-list.html", {"task_list": Task.objects.all()})