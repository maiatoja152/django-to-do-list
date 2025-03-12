"use strict";

function createTask(title) {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/create-task", true);
    xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    xhr.setRequestHeader("X-CSRFToken", CSRF_TOKEN)
    xhr.onreadystatechange = () => {
        if (xhr.readyState === XMLHttpRequest.DONE && xhr.status === 201) {
            window.location.reload();
        }
    };
    xhr.send("title=" + title);
}

const taskTitleTextarea = document.querySelector("textarea.task-title");
taskTitleTextarea.addEventListener("keyup", ({key}) => {
    if (key === "Enter") {
        createTask(taskTitleTextarea.value);
    }
});