from flask import Flask, render_template, request, jsonify
from markov import Rule, MarkovEngine, MarkovError, empirical_space_complexity, empirical_time_complexity

app = Flask(__name__)

@app.errorhandler(MarkovError)
def _err(e):
    return jsonify(error=str(e)), 400

@app.get("/")
def home():
    return render_template("index.html")

@app.post("/api/run")
def run():
    d = request.get_json(force=True)
    word = d.get("word", "")
    txt = d.get("rules", "").strip()
    if not txt:
        return jsonify(output=word, steps=0, trace=[])
    out, trace = MarkovEngine(parse(txt)).run(word)
    return jsonify(output=out, steps=len(trace), trace=[t.__dict__ for t in trace])

FACTORS = [2, 4, 8, 16, 32, 64, 128]

def _needs(d):
    if not d.get("rules") or not d.get("word"):
        return True
    return False

@app.post("/api/time")
def time():
    d = request.get_json(force=True)
    if _needs(d):
        return jsonify(error="word and rules required"), 400
    big_o, samples = empirical_time_complexity(
        parse(d["rules"]), FACTORS, lambda k: d["word"] * k
    )
    return jsonify(big_o=big_o, samples=samples)

@app.post("/api/space")
def space():
    d = request.get_json(force=True)
    if _needs(d):
        return jsonify(error="word and rules required"), 400
    words = {k: d["word"] * k for k in FACTORS}
    big_o, samples = empirical_space_complexity(
        parse(d["rules"]), FACTORS, lambda k: words[k]
    )
    return jsonify(big_o=big_o, samples=samples, words=words)

def parse(txt):
    rules = []
    for n, line in enumerate(txt.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        term = line.endswith('.')
        if term:
            line = line[:-1]
        if ':' not in line:
            raise MarkovError(f"line {n}: no ':'")
        lhs, rhs = map(str.strip, line.split(':', 1))
        rules.append(Rule(lhs, rhs, term))
    return rules

if __name__ == "__main__":
    app.run(debug=True)
