from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_bcrypt import Bcrypt
import os


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SECRET_KEY'] = 'your-secret-key'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    todos = db.relationship('Todo', backref='user', lazy=True)


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)



@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(username=data['username'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully!'})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if user and bcrypt.check_password_hash(user.password, data['password']):
        return jsonify({'user_id': user.id})
    else:
        return jsonify({'message': 'Invalid username or password'}), 401

@app.route('/todos/add/<id_user>', methods=['POST'])
def create_todo(id_user):
    current_user_id = id_user
    data = request.get_json()
    new_todo = Todo(content=data['content'], user_id=current_user_id)
    db.session.add(new_todo)
    db.session.commit()
    return jsonify({'message': 'Todo created successfully!'})

@app.route('/todos/<id_user>', methods=['GET'])
def get_todos(id_user):
    current_user_id = id_user
    todos = Todo.query.filter_by(user_id=current_user_id).all()
    output = []
    for todo in todos:
        todo_data = {'id': todo.id, 'content': todo.content, 'completed': todo.completed}
        output.append(todo_data)
    return jsonify({'todos': output})

@app.route('/')
def index():
    return jsonify({"Choo Choo": "Welcome to your Flask app 🚅"})


if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
