"use strict";

function objectToUrlEncoded(dataObject) {
    let encoded = "";
    for (const [key, value] of Object.entries(dataObject)) {
        encoded += `${key}=${value}&`;
    }
    return encoded;
}

function send_post_request(path, dataObject, doneStatusCode, onDone) {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", path, true);
    xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    xhr.setRequestHeader("X-CSRFToken", CSRF_TOKEN);
    xhr.onreadystatechange = () => {
        if (xhr.readyState === XMLHttpRequest.DONE && xhr.status === doneStatusCode) {
            onDone();
        }
    };
    xhr.send(objectToUrlEncoded(dataObject));
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
        "/api/edit-task-completed/" + taskPrimaryKey.toString(),
        { completed: completed },
        200,
        () => {},
    );
}

const taskTitleTextarea = document.querySelector("textarea.task-title");
taskTitleTextarea.addEventListener("keyup", ({key}) => {
    if (key === "Enter") {
        if (taskTitleTextarea.value.length > 0) {
            createTask({ title: taskTitleTextarea.value });
        }
    }
});
const addTaskButton = document.querySelector("#add-task-button");
addTaskButton.addEventListener("click", () => {
    if (taskTitleTextarea.value.length > 0) {
        createTask({ title: taskTitleTextarea.value });
    }
});

const taskListCheckboxes = document.querySelectorAll("input.task-list-checkbox")
for (const checkbox of taskListCheckboxes) {
    checkbox.addEventListener("change", () => {
        editTaskCompleted(
            checkbox.parentNode.dataset.taskPk,
            checkbox.checked,
        );
    });
}