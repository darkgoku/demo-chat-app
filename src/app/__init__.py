from flask import Flask, redirect, render_template, request, session, url_for
from flask_socketio import SocketIO, join_room

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"
socketio = SocketIO(app)

all_messages = dict()


@app.route("/", methods=["GET", "POST"])
def get_room_form():
    if request.method == "GET":
        return render_template("join_room.html")

    session["username"] = request.form["username"]
    session["code"] = request.form["code"]
    session.modified = True

    all_messages[request.form["code"]] = all_messages.get(request.form["code"], [])

    return redirect(url_for("room"))


@app.route("/room")
def room():
    return render_template("room.html", code=session["code"])


@socketio.on("new_message")
def new_message(message, methods=["GET", "POST"]):
    code = session["code"]
    all_messages[code].append(
        {"username": session["username"], "message": message,}
    )
    socketio.emit("message_recieved", all_messages[code], room=code)


@socketio.on("connect")
def on_connect(*args):
    room = session["code"]
    join_room(room)
    socketio.emit("message_recieved", all_messages.get(room, []), room=request.sid)
