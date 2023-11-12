let refreshInterval;

function chatMessageHTML(messageJSON,answerValue) {
    const usernameBtn = document.getElementById("username");
    const usernameText = usernameBtn.textContent;
    const usernameArr = usernameText.split(",");
    if (usernameArr.length >= 2) {
        const usernameValue = usernameArr[1].trim(); // Trim any whitespace
        if (usernameValue !== undefined) {
            username = usernameValue;
        }}
    const post_username = messageJSON.username;
    const title = messageJSON.title;
    const description = messageJSON.description;
    const answerMethod = messageJSON.answer_method;
    const post_id = messageJSON.post_id;
    const correctAnswers = messageJSON.correct_answers;
    const image_filename = messageJSON.image_filename;
    const submited_users = messageJSON.submited_users;
    let submited_usersArr = submited_users.slice(1).split(",");
    let datetime = new Date(messageJSON.time);
    let timeDiff = new Date() - datetime;
    let messageHTML = "";
    messageHTML += "<div class='post'>";
    messageHTML += "<h1>" + post_username + ":</h1>";
    messageHTML += "<h2>" + title + "</h2>";
    messageHTML += "<h4>" + description + "</h4>";
    if (image_filename !== "") {
        messageHTML += "<img class='post-image' src='" + image_filename + "'/>";
    }
    if (!submited_usersArr.includes(username)) {
        if (post_username !== username) {
            if (timeDiff / 1000 < 70) {
                messageHTML +=
                    "<h1 style='text-align: right;'> Time remaining : " +
                    Math.floor(timeDiff / 1000) +
                    "/70" +
                    "</h1>";
                if (answerMethod === "radio") {
                    const choice1 = messageJSON.choice1;
                    const choice2 = messageJSON.choice2;
                    const choice3 = messageJSON.choice3;
                    const choice4 = messageJSON.choice4;
                    messageHTML +=
                        "<form action='/answer' method='POST' enctype='multipart/form-data'>";
                    messageHTML +=
                        "<input type='hidden' name= 'post_id' value='" + post_id + "'>";
                    messageHTML += "<label>Select your Answer</label><br>";
                    if(answerValue == choice1){
                        messageHTML += "<input type=\"radio\" name=\"answer_text\" value=\"" +  choice1 +"\" checked >" + choice1 + "<br>"}
                    else{ messageHTML += "<input type=\"radio\" name=\"answer_text\" value=\"" +  choice1 +"\" checked >" + choice1 + "<br>"}
                    if(answerValue == choice2){
                        messageHTML += "<input type=\"radio\" name=\"answer_text\" value=\"" +  choice2 +"\" checked >" + choice2 + "<br>"}
                    else{ messageHTML += "<input type=\"radio\" name=\"answer_text\" value=\"" +  choice2 +"\" >" + choice2 + "<br>"}
                    if(answerValue == choice3){
                        messageHTML += "<input type=\"radio\" name=\"answer_text\" value=\"" +  choice3 +"\" checked >" + choice3 + "<br>"}
                    else{ messageHTML += "<input type=\"radio\" name=\"answer_text\" value=\"" +  choice3 +"\" >" + choice3 + "<br>"}
                    if(answerValue == choice4){
                        messageHTML += "<input type=\"radio\" name=\"answer_text\" value=\"" +  choice4 +"\" checked >" + choice4 + "<br>"}
                    else{ messageHTML += "<input type=\"radio\" name=\"answer_text\" value=\"" +  choice4 +"\" >" + choice4 + "<br>"}
                    messageHTML += "<input type='submit'>";
                    messageHTML += "</form>";
                } else {
                    messageHTML +=
                        "<form action='/answer' method='POST' enctype='multipart/form-data'>";
                    messageHTML +=
                        "<input type='hidden' name= 'post_id' value='" + post_id + "'>";
                    messageHTML += "<label>Type your Answer</label><br>";
                    messageHTML +=
                        "<input type='text' name='answer_text' required value='" + answerValue + "'>";
                    messageHTML += "<input type='submit'>";
                    messageHTML += "</form>";
                }
            }
        }
    }
    messageHTML += "</div>";
    return messageHTML;
}

function clearChat() {
    const chatMessages = document.getElementById("chat_box");
    chatMessages.innerHTML = "";
}

function addMessageToChat(messageJSON) {
    const chatMessages = document.getElementById("chat_box");
    const post_id = messageJSON.post_id;
    const answerValue = localStorage.getItem(`post-${post_id}-answer`);
    chatMessages.innerHTML += chatMessageHTML(messageJSON,answerValue);
}

function updateChat() {
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            const forms = document.querySelectorAll('form[action="/answer"]');
            forms.forEach(form => {
                const post_id = form.querySelector('input[name="post_id"]').value;
                const input = form.querySelector('input[name="answer_text"]:checked') || form.querySelector('input[name="answer_text"][type="text"]');
                localStorage.setItem(`post-${post_id}-answer`, input.value);});
            clearChat();
            const messages = JSON.parse(this.response);
            for (const message of messages) {
                addMessageToChat(message);
            }
        }
    };
    request.open("GET", "/chat-history");
    request.send();
}

function getUserName() {
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            const username = JSON.parse(this.responseText).username;
            document.getElementById("username").innerText = `Welcome,${username}`;
        }
    };
    request.open("GET", "/get-username");
    request.setRequestHeader("X-Content-Type-Options", "nosniff");
    request.send();
}

function welcome() {
    document.addEventListener("keypress", function (event) {
        if (event.code === "Enter") {
            sendChat();
        }
    });
    document.getElementById("paragraph").innerHTML += "<br/>You Social Media Feed! 😀";
    getUserName();
    updateChat();
}