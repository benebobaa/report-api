from flask import Flask, jsonify, request, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
from flask_cors import CORS
import os, requests


app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///testing_image.db'
app.config['SECRET_KEY'] = 'your-secret-key'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    todos = db.relationship('Report', backref='user', lazy=True)


class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type_report = db.Column(db.String(200), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    phone = db.Column(db.String(100), nullable=False)
    status = db.Column(db.Integer, default=0, nullable=False)
    date = db.Column(db.String, default=datetime.utcnow, nullable=False)
    image_url = db.Column(db.String(200), nullable=False)
    img = db.Column(db.Text, nullable=False)
    name = db.Column(db.Text, nullable=False)
    mimetype = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
class Helper(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String, default=datetime.utcnow, nullable=False)
    
with app.app_context():
    db.create_all()

# == AUTH LOGIN REGISTER == 

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
    
# == IMAGE URL ACCESS ==

@app.route('/report/image/<int:img_id>', methods=['GET'])
def get_image(img_id):
    img = Report.query.filter_by(id=img_id).first()
    if not img:
        return jsonify({'message': 'Image not found'}), 404
    return Response( img.img, mimetype=img.mimetype) 

# == REPORT FORM POST DATA == 

@app.route('/report/add/<id_user>', methods=['POST'])
def create_report(id_user):
    current_user_id = id_user
    type_report = request.form['type_report']
    content = request.form['content']
    phone = request.form['phone']
    date = request.form['date']
    pic = request.files['image']
    if not pic:
        return jsonify({'message': 'No image uploaded'}), 400
    filename = secure_filename(pic.filename)
    mimetype = pic.mimetype
    submit_id = Helper(date = date) 
    db.session.add(submit_id)
    get_id = Helper.query.order_by(Helper.id.desc()).first()
    submit = Report(type_report = type_report, content = content, phone = phone, date = date , image_url= 'https://'+request.host + '/report/image/' + str(get_id.id), img=pic.read(), name=filename, mimetype=mimetype,user_id=current_user_id)
    db.session.add(submit)
    db.session.commit()
    url = "https://onesignal.com/api/v1/notifications"

    payload = {
        "app_id":"58482fcd-5f0a-47f3-8fe2-81968252abaa",
        "included_segments": ["All"],
        "headings":{
            "en":"Laporan Baru",
            "id":"Laporan Baru"
        },
        "contents": {
            "en": "Cek user admin untuk melihat laporan terbaru",
            "id": "Cek user admin untuk melihat laporan terbaru"
        },
        "name": "M-REPORT"
    }

    headers = {
        "Authorization": "Basic ZDNlMzY4YmYtZjlkYS00NDhmLWE0NzMtM2U3OGNjZmY3Mzc5",
        "content-type": "application/json",
        "accept" : "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    print(response.text)
    return jsonify({'message': 'Report submit success'}), 201

# == REPORT FORM GET DATA == 

@app.route('/reports/<id_user>', methods=['GET'])
def get_reports(id_user):
    current_user_id = id_user
    reports = Report.query.filter_by(user_id=current_user_id).all()
    output = []
    for report in reports:
        report_data = {'id': report.id, 'type_report': report.type_report, 'content': report.content, 'phone': report.phone, 'status': report.status, 'date': report.date, 'image_url': report.image_url}
        output.append(report_data)
    return jsonify({'data': output})

@app.route('/admin/reports', methods=['GET'])
def get_admin_reports():
    reports = Report.query.all()
    output = []
    for report in reports:
        report_data = {'id': report.id, 'type_report': report.type_report, 'content': report.content, 'phone': report.phone, 'status': report.status, 'date': report.date, 'image_url': report.image_url}
        output.append(report_data)
    return jsonify({'data': output})

# == DEL REPORTS ==
@app.route('/admin/report/<int:report_id>', methods=['DELETE'])
def del_admin_report(report_id):
    report = Report.query.filter_by(id=report_id).first()
    if not report:
        return jsonify({'message': 'Report not found'}), 404
    db.session.delete(report)
    db.session.commit()
    return jsonify({'message': 'Report deleted successfully!'})


# == PUT UPDATE STATUS REPORT ==

@app.route('/admin/report/<int:report_id>', methods=['PUT'])
def update_report(report_id):
    data = request.get_json()
    report = Report.query.filter_by(id=report_id).first()
    if not report:
        return jsonify({'message': 'Report not found'}), 404
    report.status = data['status']
    db.session.commit()
    return jsonify({'message': 'Report updated successfully!'})

# @app.route('/todos/add/<id_user>', methods=['POST'])
# def create_todo(id_user):
#     current_user_id = id_user
#     data = request.get_json()
#     new_todo = Todo(content=data['content'], user_id=current_user_id)
#     db.session.add(new_todo)
#     db.session.commit()
#     return jsonify({'message': 'Todo created successfully!'})

# @app.route('/todos/<id_user>', methods=['GET'])
# def get_todos(id_user):
#     current_user_id = id_user
#     todos = Todo.query.filter_by(user_id=current_user_id).all()
#     output = []
#     for todo in todos:
#         todo_data = {'id': todo.id, 'content': todo.content, 'completed': todo.completed}
#         output.append(todo_data)
#     return jsonify({'todos': output})

@app.route('/')
def index():
    return jsonify({"Choo Choo": "Welcome to your Flask app 🚅"})


if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
