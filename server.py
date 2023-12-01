from util.request import Request
import string
from datetime import datetime, timezone, timedelta
import pymongo
import json
import html
import bcrypt
import secrets
import hashlib
from flask import Flask, jsonify, make_response, request, session, copy_current_request_context
import flask
import os
from flask import request, send_file
from flask import Response
from flask import render_template
from markupsafe import escape
from werkzeug.utils import secure_filename
from database import OurDataBase
from flask_socketio import SocketIO, emit, send
from util.increment_question_id import add_question, get_all_questions
from util.answer_handling import check_answer
import time
import secrets
from itsdangerous import URLSafeTimedSerializer
from flask import url_for
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from dotenv import load_dotenv
load_dotenv()

#withemailverificationss
app = Flask(__name__)
mail =Mail(app)

#########################################################################################################
#########################################################################################################
#IP Blocking/New content for Obj 3 starts here

IP_counts = {}
IP_timers = {}

@app.before_request
def ip_check():
    ip = request.headers.get('X-Actual-IP', 0)
    current_time = int(time.time())
    if ip != 0:
        known = IP_counts.get(str(ip), 0)
        if known == 0:
            IP_counts[ip] = 1
            IP_timers[ip] = [int(time.time()) + 10, 0]
        else:
            IP_counts[ip] += 1

        #If IP is blocked then we send error request
        if IP_timers[ip][1] != 0 and time.time() <= IP_timers[ip][1]:
            resp = make_response("You have sent too many requests, try again after 30 seconds")
            resp.status = "429 Too Many Requests"
            return resp

        #if block ends then reset
        if IP_timers[ip][1] != 0 and current_time > IP_timers[ip][1]:
            IP_counts[ip] = 0
            IP_timers[ip] = [int(time.time()), 0]

        #If more than 50 requests have been made in 10s, block and send error request else reset
        if IP_timers[ip][0] != 0 and current_time <= IP_timers[ip][0] and IP_counts[ip] >= 50:
            IP_timers[ip] = [0, int(time.time()) + 30]
            resp = make_response("You have sent too many requests, try again after 30 seconds")
            resp.status = "429 Too Many Requests"
            return resp
        elif IP_timers[ip][0] != 0 and current_time > IP_timers[ip][0]:
            IP_counts[ip] = 0
            IP_timers[ip] = [int(time.time()) + 10, 0]

#IP Blocking/New content for Obj 3 ends here
#########################################################################################################
#########################################################################################################

# emailverification
def generate_secret_key(length=80):
    return secrets.token_hex(length)

app.config['SECRET_KEY'] = generate_secret_key()

serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

def generate_verification_token(email):
    return serializer.dumps(email, salt='email-confirmation')


app.config['SENDGRID_API_KEY'] = os.getenv('api_key')
app.config['FROM_EMAIL'] = 'topquiz012@gmail.com'

def send_verification_email(email, username):
    token = generate_verification_token(email)
    print("emaiiiil token",token)
    db = OurDataBase()
    users = db["Users"]
    username=user_authenticated()
       

    users.update_one({"username": username}, {"$set": {"email_token": token}}, upsert=False)

    print("usernamemm",username)

    confirm_url = url_for('confirm_email', token=token, _external=True)
    confirm_url = confirm_url.replace("127.0.0.1:8080", os.getenv('SERVER_NAME'))
    

    from_email = Email(app.config['FROM_EMAIL'])  # Use the Email class
    to_email = To(email)  # Use the To class
    print("from email",from_email)
    subject = 'Email Verification'
    content = Content('text/html', f'Hello {username},<br>Please click on the link to verify your email: <a href="{confirm_url}">{confirm_url}</a>')

    message = Mail(from_email, to_email, subject, content)

    try:
        sg = SendGridAPIClient(app.config['SENDGRID_API_KEY'])
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(str(e))


@app.route('/send-verification-email', methods=['POST'])
def send_verification_email_route():
    user = user_authenticated()
    if user:
        db = OurDataBase()
        users = db["Users"]
        user_data = users.find_one({"username": user})
        if user_data and not user_data.get("email_confirmed"):
            email = user_data['email']
            print("sent to",email)
            # call the function to send the verification email
            send_verification_email(email, user)
            db.close()
            return jsonify({"status": "success"}), 200
        db.close()
    return jsonify({"status": "error"}), 400


@app.route('/confirm_email/<token>')
def confirm_email(token):
    print("email token", token)
    db = OurDataBase()
    users = db["Users"]
    
    # db = OurDataBase()
    # users = db["Users"]
    username=user_authenticated()
       

    users.update_one({"email_token": token}, {"$set": {"email_confirmed": True}}, upsert=False)
    print("usernamemm",username)
    
    return "Email confirmed"
