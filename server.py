from pymongo import MongoClient

from util.request import Request
import string
from datetime import datetime, timezone, timedelta
import pymongo
import json
import html
import bcrypt
import secrets
import hashlib
from flask import Flask, jsonify, make_response, request
import flask
import os
from flask import request, send_file
from flask import Response
from flask import render_template
from markupsafe import escape

app = Flask(__name__)
# for easy switching between local and docker
# clientname = "mongo"
clientname = "localhost"
dbname = "cse312"


def add_no_sniff(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'


class OurDataBase:
    def __init__(self, client_name=clientname, db_name=dbname):
        self.clientname = client_name
        self.dbname = db_name
        self.mongo_client = pymongo.MongoClient(client_name)
        self.db = self.mongo_client[dbname]

    def __getitem__(self, key):
        return self.db[key] # changed by Zuhra to be able to add a new collection before_it_was->["key"]

    def close(self):
        self.mongo_client.close()


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


@app.get("/")
def site_root():
    resp = flask.Response()
    with open("./public/index.html", 'rb') as f:
        content = f.read()
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
    users = db.__getitem__("Users")
    # users = db["Users"]
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
    return resp


@app.post("/login")
def show_me_your_papers():
    req = flask.request
    resp = flask.Response()
    username = html.escape(req.form["username_login"])
    password = req.form["password_login"]
    db = OurDataBase()
    users = db.__getitem__("Users")
    # users = db["Users"]
    found_user = users.find_one({"username": username})
    if found_user is not None:
        hashed_pw = found_user["password"]
        bytess = password.encode('utf-8')
        check = bcrypt.checkpw(bytess, hashed_pw)
        if check:
            auth_token = create_token()
            hashed_token = hash_token(auth_token)
            expires = create_future_timestamp(3600 * 24)  # 1 day
            newvalues = {"$set": {"token": hashed_token, "expires": expires}}
            users.update_one({"username": username}, newvalues)
            resp.set_cookie('token', auth_token, max_age=3600*24)
            bodymessage = "Login successful!"
        else:
            bodymessage = "Incorrect username or password"
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
    db = OurDataBase()
    auth_token = flask.request.cookies.get('token')
    if auth_token is not None:
        token_hash = hash_token(auth_token)
        users = db.__getitem__("Users")
        # users = db["Users"]
        user = users.find_one({"token": token_hash})
        if user is not None:
            username = user["username"]
            return jsonify({"username": username}), 200

    return jsonify({"username": None}), 200

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
    description = html.escape(req.form.get("description"))

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


    # old one - juila
    # Save the post to the database
    # posts = db["Posts"]

    # Added by zuhra to create a new collection
    posts = db.__getitem__("Posts")

    posts.insert_one({
        "title": title,
        "description": description,
        "username": username
    })

    db.close()

    # Redirect to the home page after creating the post
    resp.status = 302
    resp.headers['Location'] = "/"
    return resp

@app.route("/chat-history", methods=["GET"])
def chat_history():
    db = OurDataBase()
    posts = db.__getitem__("Posts")
    existing_posts = list(posts.find({}, {'_id': 0}))

    return existing_posts, 200

# @app.route("/public/style.css")
# def style_path():
#     f = open("style.css", "r", encoding="utf-8")
#     g = f.read()
#     data = make_response(g)
#     data.headers["X-Content-Type-Options"] = "nosniff"
#     data.headers["Content-Type"] = "text/css;charset=utf-8"
#     return data
#
# @app.route("/public/functions.js")
# def functions_path():
#     f = open("functions.js", "r", encoding="utf-8")
#     g = f.read()
#     data = make_response(g)
#     data.headers["X-Content-Type-Options"] = "nosniff"
#     data.headers["Content-Type"] = "text/javascript; charset=utf-8"
#     return data


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
