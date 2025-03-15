"use strict";

function deleteTask(taskPrimaryKey) {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/delete-task/" + taskPrimaryKey.toString(), true)
    xhr.setRequestHeader("X-CSRFToken", CSRF_TOKEN);
    xhr.onreadystatechange = () => {
        if (xhr.readyState === XMLHttpRequest.DONE && xhr.status === 200) {
            window.location.replace("/")
        }
    }
    xhr.send()
}

const deleteButton = document.querySelector(
    "button.task-detail-delete-button"
);
deleteButton.addEventListener("click", () => {
        deleteTask(deleteButton.dataset.taskPk);
});