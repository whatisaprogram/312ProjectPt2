function welcome() {
    document.getElementById("paragraph").innerHTML += "<br/>CSE312 Project"
}


function like() {
    var text = document.getElementById("like");
    text.innerHTML = (parseInt(text.innerHTML) + 1).toString();
    document.getElementById("like_button").style.backgroundColor = "LawnGreen";
}