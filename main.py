from flask import Flask
from app.api import api
import os

app = Flask(__name__)

# Register the API blueprint
app.register_blueprint(api, url_prefix='/api')

# development mode and production mode
debug_mode = os.environ.get('FLASK_DEBUG', 'False') == 'True'

@app.route("/")
def index():
    return "Hello World!"

if __name__ == "__main__":
    # 0.0.0.0 make flask use all available network interfaces
    app.run(host='0.0.0.0', port=5001, debug=debug_mode)  