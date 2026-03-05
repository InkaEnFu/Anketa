from flask import Flask, render_template, request, redirect, url_for, flash, session, Response, jsonify
import random
import string
import io
import time
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import config
import database

app = Flask(__name__)
app.secret_key = "flask-anketa-secret-2026"

# Inicializace databáze při startu aplikace
database.init_db()

CAPTCHA_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # bez I, 0, O, 1
CAPTCHA_MAX_ATTEMPTS = 3
CAPTCHA_LOCKOUT_SECONDS = 600  # 10 minut


def _get_ip():
    """Vrátí skutečnou IP klienta (funguje i za reverzním proxy)."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr


def _new_captcha_code():
    code = ''.join(random.choices(CAPTCHA_CHARS, k=5))
    session["captcha_code"] = code
    session["captcha_verified"] = False
    return code


# ------------------------------------------------------------------
# Generování CAPTCHA obrázku
# ------------------------------------------------------------------
@app.route("/captcha-image")
def captcha_image():
    # Zamezit generování nového kódu při zablokování
    ip = _get_ip()
    _, locked_until = database.get_captcha_state(ip)
    if time.time() < locked_until:
        return Response(status=429)

    code = _new_captcha_code()
    width, height = 190, 60
    img = Image.new("RGB", (width, height), color=(245, 246, 252))
    draw = ImageDraw.Draw(img)

    # šumové tečky
    for _ in range(400):
        draw.point(
            (random.randint(0, width), random.randint(0, height)),
            fill=(random.randint(160, 220), random.randint(160, 220), random.randint(200, 240)),
        )

    # rušivé čáry
    for _ in range(5):
        draw.line(
            [(random.randint(0, width), random.randint(0, height)),
             (random.randint(0, width), random.randint(0, height))],
            fill=(random.randint(140, 190), random.randint(140, 190), random.randint(180, 220)),
            width=1,
        )

    # písmo
    try:
        font = ImageFont.load_default(size=38)
    except TypeError:
        font = ImageFont.load_default()

    for i, ch in enumerate(code):
        x = 8 + i * 36 + random.randint(-3, 3)
        y = random.randint(4, 14)
        color = (
            random.randint(20, 80),
            random.randint(20, 100),
            random.randint(120, 200),
        )
        draw.text((x, y), ch, font=font, fill=color)

    img = img.filter(ImageFilter.GaussianBlur(radius=0.7))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    response = Response(buf.getvalue(), mimetype="image/png")
    response.headers["Cache-Control"] = "no-store"
    return response


# ------------------------------------------------------------------
# Ověření CAPTCHA (AJAX)
# ------------------------------------------------------------------
@app.route("/verify-captcha", methods=["POST"])
def verify_captcha():
    ip = _get_ip()
    now = time.time()

    # Zkontroluj zablokování v DB
    _, locked_until = database.get_captcha_state(ip)
    if now < locked_until:
        remaining = int(locked_until - now)
        return jsonify({"ok": False, "locked": True, "remaining": remaining}), 429

    user_input = request.form.get("captcha_input", "").strip().upper()
    correct = session.get("captcha_code", "")

    if user_input and user_input == correct:
        database.clear_captcha_attempts(ip)
        session["captcha_verified"] = True
        return jsonify({"ok": True})

    # Nesprávná odpověď – zaznamenej v DB
    locked, locked_until, remaining_attempts = database.record_captcha_failure(
        ip, CAPTCHA_MAX_ATTEMPTS, CAPTCHA_LOCKOUT_SECONDS
    )

    if locked:
        return jsonify({
            "ok": False,
            "locked": True,
            "remaining": CAPTCHA_LOCKOUT_SECONDS,
        }), 429

    return jsonify({"ok": False, "locked": False, "remaining_attempts": remaining_attempts}), 400


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

        # Ověření CAPTCHA (session flag nastavený přes /verify-captcha)
        if not session.get("captcha_verified"):
            flash("Nejprve prosím dokonči ověření CAPTCHA.", "danger")
            return redirect(url_for("index"))

        option_id = request.form.get("option")
        if not option_id:
            flash("Vyber prosím jednu možnost.", "warning")
            return redirect(url_for("index"))
        success = database.add_vote(option_id)
        if not success:
            flash("Neplatná možnost.", "danger")
            return redirect(url_for("index"))

        # Uložit vlastní značku, pokud zvolil "Jiné"
        if option_id == "jine":
            custom_brand = request.form.get("custom_brand", "").strip()
            if custom_brand and len(custom_brand) <= 100:
                database.add_custom_brand(custom_brand)

        session["voted"] = True
        session.pop("captcha_verified", None)
        flash("Tvůj hlas byl uložen!", "success")
        return redirect(url_for("results"))

    captcha_verified = session.get("captcha_verified", False)
    ip = _get_ip()
    _, locked_until = database.get_captcha_state(ip)
    now = time.time()
    locked = now < locked_until
    lock_remaining = max(0, int(locked_until - now)) if locked else 0
    return render_template("index.html",
                           question=config.QUESTION,
                           options=config.OPTIONS,
                           already_voted=already_voted,
                           captcha_verified=captcha_verified,
                           captcha_locked=locked,
                           lock_remaining=lock_remaining)


# ------------------------------------------------------------------
# F2 – Zobrazení výsledků
# ------------------------------------------------------------------
@app.route("/results")
def results():
    data, total = build_results_data()
    custom_brands = database.get_custom_brands()
    return render_template("results.html",
                           question=config.QUESTION,
                           results=data,
                           total=total,
                           custom_brands=custom_brands)


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
    app.run(debug=False)