#--------------------------------------------------------

app.secret_key = "secret key"
UPLOAD_FOLDER = 'public/image/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*", transports=['websocket'])  # Socket IO Initialization

@socketio.on('connect')
def connect():
    db = OurDataBase()
    posts = db["Posts"]
    data=posts.find({})
    timeDic={}
    for record in data:
        times = record['end_time']
        id=record['post_id']
        timeDic[id]=times
    time.sleep(1)

    socketio.emit('update_remaining_time', json.dumps(timeDic))

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
        if user is not None:
            return user["username"]
    return None

@app.get("/")
def site_root():
    user = user_authenticated()
    if user:  # If user is authenticated
        # Redirect to a dashboard or main page
        response = flask.redirect("/dashboard")
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

@app.route("/api/verification-status")
def api_verification_status():
    user = user_authenticated()
    if user:
        db = OurDataBase()
        users = db["Users"]
        user_data = users.find_one({"username": user})
        db.close()
        if user_data:
            is_verified = user_data.get("email_confirmed", False)
            return jsonify({"is_verified": is_verified})
    return jsonify({"is_verified": False})

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
    email=req.form["email_reg"]
    db = OurDataBase()
    users = db["Users"]
    found_user = users.find_one({"username": username})
    if found_user is None:
        bytess = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_salted = bcrypt.hashpw(bytess, salt)
        users.insert_one({"username": username, "password": hashed_salted, 'email_confirmed':False, 'email':email, 'email_token':None})
        bodymessage = "Successfully created " + username + "!"
    else:
        bodymessage = username + " is already taken!"
    db.close()
    add_no_sniff(resp)
    resp.status = 301
    resp.data = bodymessage
    resp.headers['Content-Type'] = "text/plain"
    resp.headers['Location'] = "/"

    #Obj3 create gradebook database
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
            "end_time": int(time.time())+70,
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
            "end_time": int(time.time()) + 70,
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
    ans = html.escape(req.form.get("answer_text"))
    post_id = req.form.get("post_id")
    print("post_idpost_idpost_idpost_id", post_id)
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
    old_value = posts.find_one({"post_id": post_id})["submited_users"]
    new_data = {"$set": {"submited_users": old_value + "," + username}}
    # create a unique post ID
    posts.update_one({"post_id": post_id}, new_data)
    db.close()

    #print("Is this it? ", req.form.get("answer_text"))

    # Check answer and mark in the gradebook the user's grade
    db = OurDataBase()
    #toRet = {"success": check_answer(post_id, req.form.get("answer_text"), username, db)}
    grades = db["Gradebook"].find_one({"User": username})
    grades = grades["Questions"]
    grades[str(post_id)] = 0
    db["Gradebook"].update_one({"User": username}, {"$set": {"Questions": grades}})
    if check_answer(post_id, ans, username, db):
        print("Gave 1")
        grades[str(post_id)] = 1
        db["Gradebook"].update_one({"User": username}, {"$set": {"Questions": grades}})
    test = db["Gradebook"].find({})
    for i in test:
        print(i)
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
        socketio.emit('auth',True, namespace='/answers')

    @socketio.on('new answer', namespace='/answers')
    def handle_new_answer():
        emit('new answer',broadcast=True)

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

#Making separate page for gradebook for Obj3
@app.route("/gradebook")
def gradebook():
    user = user_authenticated()
    answered = []
    if user:
        db = OurDataBase()
        questions = get_all_questions(db)
        grades = db["Gradebook"].find_one({"User": user})
        grades = grades["Questions"]
        for i in questions:
            if grades.get(str(i["post_id"]), -1) != -1:
                answered.append([i, str(grades[str(i["post_id"])]) + "/1"])
        db.close()
    return render_template("gradebook.html", user=user, questions=answered)

#Making separate page for admin gradebook for Obj3
@app.route("/admin_gradebook")
def admin_gradebook():
    user = user_authenticated()
    answered = []
    if user:
        db = OurDataBase()
        questions = get_all_questions(db)
        for i in questions:
            grades = db["Gradebook"].find({})
            total = 0
            actual = 0
            if user == i["username"]:
                for x in grades:
                    temp = x["Questions"]
                    print(temp)
                    if temp.get(str(i["post_id"]), -1) != -1:
                        total += 1
                        actual += int(temp[str(i["post_id"])])
                print("total: ", total, "actual: ", actual)
                answered.append([i, str(actual) + "/" + str(total)])
        db.close()
    return render_template("admin_gradebook.html", user=user, questions=answered)
@app.route("/grades")
def grade():
    user = user_authenticated()
    with open("./public/grades.html", 'rb') as f:
        content = f.read()
    resp = flask.Response()
    resp.data = content
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    return resp

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
