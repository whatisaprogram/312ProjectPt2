let refreshInterval;
let countdownIntervals = {}; // Store intervals for each post
var socket = null;


// Function to generate HTML for a new chat message
function chatMessageHTML(messageJSON) {
    // Extracting details from the message
    const post_username = messageJSON.username;
    const title = messageJSON.title;
    const description = messageJSON.description;
    const post_id = messageJSON.post_id;
    const endTime = new Date(messageJSON.endTime); // Assuming endTime is sent as a Date string

    let messageHTML = "";
    messageHTML += "<div class='post' id='post_" + post_id + "'>";
    messageHTML += "<h1>" + post_username + ":</h1>";
    messageHTML += "<h2>" + title + "</h2>";
    messageHTML += "<h4>" + description + "</h4>";
    messageHTML += "<h1 style='text-align: right;' id='timer_" + post_id + "'> Time remaining: </h1>";
    messageHTML += "</div>";

    return messageHTML;
}




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
        document.getElementById("username");
        const usernamei = usernameBtn.textContent.trim();
        console.log("post user",post_username)
        console.log('user',usernamei)
        if (post_username !== usernamei) {
                  messageHTML += "<div id='answer_section_" + post_id + "'>";

           
                messageHTML += "<h1 style='text-align: right;' id='timer_" + post_id + "'> Time remaining : </h1>";

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
    messageHTML += "</div>";
    messageHTML += "</div>";
    return messageHTML;
}


function updateCountdown(post_id, end_time){
    // Clear existing interval for this post if it exists
    if (countdownIntervals[post_id]) {
        clearInterval(countdownIntervals[post_id]);
    }

    // Start new countdown
    countdownIntervals[post_id] = setInterval(function() {
        let current_time = Math.floor(Date.now() / 1000);
        let remaining = end_time - current_time;
        console.log('current is');
        console.log(current_time);
        console.log("remaining",remaining)
        if (remaining >= 0) {
            let timerElement = document.getElementById('timer_' + post_id);
            if (timerElement) {
                timerElement.innerHTML = "Time remaining: " + remaining;
            }
        } else {
            clearInterval(countdownIntervals[post_id]);
            let timerElement = document.getElementById('answer_section_' + post_id);
            if (timerElement) {
                timerElement.innerHTML = "Time is up";
            }
        }
    }, 1000);
}


function addMessageToChat(messageJSON) {
    const chatMessages = document.getElementById("chat_box");
    const post_id = messageJSON.post_id;
    const answerValue = localStorage.getItem(`post-${post_id}-answer`);

    chatMessages.innerHTML += chatMessageHTML(messageJSON, answerValue);
}


function clearChat() {
    const chatMessages = document.getElementById("chat_box");
    chatMessages.innerHTML = "";
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
            document.getElementById("username").innerText = `${username}`;
        }
    };
    request.open("GET", "/get-username");
    request.setRequestHeader("X-Content-Type-Options", "nosniff");
    request.send();
}
function getUserName2() {
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            const username = JSON.parse(this.responseText).username;
            document.getElementById("username2").innerText = `${username}`;
        }
    };
    request.open("GET", "/get-username");
    request.setRequestHeader("X-Content-Type-Options", "nosniff");
    request.send();
}

function updateVerificationStatus() {
    fetch('/api/verification-status')
        .then(response => response.json())
        .then(data => {
            const statusElement = document.getElementById('verification-text');
            if (data.is_verified) {
                statusElement.innerText = 'Verified';
            } else {
                statusElement.innerText = 'Not Verified';
                
                document.getElementById('verify-email-link').style.display = 'inline';
                
            }
        });
}

document.addEventListener('DOMContentLoaded', function() {
    // Attach the event listener to the "Verify Email" link
    const verifyEmailLink = document.getElementById('verify-email-link');
    if (verifyEmailLink) {
        verifyEmailLink.addEventListener('click', sendVerificationEmail);
    }
});

function sendVerificationEmail(event) {
    event.preventDefault(); // Prevent the default link behavior

    fetch('/send-verification-email', { 
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (response.ok) {
            alert('Verification email sent! Please check your inbox.');
        } else {
            response.json().then(data => {
                alert(data.message || 'Error sending verification email.');
            });
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while sending verification email.');
    });
}

function welcome() {
    updateVerificationStatus();
    const verifyEmailLink = document.getElementById('verify-email-link');
    if (verifyEmailLink) {
        verifyEmailLink.addEventListener('click', sendVerificationEmail);
    }


    socket = io({ transports: ['websocket'] });
    socket.on('connect', function () {
        console.log("socketio connected");
    });

    socket.on("data", (data) => {
        console.log("received data");
    });

    socket.on('new_post', function(messageJSON) {
        addMessageToChat(messageJSON);
    });

    socket.on('update_remaining_time', function(data) {
        let timeDict = JSON.parse(data);

        for (let post_id in timeDict) {
            if (timeDict.hasOwnProperty(post_id)) {
                let end_time = timeDict[post_id];
                updateCountdown(post_id, end_time);
                console.log("endTime",end_time)
            }
        }
    });

    document.addEventListener("keypress", function (event) {
        if (event.code === "Enter") {
            sendChat();
        }
    });

    //document.getElementById("paragraph").innerHTML += "<br/>Your Social Media Feed! 😀";
    getUserName();
    getUserName2();
    updateChat();
}

welcome();