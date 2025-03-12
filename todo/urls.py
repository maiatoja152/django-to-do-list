from django.urls import path

from . import views


app_name = "todo"
urlpatterns = [
    path("", views.task_list, name="task-list"),
    path("task/<int:pk>", views.task_detail, name="task-detail"),
    path("api/create-task", views.create_task, name="create-task"),
]