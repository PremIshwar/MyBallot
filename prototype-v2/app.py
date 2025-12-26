from flask import Flask, redirect, request, session, render_template, url_for
from urllib.parse import urlencode
import uuid

from crypto_utils import create_encrypted_signed_ballot

import win_joystick #Windows
#import joystick_listener #Raspi

app = Flask(__name__)

#Joystick Interface
win_joystick.start() #Windows
#joystick_listener.start() #Raspi
app.secret_key = "dev-secret-key"  

PERSONA_LINK = (
    "https://miniapp.withpersona.com/verify"
    "?inquiry-template-id=itmpl_i2BGeWpxqZfSoRR8d7LYQoQfwAJy"
    "&environment-id=env_jVvGECEUMVfz8qcVsjnAvXETSPMM"
)

#Welcome
@app.route("/")
def index():
    session.clear()
    return render_template("index.html")


#Start verification
@app.route("/verify")
def verify():
    redirect_uri = url_for("persona_callback", _external=True)
    return redirect(f"{PERSONA_LINK}&redirect-uri={redirect_uri}")


#Persona callback
@app.route("/callback")
def persona_callback():
    status = request.args.get("status", "").lower()

    first = request.args.get("fields[name-first][value]", "")
    last = request.args.get("fields[name-last][value]", "")
    id_number = request.args.get("fields[identification-number][value]", "")

    if status != "completed":
        return redirect(url_for("index"))

    session["voter"] = {
        "name": f"{first} {last}".strip(),
        "id_number": id_number,
        "status": status,
        "token": str(uuid.uuid4())
    }

    return redirect(url_for("vote"))


#Voting page
@app.route("/vote", methods=["GET", "POST"])
def vote():
    voter = session.get("voter")
    
    if request.method == "POST":
        choice = request.form.get("choice")
        packet = create_encrypted_signed_ballot(voter, choice)

        print("VOTE CAST")
        print("Name:", voter["name"])
        print("ID:", voter["id_number"])
        print("Choice:", choice)

        session["ballot_id"] = packet["envelope_meta"]["ballot_id"]
        return redirect(url_for("thankyou"))

    return render_template("vote.html", voter=voter)
            

#END
@app.route("/thankyou")
def thankyou():
    ballot_id = session.get("ballot_id")
    

    return render_template("thankyou.html", ballot_id="ballot_id")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
