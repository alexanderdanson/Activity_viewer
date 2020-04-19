//let xhr = new XMLHttpRequest();
//xhr.open('get', '/total_distance_per_activity/1');
//xhr.send();

//xhr.onload = function() {
//    console.log(xhr.response);
//};

fetch('/total_distance_per_activity/1')
    .then(response => response.json())
    .then(json => console.log(json));
