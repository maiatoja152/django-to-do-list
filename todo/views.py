from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.http import HttpResponse
from django.http import HttpRequest
from django.http import HttpResponseNotAllowed
from django.http import HttpResponseBadRequest

from .models import Task

from .forms import TaskForm


def task_list(request: HttpRequest) -> HttpResponse:
    return render(request, "todo/task-list.html", {"task_list": Task.objects.all()})


def task_detail(request: HttpRequest, pk: int) -> HttpResponse:
    task: Task = get_object_or_404(Task, pk=pk)

    form: TaskForm
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect(reverse("todo:task-detail", args=(pk,)))
    else:
        form = TaskForm(instance=task)

    context = {"task_title": task.title, "form": form}
    return render(request, "todo/task-detail.html", context)


def create_task(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseNotAllowed(("POST",))
    
    if "title" in request.POST:
        Task.objects.create(title=request.POST["title"])
        return HttpResponse(status=201)
    else:
        return HttpResponseBadRequest("title is required.")