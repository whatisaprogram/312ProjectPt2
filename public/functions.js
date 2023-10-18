function deleteMessage(messageId) {
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            console.log(this.response);
        }
    }
    request.open("DELETE", "/chat-message/" + messageId);
    request.send();
}

function chatMessageHTML(messageJSON) {
    const username = messageJSON.username;
    const title = messageJSON.title;
    const description = messageJSON.description
    const messageId = messageJSON.id;
    const likes = messageJSON.total;
    const postId = messageJSON.post_id;
    let messageHTML = "<br><button onclick='deleteMessage(\"" + messageId + "\")'>X</button> ";
    messageHTML += "<span id='message_" + messageId + "'><strong>" + username + "</strong>" + ": " + "<strong>" + " Title: " + "</strong>" + title + "<strong>" + " Description: " + "</strong>" + description +
        "<button id= 'like_button' class='button_like' onclick='like(\"" + postId + "\", " + likes + ")'>Like</button>" + "<div id= like>" + likes + "</div>" + "</span>";
    return messageHTML;
}

function clearChat() {
    const chatMessages = document.getElementById("chat_box");
    chatMessages.innerHTML = "";
}

function addMessageToChat(messageJSON) {
    const chatMessages = document.getElementById("chat_box");
    chatMessages.innerHTML += chatMessageHTML(messageJSON);
    chatMessages.scrollIntoView(false);
    chatMessages.scrollTop = chatMessages.scrollHeight - chatMessages.clientHeight;
}

function sendChat() {
    const chatTextBox = document.getElementById("chat-text-box");
    const message = chatTextBox.value;
    chatTextBox.value = "";
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            console.log(this.response);
        }
    }
    const messageJSON = { "message": message };
    request.open("POST", "/chat-message");
    request.send(JSON.stringify(messageJSON));
    chatTextBox.focus();
}

function updateChat() {
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            clearChat();
            const messages = JSON.parse(this.response);
            for (const message of messages) {
                addMessageToChat(message);
            }
        }
    }
    request.open("GET", "/chat-history");
    request.send();
}

function getUserName() {
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            console.log('getUserName response: ', this.responseText);
            const username = JSON.parse(this.responseText).username;
            document.getElementById("username").innerText = `Welcome, ${username}!`;
        }
    }
    request.open("GET", "/get-username");
    request.send();
}


// Not needed - by Zuhra
// function fetchAndDisplayExistingPosts() {
//     const request = new XMLHttpRequest();
//     request.onreadystatechange = function () {
//         if (this.readyState === 4) {
//             const existingPosts = JSON.parse(this.response);
//             displayExistingPosts(existingPosts);
//         }
//     }
//     request.open("GET", "/get-existing-posts");
//     request.send();
// }
//
// function displayExistingPosts(existingPosts) {
//     const postContainer = document.getElementById("post-container");
//
//     // Iterate through existing posts and append them to the page
//     postContainer.forEach(function (post) {
//         appendPostToContainer(post);
//     });
// }

var history = {};

function like(postId, like_count) {
    var count = 0
    if (!(postId in history)){
        history[postId] = false;
    }
    if (history[postId] === false){
        count = "1"
        history[postId] = true;
    }
    else{
        count = "0"
        history[postId] = false;
    }
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            console.log("Pressed Like Button")
        }
    }
    const likes = {"like" : count, "post_id": postId, "total": like_count};
    request.open("POST", "/like");
    request.setRequestHeader("Content-Type", "application/json");
    request.send(JSON.stringify(likes));
}

function welcome() {
    document.addEventListener("keypress", function (event) {
        if (event.code === "Enter") {
            sendChat();
        }
    });

    document.getElementById("paragraph").innerHTML += "<br/>You Social Media Feed! 😀";
    // document.getElementById("chat-text-box").focus();

    getUserName();
    updateChat();
    setInterval(updateChat, 2000);
}


