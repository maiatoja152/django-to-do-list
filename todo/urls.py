from django.urls import path

from . import views


app_name = "todo"
urlpatterns = [
    path("", views.task_list, name="task-list"),
    path("task/<int:pk>", views.task_detail, name="task-detail"),
    path("api/edit-task/<int:pk>", views.edit_task, name="edit-task"),
]