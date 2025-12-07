from flask import Flask, send_file, request, abort, render_template_string
import os
from dotenv import load_dotenv

load_dotenv()
PIN = os.getenv("PIN","123456")
app = Flask(__name__, static_folder="../output", template_folder="../output")

TEMPLATE = """
<html>
<head><title>Trading Dashboard</title></head>
<body>
<h2>AI Trading Dashboard (Demo)</h2>
<form method="POST">
PIN: <input name="pin" maxlength="6"/>
<input type="submit" value="Unlock"/>
</form>
{% if unlocked %}
  <p>Latest chart:</p>
  <img src="/chart" style="max-width:900px"/>
  <h3>Analysis</h3>
  <pre>{{analysis}}</pre>
{% endif %}
</body>
</html>
"""

def check_pin(p):
    return p == PIN

@app.route("/", methods=["GET","POST"])
def index():
    unlocked = False
    analysis = "No analysis yet."
    if request.method=="POST":
        pin = request.form.get("pin","")
        if not check_pin(pin):
            abort(403)
        unlocked = True
    # read analysis file if exists
    try:
        with open("output/analysis.txt","r") as f:
            analysis = f.read()
    except:
        analysis = "No analysis saved yet."
    return render_template_string(TEMPLATE, unlocked=unlocked, analysis=analysis)

@app.route("/chart")
def chart():
    p = "output/BTCUSDT_chart.png"
    if not os.path.exists(p):
        abort(404)
    return send_file(p, mimetype="image/png")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
