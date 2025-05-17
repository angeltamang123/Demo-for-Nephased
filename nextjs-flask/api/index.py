
from flask import Flask, request, jsonify
import logging
import traceback
import os
from dotenv import load_dotenv
from gradio_client import Client

load_dotenv()

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
if not app.debug:
    app.logger.setLevel(logging.INFO)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    app.logger.addHandler(stream_handler)
else:
    app.logger.setLevel(logging.DEBUG)

# Gradio API setup
SPACE_ID= "Vyke2000/Nephased-gradio"
API_NAME = "/predict_sentiment" 
HF_AUTH_TOKEN = os.getenv("HF_TOKEN")

gradio_client_instance = None

def get_gradio_client():
    global gradio_client_instance
    if gradio_client_instance is None:
        if HF_AUTH_TOKEN:
            try:
                gradio_client_instance = Client(SPACE_ID, hf_token=HF_AUTH_TOKEN)
                app.logger.info(f"Gradio Client initialized successfully for space: {SPACE_ID}")
            except Exception as e:
                app.logger.error(f"Failed to initialize Gradio Client: {e}")       
        else:
            app.logger.warning("HF_TOKEN not found. Gradio Client for private space will not be initialized.")
    return gradio_client_instance


@app.route("/api/predict", methods=["POST"])
def predict():
    client = get_gradio_client()

    if not client:
        app.logger.error("Gradio Client is not initialized. Check HF_TOKEN and Space ID.")
        return jsonify({"status": "error", "message": "Server configuration error: Gradio client not ready"}), 500
    
    try:
        data = request.get_json()
        if not data or "texts" not in data:
           app.logger.warning("Request received without 'texts' field in the JSON body.")
           return jsonify({"status": "error", "message": "No texts provided in JSON body (expected {'texts': [...]})"}), 400
        
        texts = data["texts"]
        if not isinstance(texts, list):
            app.logger.warning("'texts' field was not a list.")
            return jsonify({"status": "error", "message": "'texts' must be a list"}), 400
        
        if not texts:
            app.logger.info("Received an empty list of texts.")
            return jsonify({"status": "ok", "sentiments": []}), 200
        
        # Prepare data for Gradio:
        gradio_function_payload = data
        
        app.logger.info(f"Sending predict request to Gradio Space using gradio_client.")
        app.logger.debug(f"Payload for Gradio function: {gradio_function_payload}")

        result_from_gradio = client.predict(
            gradio_function_payload,
            api_name=API_NAME
        )

        app.logger.info(f"Gradio client call successful. Result: {result_from_gradio}")

        if isinstance(result_from_gradio, dict) and result_from_gradio.get("status") == "ok":
            sentiments = result_from_gradio.get("sentiments")
          
            if isinstance(sentiments, list) and len(sentiments) == len(texts):
                return jsonify({"status": "ok", "sentiments": sentiments}), 200
            else:
                app.logger.error(f"Malformed success response from Gradio or sentiment count mismatch. Expected {len(texts)} sentiments. Got: {result_from_gradio}")
                return jsonify({"status": "error", "message": "Unexpected response format or count from Gradio model"}), 500
        elif isinstance(result_from_gradio, dict) and result_from_gradio.get("status") == "error":
            error_message = result_from_gradio.get("message", "Unknown error from Gradio function")
            app.logger.error(f"Gradio function returned an error: {error_message}")
            return jsonify({"status": "error", "message": "Error from Gradio model logic", "details": error_message}), 500
        else: 
            app.logger.error(f"Unexpected response type or structure from Gradio: {result_from_gradio}")
            return jsonify({"status": "error", "message": "Unexpected data structure from Gradio"}), 500
       

    except Exception as e: 
        app.logger.error(f"Exception when using gradio_client or processing its result: {traceback.format_exc()}")
    
        if "401" in str(e) or "Unauthorized" in str(e) or "Unauthenticated" in str(e):
             return jsonify({"status": "error", "message": "Authentication error with Gradio service", "details": str(e)}), 401
        if "404" in str(e) or "Not Found" in str(e) or "Could not find Space" in str(e) or "Could not find API" in str(e):
             return jsonify({"status": "error", "message": "Gradio service or API endpoint not found", "details": str(e)}), 404
        return jsonify({"status": "error", "message": f"An internal server error occurred: {str(e)}"}), 500