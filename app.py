from flask import Flask, render_template, request, redirect, url_for, flash, session
import config
import database

app = Flask(__name__)
app.secret_key = "flask-anketa-secret-2026"

# Inicializace databáze při startu aplikace
database.init_db()


def build_results_data():
    """Sestaví seznam možností s počty hlasů pro šablony."""
    counts = database.get_results()
    total = sum(counts.values())
    data = []
    for opt in config.OPTIONS:
        count = counts.get(opt["id"], 0)
        percent = round(count / total * 100) if total > 0 else 0
        data.append({
            "id":      opt["id"],
            "label":   opt["label"],
            "count":   count,
            "percent": percent,
        })
    return data, total


# ------------------------------------------------------------------
# F1 – Hlasování  (GET = zobraz formulář, POST = ulož hlas)
# ------------------------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    already_voted = session.get("voted", False)
    if request.method == "POST":
        if already_voted:
            flash("Už jsi hlasoval/a. Každý může hlasovat pouze jednou.", "warning")
            return redirect(url_for("results"))
        option_id = request.form.get("option")
        if not option_id:
            flash("Vyber prosím jednu možnost.", "warning")
            return redirect(url_for("index"))
        success = database.add_vote(option_id)
        if not success:
            flash("Neplatná možnost.", "danger")
            return redirect(url_for("index"))
        session["voted"] = True
        flash("Tvůj hlas byl uložen!", "success")
        return redirect(url_for("results"))
    return render_template("index.html",
                           question=config.QUESTION,
                           options=config.OPTIONS,
                           already_voted=already_voted)


# ------------------------------------------------------------------
# F2 – Zobrazení výsledků
# ------------------------------------------------------------------
@app.route("/results")
def results():
    data, total = build_results_data()
    return render_template("results.html",
                           question=config.QUESTION,
                           results=data,
                           total=total)


# ------------------------------------------------------------------
# F3 – Reset hlasování (GET = formulář, POST = provedení resetu)
# ------------------------------------------------------------------
@app.route("/reset", methods=["GET", "POST"])
def reset():
    if request.method == "POST":
        token = request.form.get("token", "").strip()
        if token == config.RESET_TOKEN:
            database.reset_votes()
            flash("Hlasování bylo úspěšně resetováno.", "success")
        else:
            flash("Nesprávný token – reset nebyl proveden.", "danger")
        return redirect(url_for("results"))
    return render_template("reset.html")


# ------------------------------------------------------------------
# Stránka O anketě
# ------------------------------------------------------------------
@app.route("/about")
def about():
    return render_template("about.html")


if __name__ == "__main__":
    app.run(debug=True)
