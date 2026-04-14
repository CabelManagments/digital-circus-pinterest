# app.py
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import base64
import re

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# Конфигурация базы данных
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'digital_circus.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Модель пина
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
    return jsonify(pin.to_dict()), 201

@app.route('/api/pins/<int:pin_id>/like', methods=['POST'])
def like_pin(pin_id):
    pin = Pin.query.get_or_404(pin_id)
    pin.likes += 1
    db.session.commit()
    return jsonify({'likes': pin.likes})

@app.route('/api/pins/<int:pin_id>', methods=['DELETE'])
def delete_pin(pin_id):
    pin = Pin.query.get_or_404(pin_id)
    db.session.delete(pin)
    db.session.commit()
    return jsonify({'message': 'Pin deleted'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
