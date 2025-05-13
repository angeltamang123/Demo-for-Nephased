from flask import Flask, request, jsonify
import torch
import numpy as np
from gensim.models import FastText
import re
import string
import nltk
from nepali_stemmer.stemmer import NepStemmer
from nltk.corpus import stopwords

# Initialize Flask app
app = Flask(__name__)

# Load the model and embeddings once
device = "cuda" if torch.cuda.is_available() else "cpu"

# Load the trained DNN model
class DNN_Classifier(torch.nn.Module):
    def __init__(self, input_dim, output_dim, input_neurons=64, hidden1_neurons=32, dropout1_rate=0.4, dropout2_rate=0.3):
        super(DNN_Classifier, self).__init__()
        self.fc1 = torch.nn.Linear(input_dim, input_neurons)
        self.bn1 = torch.nn.BatchNorm1d(input_neurons)
        self.dropout1 = torch.nn.Dropout(dropout1_rate)
        self.relu = torch.nn.ReLU()
        self.fc2 = torch.nn.Linear(input_neurons, hidden1_neurons)
        self.bn2 = torch.nn.BatchNorm1d(hidden1_neurons)
        self.dropout2 = torch.nn.Dropout(dropout2_rate)
        self.fc3 = torch.nn.Linear(hidden1_neurons, output_dim)

    def forward(self, x):
        x = self.fc1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.dropout1(x)
        x = self.fc2(x)
        x = self.bn2(x)
        x = self.relu(x)
        x = self.dropout2(x)
        x = self.fc3(x)
        return x

# Load trained model
input_dim = 300
output_dim = 4
model = DNN_Classifier(input_dim, output_dim)
model.load_state_dict(torch.load("/home/angel-tamang/Nepali Hate Sentiment Detection/Project/Post-Defense/Word Embeddings/dnn_classifier.pth"))
model.to(device)
model.eval()

# Load FastText model
fasttext = FastText.load("/home/angel-tamang/Nepali Hate Sentiment Detection/Project/Post-Defense/Data/fasttext_model")

# NLP preprocessing setup
nltk.download("punkt")
nltk.download("stopwords")
nepali_stopwords = set(stopwords.words("nepali"))
nepstem = NepStemmer()

# Preprocessing function
def preprocess_text(text):
    if not isinstance(text, str):
        return ""
    text = nepstem.stem(text)
    text = text.lower()
    text = re.sub(r"।", " |", text)
    text = re.sub(r"[" + re.escape(string.punctuation) + "]", " ", text)
    text = re.sub(r"[\.\-…]+", " ", text)
    text = " ".join([word for word in text.split() if word not in nepali_stopwords])
    return text

# Convert text to embedding
def text_to_embedding(text):
    words = text.split()
    valid_word_vectors = [fasttext.wv[word] for word in words if word in fasttext.wv]
    if valid_word_vectors:
        return np.mean(valid_word_vectors, axis=0)
    else:
        return np.zeros(fasttext.vector_size)

# Inference function
def preprocess_and_predict(texts):
    preprocessed_texts = [preprocess_text(text) for text in texts]
    embeddings = np.array([text_to_embedding(text) for text in preprocessed_texts])
    input_tensor = torch.tensor(embeddings, dtype=torch.float32).to(device)

    with torch.no_grad():
        output = model(input_tensor)
        probs = torch.softmax(output, dim=1)
        predicted_classes = torch.argmax(probs, dim=1).cpu().numpy()

    return predicted_classes.tolist()

@app.route("/api/init", methods=["GET"])
def init_model():
    return jsonify({"status": "ok"})

@app.route("/api/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        if not data or "texts" not in data:
            return jsonify({"status": "error", "message": "No texts provided"}), 400

        texts = data["texts"]
        if not isinstance(texts, list):
            return jsonify({"status": "error", "message": "'texts' must be a list"}), 400

        class_labels = {0: "GENERAL", 1: "LIGHT PROFANITY", 2: "HIGH PROFANITY", 3: "VIOLENCE"}

        pred_classes = preprocess_and_predict(texts)

        # Convert class indices to labels
        sentiments = [class_labels[pred] for pred in pred_classes]

        return jsonify({"status": "ok", "sentiments": sentiments}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

