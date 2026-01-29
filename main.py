from flask import Flask
from flask_cors import CORS
from app import pathfinder_bp
from backend import backend_bp
from verify import verify_bp

from flask import Flask, send_from_directory

app = Flask(__name__)
CORS(app)


app.register_blueprint(backend_bp)
app.register_blueprint(pathfinder_bp)
app.register_blueprint(verify_bp)
@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)
if __name__ == '__main__':
    app.run(debug=True)
