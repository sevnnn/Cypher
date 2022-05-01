from flask import Flask, render_template
from cypher import Cypher

c = Cypher()
f = Flask(__name__)


@f.route("/")
def index():
    return render_template("index.html", c=c)


@f.route("/check_match")
def check_match():
    body, sc = c.api_get("glz", f"/core-game/v1/players/{c.puuid}")
    if sc == 200:
        return body["MatchID"]
    else:
        print(sc)
        return "0"


@f.route("/match/<string:match_id>")
def match(match_id):
    body = c.api_get("glz", f"/core-game/v1/matches/{match_id}")[0]
    info, blue, red = c.gather_info(body)
    return render_template("match.html", c=c, info=info, blue=blue, red=red)


if __name__ == "__main__":
    # os.system("start http://localhost:5000")
    print(
        "Open http://localhost:5000 in your browser if it wasn't opened automatically"
    )
    f.run(debug=True)
