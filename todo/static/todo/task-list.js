"use strict";

function send_post_request(path, dataObject, doneStatusCode, onDone) {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", path, true);
    xhr.setRequestHeader("X-CSRFToken", CSRF_TOKEN);
    xhr.onreadystatechange = () => {
        if (xhr.readyState === XMLHttpRequest.DONE && xhr.status === doneStatusCode) {
            onDone();
        }
    };
    xhr.send(JSON.stringify(dataObject));
}

function createTask(dataObject) {
    send_post_request(
        "/api/create-task",
        dataObject,
        201,
        () => { window.location.reload(); },
    );
}

function editTaskCompleted(taskPrimaryKey, completed) {
    send_post_request(
        "api/edit-task-completed/" + taskPrimaryKey.toString(),
        { completed: completed },
        200,
        () => {},
    );
}

const taskTitleTextarea = document.querySelector("textarea.task-title");
taskTitleTextarea.addEventListener("keyup", ({key}) => {
    if (key === "Enter") {
        createTask({ title: taskTitleTextarea.value });
    }
});

const taskListCheckboxes = document.querySelectorAll("input.task-list-checkbox")
for (const checkbox of taskListCheckboxes) {
    checkbox.addEventListener("change", () => {
        editTaskCompleted(
            checkbox.dataset.taskPk,
            checkbox.checked,
        );
    });
}