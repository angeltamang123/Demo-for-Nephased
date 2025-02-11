# example: api/index.py
from flask import Flask, request, jsonify
from nephased import Nephased

app = Flask(__name__)

# Attempt to store global instance (since serverless can re-use it if warm)
global_nep_model = None

def get_model():
    global global_nep_model
    if global_nep_model is None:
        global_nep_model = Nephased()  # load the model
    return global_nep_model

@app.route("/api/init", methods=["GET"])
def init_model():
    try:
        model = get_model()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        if not data or "texts" not in data:
            return jsonify({"status": "error", "message": "No texts provided"}), 400

        texts = data["texts"]
        if not isinstance(texts, list):
            return jsonify({"status": "error", "message": "'texts' must be a list"}), 400

        model = get_model()
        sentiments = model.predict(texts)

        return jsonify({"status": "ok", "sentiments": sentiments}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
