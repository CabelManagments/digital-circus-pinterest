from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from datetime import datetime
import os
import urllib.parse

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    uri = urllib.parse.urlparse(DATABASE_URL)
    uri = uri._replace(netloc=uri.netloc.replace(':@', ':'))
    app.config['SQLALCHEMY_DATABASE_URI'] = uri.geturl()
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///digital_circus.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Pin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500))
    image_data = db.Column(db.Text, nullable=False)
    image_mime = db.Column(db.String(50), default='image/jpeg')
    author = db.Column(db.String(100), default='Анонимный артист')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    likes = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'image_data': self.image_data,
            'image_mime': self.image_mime,
            'author': self.author,
            'created_at': self.created_at.isoformat(),
            'likes': self.likes
        }

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/pins', methods=['GET'])
def get_pins():
    pins = Pin.query.order_by(Pin.created_at.desc()).all()
    return jsonify([pin.to_dict() for pin in pins])

@app.route('/api/pins', methods=['POST'])
def create_pin():
    data = request.json
    pin = Pin(
        title=data.get('title', 'Безымянный пин'),
        description=data.get('description', ''),
        image_data=data.get('image_data'),
        image_mime=data.get('image_mime', 'image/jpeg'),
        author=data.get('author', 'Анонимный артист')
    )
    db.session.add(pin)
    db.session.commit()
    socketio.emit('new_pin', pin.to_dict(), broadcast=True)
    return jsonify(pin.to_dict()), 201

@app.route('/api/pins/<int:pin_id>/like', methods=['POST'])
def like_pin(pin_id):
    pin = Pin.query.get_or_404(pin_id)
    pin.likes += 1
    db.session.commit()
    socketio.emit('like_update', {'id': pin_id, 'likes': pin.likes}, broadcast=True)
    return jsonify({'likes': pin.likes})

@app.route('/api/pins/<int:pin_id>', methods=['DELETE'])
def delete_pin(pin_id):
    pin = Pin.query.get_or_404(pin_id)
    db.session.delete(pin)
    db.session.commit()
    socketio.emit('delete_pin', {'id': pin_id}, broadcast=True)
    return jsonify({'message': 'Pin deleted'})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8080)
