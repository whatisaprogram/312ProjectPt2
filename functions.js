function welcome() {
    document.getElementById("paragraph").innerHTML += "<br/>CSE312 Project"
}
var pressed = false

function like() {
    var text = document.getElementById("like");
    if (pressed == false){
        text.innerHTML = (parseInt(text.innerHTML) + 1).toString()
        pressed = true
        document.getElementById("like_button").style.backgroundColor = "LawnGreen";
    }
    else{
        text.innerHTML = (parseInt(text.innerHTML) - 1).toString()
        pressed = false
        document.getElementById("like_button").style.backgroundColor = "LightGrey";
    }
}