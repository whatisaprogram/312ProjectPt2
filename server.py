from flask import Flask, jsonify, make_response, request, session, copy_current_request_context
from database import OurDataBase
from flask_socketio import SocketIO, emit
from datetime import datetime, timezone, timedelta
import html
import bcrypt
import secrets
import hashlib
from flask import Flask, jsonify
import flask
from flask import request
from markupsafe import escape
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret key"
UPLOAD_FOLDER = 'public/image/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*",
                    transports=['websocket'])  # Socket IO Initialization


# for easy switching between local and docker
def add_no_sniff(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'


def hash_token(token_as_string):
    return hashlib.sha256(token_as_string.encode()).hexdigest()


def create_token(size=100):
    token = secrets.token_hex(size)
    return token


def create_future_timestamp(secs=3600):
    toRet = datetime.now(timezone.utc) + timedelta(seconds=3600)
    return toRet.timestamp()


def current_timestamp():
    return datetime.now(timezone.utc).timestamp()


# checks if the user is authenticated if not or user is not logged in then returns None
def user_authenticated():
    auth_token = flask.request.cookies.get('token')
    if auth_token is not None:
        db = OurDataBase()
        users = db["Users"]
        token_hash = hash_token(auth_token)
        user = users.find_one({"token": token_hash})
        if user is not None:  # wrong
            return user["username"]
    return None


@app.get("/")
def site_root():
    user = user_authenticated()
    if user:  # If user is authenticated
        # Redirect to a dashboard or main page
        response = flask.redirect("/dashboard") # wrong
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response
    else:  # If user is not authenticated, show the login page
        resp = flask.Response()
        with open("./public/login.html", 'rb') as f:
            content = f.read()
            resp.data = content
        resp.headers['Content-Type'] = 'text/html; charset=utf-8'
        resp.headers['X-Content-Type-Options'] = 'nosniff'
        return resp


@app.route("/guest")
def guest_login():
    resp = flask.redirect("/dashboard")
    add_no_sniff(resp)
    return resp


@app.route("/dashboard")
def dashboard():
    user = user_authenticated()
    with open("./public/index.html", 'rb') as f:
        content = f.read()
    resp = flask.Response()
    resp.data = content
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    return resp


@app.get("/public/<file>")
def send_static_file(file):
    exists = os.path.exists("./public/" + file)
    status = 200
    if not exists:
        content = "ERROR 404: FILE NOT FOUND"
        status = 404
    else:
        with open("./public/" + file, 'rb') as f:
            content = f.read()

    resp = flask.Response(status=status)
    resp.data = content
    resp.headers['X-Content-Type-Options'] = 'nosniff'

    if status != 200:
        return resp
    fileends = {"html": "text/html; charset = utf8",
                "css": "text/css; charset = utf8",
                "js": "text/javascript; charset = utf8",
                "png": "image/png",
                'jpg': 'image/jpeg',
                "": "text/plain"}
    contenttype = file.split(".")[-1]
    if contenttype in fileends:
        resp.headers['Content-Type'] = fileends[contenttype]
    return resp


@app.get("/public/image/<file>")
def send_image_file(file):
    exists = os.path.exists("./public/image/" + file)
    status = 200
    if not exists:
        content = "ERROR 404: FILE NOT FOUND"
        status = 404
    else:
        with open("./public/image/" + file, 'rb') as f:
            content = f.read()

    resp = flask.Response(status=status)
    resp.data = content
    resp.headers['X-Content-Type-Options'] = 'nosniff'

    if status != 200:
        return resp
    fileends = {"html": "text/html; charset = utf8",
                "css": "text/css; charset = utf8",
                "js": "text/javascript; charset = utf8",
                "png": "image/png",
                "": "text/plain"}
    contenttype = file.split(".")[-1]

    if contenttype in fileends:
        resp.headers['Content-Type'] = fileends[contenttype]
    return resp


@app.get("/visit-counter")
def welcome_to_the_jungle():
    resp = flask.Response()
    visits = request.cookies.get('visits', None)
    if visits is None:
        resp.set_cookie('visits', str(1))
        resp.data = str(1)
    else:
        try:
            visits = int(visits)
            resp.set_cookie('visits', str(visits + 1), max_age=3600)
            resp.data = str(visits + 1)
        except:
            resp = flask.Response(status=400)
            resp.data = "YOUR COOKIE IS BAD"

    resp.headers['X-Content-Type-Options'] = 'nosniff'
    resp.headers['Content-Type'] = "text/plain"
    return resp


@app.post("/register")
def join_us_spongebob():
    req = flask.request
    resp = flask.Response()
    username = html.escape(req.form["username_reg"])
    password = req.form["password_reg"]
    db = OurDataBase()
    users = db["Users"]
    found_user = users.find_one({"username": username})
    if found_user is None:
        bytess = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_salted = bcrypt.hashpw(bytess, salt)
        users.insert_one({"username": username, "password": hashed_salted})
        bodymessage = "Successfully created " + username + "!"
    else:
        bodymessage = username + " is already taken!"
    db.close()
    add_no_sniff(resp)
    resp.status = 301
    resp.data = bodymessage
    resp.headers['Content-Type'] = "text/plain"
    resp.headers['Location'] = "/"

    #For objective 3 make a collection for the registered users gradebook
    db = OurDataBase()
    grades = db.__getitem__("Gradebook")
    grades.insert_one({"User": username, "Questions": {}})
    db.close()
    return resp


@app.post("/login")
def show_me_your_papers():
    req = flask.request
    resp = flask.Response()
    username = html.escape(req.form["username_login"])
    password = req.form["password_login"]
    db = OurDataBase()
    users = db["Users"]
    found_user = users.find_one({"username": username})
    if found_user is not None:
        hashed_pw = found_user["password"]
        bytess = password.encode('utf-8')
        check = bcrypt.checkpw(bytess, hashed_pw)
        if check:  # Successful login
            auth_token = create_token()
            hashed_token = hash_token(auth_token)
            expires = create_future_timestamp(3600 * 24)  # 1 day
            newvalues = {"$set": {"token": hashed_token, "expires": expires}}
            users.update_one({"username": username}, newvalues)
            resp.set_cookie('token', auth_token, max_age=3600 * 24, httponly=True)
            bodymessage = "Login successful!"
            resp.headers['Location'] = "/dashboard"  # Redirect to a dashboard or main page after successful login
        else:
            bodymessage = "Incorrect username or password"
            resp.headers['Location'] = "/"
    else:
        bodymessage = "Incorrect username or password"

    db.close()
    add_no_sniff(resp)
    resp.status = 301
    resp.data = bodymessage
    resp.headers['Content-Type'] = "text/plain"
    resp.headers['Location'] = "/"
    return resp


@app.get("/get-username")
def get_username():
    auth_token = flask.request.cookies.get('token')
    if auth_token is not None:
        db = OurDataBase()
        users = db["Users"]
        token_hash = hash_token(auth_token)
        user = users.find_one({"token": token_hash})
        if user is not None:
            username = escape(user["username"])
            response = jsonify({"username": username})
            response.headers['X-Content-Type-Options'] = 'nosniff'
            return response, 200
    response = jsonify({"username": "Guest"})
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response, 200


@app.post("/create-post")
def create_post():
    req = flask.request
    resp = flask.Response()
    # Check if user is authenticated (has a valid token)
    auth_token = req.cookies.get('token')
    if auth_token is None:
        resp.status = 401  # Unauthorized
        resp.data = "You need to be logged in to create a post."
        return resp
    # Retrieve title and description from the form
    title = html.escape(req.form.get("title"))
    answer_method = html.escape(req.form.get("answer_method"))
    correct_answers = html.escape(req.form.get("correct_answers"))
    description = html.escape(req.form.get("description"))
    image = req.files['file']
    if not title or not description:
        resp.status = 400  # Bad request
        resp.data = "Title and description are required."
        return resp
    # Get the username of the authenticated user
    db = OurDataBase()
    users = db["Users"]
    token_hash = hash_token(auth_token)
    user = users.find_one({"token": token_hash})
    if user is None:
        db.close()
        resp.status = 401  # Unauthorized
        resp.data = "Invalid token. Please log in."
        return resp
    username = user["username"]
    posts = db["Posts"]
    # create a unique post ID
    post_id = str(posts.count_documents({}) + 1)
    # add post to database
    image_path = ""
    if image.filename != '':
        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        image_path = "public/image/" + filename
        print(image_path)
    if answer_method == "text":
        posts.insert_one({
            "title": title,
            "description": description,
            "username": username,
            "post_id": post_id,
            "answer_method": answer_method,
            "correct_answers": correct_answers,
            "image_filename": image_path,
            "time": datetime.now(),
            "submited_users": ""
        })
        db.close()
    else:
        choice1 = html.escape(req.form.get("choice1"))
        choice2 = html.escape(req.form.get("choice2"))
        choice3 = html.escape(req.form.get("choice3"))
        choice4 = html.escape(req.form.get("choice4"))
        posts.insert_one({
            "title": title,
            "description": description,
            "username": username,
            "post_id": post_id,
            "answer_method": answer_method,
            "correct_answers": correct_answers,
            "choice1": choice1,
            "choice2": choice2,
            "choice3": choice3,
            "choice4": choice4,
            "image_filename": image_path,
            "time": datetime.now(),
            "submited_users": ""
        })
        db.close()

    # Socket IO Events - New Post Creation
    @socketio.on('connect', namespace='/posts')
    def handle_connect():
        auth_token = request.cookies.get('token')
        if auth_token is None:
            socketio.disconnect()
            return
        # retrieve the username from the Flask-SocketIO session
        username = session.get('username')
        # If the session does not contain a username, the connection is unauthorized
        if not username:
            socketio.disconnect()
            return
        socketio.emit('auth', True, namespace='/posts')

    @socketio.on('new post', namespace='/posts')
    def handle_new_post():
        emit('new post', broadcast=True)

    socketio.emit('new post', namespace='/posts')
    # Redirect to the home page after creating the post
    resp.status = 302
    resp.headers['Location'] = "/"
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    return resp


@app.post("/answer")
def answer():
    req = flask.request
    resp = flask.Response()
    # Check if user is authenticated that has a valid token
    auth_token = req.cookies.get('token')
    if auth_token is None:
        resp.status = 401  # Unauthorized
        resp.data = "You need to be logged in to create a post."
        return resp
    answer = html.escape(req.form.get("answer_text"))
    post_id = req.form.get("post_id")
    print("post_idpost_idpost_idpost_id",post_id)
    # Get the username of the authenticated user
    db = OurDataBase()
    users = db["Users"]
    token_hash = hash_token(auth_token)
    user = users.find_one({"token": token_hash})
    if user is None:
        db.close()
        resp.status = 401  # Unauthorized
        resp.data = "Invalid token. Please log in."
        return resp

    username = user["username"]
    posts = db["Posts"]
    old_value = posts.find_one({"post_id":post_id})["submited_users"]
    new_data = {"$set": {"submited_users": old_value + "," + username}}
    # create a unique post ID
    posts.update_one({"post_id": post_id}, new_data)

    # # Updating Gradebook collection for Obj3
    # grades = db["Gradebook"].find_one({"User": user})
    # grades = grades["Questions"]
    # grades[str(data["id"])] = 0
    # db["Gradebook"].update_one({"User": user}, {"$set": {"Questions": grades}})
    # if check_answer(int(data["id"]), data["answer"], user, db):
    #     grades[str(data["id"])] = 1
    #     db["Gradebook"].update_one({"User": user}, {"$set": {"Questions": grades}})
    # # test = db["Gradebook"].find({})
    # # for i in test:
    # #    print(i)

    db.close()


    # Socket IO Events - New Answer Submission
    @socketio.on('connect', namespace='/answers')
    def handle_connect():
        auth_token = request.cookies.get('token')
        if auth_token is None:
            socketio.disconnect()
            return
        # Retrieve the username from the Flask-SocketIO session
        username = session.get('username')
        # If the session does not contain a username, the connection is unauthorized
        if not username:
            socketio.disconnect()
            return
        socketio.emit('auth', True, namespace='/answers')

    @socketio.on('new answer', namespace='/answers')
    def handle_new_answer():
        emit('new answer', broadcast=True)

        socketio.emit('new answer', namespace='/answers')
        # Redirect to the home page after creating the post
        resp.status = 302
        resp.headers['Location'] = "/"
        resp.headers['X-Content-Type-Options'] = 'nosniff'
        return resp


@app.route("/chat-history", methods=["GET"])
def chat_history():
    db = OurDataBase()
    posts = db["Posts"]
    existing_posts = list(posts.find({}, {"_id": 0}))
    db.close()
    return jsonify(existing_posts)

# Like for Obj3
@app.route("/like", methods=["POST"])
def like():
    data = request.get_json()
    current_like = data.get('like')
    post_id = data.get('post_id')
    # total = int(data.get('total'))
    response = flask.Response()
    db = OurDataBase()
    liked_status = db.__getitem__("Status")
    posts = db.__getitem__("Posts")
    total = posts.find_one({"post_id": post_id})
    total = int(total["total"])

    user = user_authenticated()
    if user is not None:
        status = liked_status.find_one({"username": user, "post_id": post_id})
        if status is None:
            liked_status.insert_one({"username": user, "status": "1", "post_id": post_id})
            status = liked_status.find_one({"username": user, "post_id": post_id})

        if current_like == "0" and status["status"] != "1":
            posts.update_one({"post_id": post_id}, {"$set": {"total": str(total - 1)}})
            liked_status.update_one({"username": user, "post_id": post_id}, {"$set": {"status": "1"}})

        elif current_like == "1" and status["status"] != "0":
            posts.update_one({"post_id": post_id}, {"$set": {"total": str(total + 1)}})
            liked_status.update_one({"username": user, "post_id": post_id}, {"$set": {"status": "0"}})

        elif current_like == "0" and status["status"] == "1":
            posts.update_one({"post_id": post_id}, {"$set": {"total": str(total + 1)}})
            liked_status.update_one({"username": user, "post_id": post_id}, {"$set": {"status": "0"}})

        elif current_like == "1" and status["status"] == "0":
            posts.update_one({"post_id": post_id}, {"$set": {"total": str(total - 1)}})
            liked_status.update_one({"username": user, "post_id": post_id}, {"$set": {"status": "1"}})

    response.status = 302
    response.headers['Location'] = "/"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    db.close()
    return response

@app.route("/logout")
def logout():
    auth_token = flask.request.cookies.get('token')
    if auth_token is not None:
        db = OurDataBase()
        users = db["Users"]
        token_hash = hash_token(auth_token)
        users.update_one({"token": token_hash}, {"$set": {"token": None, "expires": current_timestamp()}}, upsert=False)
        db.close()
    resp = flask.redirect("/")
    resp.delete_cookie('token')
    return resp


if __name__ == "__main__":
    # Socket IO run initialization with app and port being passed.
    socketio.run(app, host="0.0.0.0", port=8080, debug=False)
