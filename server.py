from flask import Flask, make_response, request
app = Flask(__name__)
@app.route("/")
def full_page():
    f = open("index.html", "r", encoding="utf-8")
    g = f.read()
    data = make_response(g)
    data.headers["X-Content-Type-Options"] = "nosniff"
    data.headers["Content-Type"] = "text/html; charset=utf-8"
    return data

@app.route("/style.css")
def style_path():
    f = open("style.css", "r", encoding="utf-8")
    g = f.read()
    data = make_response(g)
    data.headers["X-Content-Type-Options"] = "nosniff"
    data.headers["Content-Type"] = "text/css; charset=utf-8"
    return data

@app.route("/functions.js")
def functions_path():
    f = open("functions.js", "r", encoding="utf-8")
    g = f.read()
    data = make_response(g)
    data.headers["X-Content-Type-Options"] = "nosniff"
    data.headers["Content-Type"] = "text/javascript; charset=utf-8"
    return data

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)