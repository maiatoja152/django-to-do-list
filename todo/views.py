from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.http import HttpResponse
from django.http import HttpRequest
from django.http import HttpResponseRedirect

from .models import Task

from .forms import TaskEditForm


def task_list(request: HttpRequest) -> HttpResponse:
    return render(request, "todo/task-list.html", {"task_list": Task.objects.all()})


def task_detail(request: HttpRequest, pk: int) -> HttpResponse:
    task = get_object_or_404(Task, pk=pk)
    form: TaskEditForm = TaskEditForm(instance=task)
    context = {"task": task, "form": form}
    return render(request, "todo/task-detail.html", context)


def edit_task(request: HttpRequest, pk: int) -> HttpResponseRedirect:
    task = get_object_or_404(Task, pk=pk)
    return redirect(reverse("todo:task-detail", args=(pk,)))