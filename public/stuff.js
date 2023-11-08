let url = null;
function uploadImage(){
    let image = document.getElementById("form-file");
    image = image.files;
    let toRet = {};
    let formData = new FormData();
    formData.append('image', image[0]);
    fetch('/upload', {
        method: 'POST',
        body: formData,
    })
    .then((response) => {
        return response.json()
    }).then(response => {
        toRet = response;
        url = toRet["url"];
        let currentImage = document.getElementById("current-image");
        currentImage.innerHTML = "<img src=\""+url+"\">";
        return false;
    }).catch(error => {
        console.error(":((");
    });

}

function submitForm(){
    let title = document.getElementById("title").value;
    let description = document.getElementById("description").value;
    let method = document.getElementById("method").value;
    let answers = document.getElementById("answers").value;
    let imgurl = getUrl();
    let blob = JSON.stringify({"title": title, "description": description, "method": method, "answers": answers, "imgurl": imgurl});
    let json_blob = new Blob([blob], { type: 'application/json' });
    let the_response;
    fetch('/post-question', {
        method: 'POST',
        body: json_blob,
    }).then(response => {
        return response.ok? response.json() : console.log("error");
    }).then(response => {
        the_response = response;
        location.reload();
    }).catch(error => {
        console.error(error);
    });
    location.reload();
}

function submitAnswer(element){
    let the_id = element.parentNode.id.trim();
    the_id = the_id.slice(0, -1);
    let the_answer = element.parentNode.children[1].value
    let blob = JSON.stringify({"id": the_id, "answer" : the_answer});
    let json_blob = new Blob([blob], { type: 'application/json' });
    fetch('/post-answer', {
        method: "POST",
        body: json_blob,
    }).then(response => {
        return response.ok? response.json() : console.log("error");
    }).then(response => {
        let parent = element.parentNode
        let grandparent = parent.parentNode
        let messagebox = grandparent.getElementsByClassName("sweaty")[0]
        console.log(response);
        messagebox.innerHTML = response["success"]? "Correct! :)" : "Incorrect. Completely worthless!"
    }).catch(error => {
        console.error(error);
    });
    // document.getElementById("submit_answer").disabled=true
}

function getUrl(){
    if(url == null){
        url = "/public/image/kitten.jpg";
    }
    return url;
}

