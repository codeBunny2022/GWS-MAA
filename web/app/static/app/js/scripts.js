document.addEventListener('DOMContentLoaded', function () {
    const taskForm = document.getElementById('task-form');
    const responseData = document.getElementById('response-data');

    taskForm.addEventListener('submit', function (event) {
        event.preventDefault();
        
        const formData = new FormData(taskForm);
        let jsonData = {};
        formData.forEach((value, key) => {
            jsonData[key] = value;
        });

        fetch('/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(jsonData)
        })
        .then(response => response.json())
        .then(data => {
            responseData.textContent = JSON.stringify(data, null, 2);
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });
});

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}