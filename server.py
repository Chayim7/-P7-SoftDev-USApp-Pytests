from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, session, url_for

from provider import get_clubs, get_competitions

app = Flask(__name__)
# You should change the secret key in production!
app.secret_key = "something_special"


@app.route("/")
def index():
    """Homepage"""
    return render_template("index.html")


@app.route("/login", methods=["POST"])
def login():
    """Use the session object to store the club information across requests"""

    clubs = get_clubs()
    email = request.form.get("email", "").strip()

    if not email:
        flash("Error: Please enter an email address.")
        return render_template("index.html"), 401

    matching_clubs = [item for item in clubs if item["email"] == email]

    if not matching_clubs:
        flash("Error: Email not found. Please check your email address.")
        return render_template("index.html"), 401

    club = matching_clubs[0]
    session["club"] = club

    return redirect(url_for("summary"))


@app.route("/summary")
def summary():
    """Custom "homepage" for logged in users"""

    club = session["club"]
    competitions = get_competitions()

    return render_template("welcome.html", club=club, competitions=competitions)


@app.route("/book/<competition>")
def book(competition):
    """Book spots in a competition page"""
    club = session["club"]

    competitions = get_competitions()
    matching_comps = [comp for comp in competitions if comp["name"] == competition]

    found_competition = matching_comps[0]

    if found_competition:
        return render_template("booking.html", club=club, competition=found_competition)
    else:
        flash("Something went wrong-please try again")
        return redirect(url_for("summary"))


@app.route("/book", methods=["POST"])
def book_spots():
    """This page is only accessible through a POST request (form validation)"""
    club = session["club"]
    competitions = get_competitions()

    matching_comps = [
        comp for comp in competitions if comp["name"] == request.form["competition"]
    ]

    competition = matching_comps[0]

    competition_date = datetime.strptime(competition["date"], "%Y-%m-%d %H:%M:%S")
    if competition_date < datetime.now():
        flash("Error: You cannot book spots in a past competition.")
        return render_template("welcome.html", club=club, competitions=competitions)

    spots_required = int(request.form["spots"])
    club_points = int(club["points"])
    max_spots_per_booking = 12

    if spots_required > max_spots_per_booking:
        flash("Error: You cannot book more than 12 spots per competition.")
        return render_template("welcome.html", club=club, competitions=competitions)

    if spots_required > club_points:
        flash("Error: You do not have enough points to book this many spots.")
        return render_template("welcome.html", club=club, competitions=competitions)

    competition["spotsAvailable"] = int(competition["spotsAvailable"]) - spots_required
    club["points"] = str(club_points - spots_required)
    session["club"] = club

    flash("Great-booking complete!")
    return render_template("welcome.html", club=club, competitions=competitions)


@app.route("/points")
def points_board():
    """Public points board: list clubs and their points (sorted desc).
    
    This page is publicly accessible without login (Issue #6).
    """
    clubs = get_clubs()
    # Sort by integer points descending when possible
    try:
        clubs_sorted = sorted(clubs, key=lambda c: int(c.get("points", 0)), reverse=True)
    except Exception:
        clubs_sorted = clubs
    return render_template("points.html", clubs=clubs_sorted)


@app.route("/logout")
def logout():
    """We delete session data in order to log the user out"""
    del session["club"]
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
