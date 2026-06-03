from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
# Dùng SQLite cho giai đoạn test trực tiếp tại local
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dxcon.db' 
db = SQLAlchemy(app)

# Định nghĩa Model đơn giản để test
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))

with app.app_context():
    db.create_all()

# Route nhận dữ liệu từ curl
@app.route('/api/v1/patients', methods=['POST'])
def create_patient():
    data = request.get_json()
    new_patient = Patient(
        full_name=data.get('full_name'),
        phone=data.get('phone'),
        address=data.get('address')
    )
    db.session.add(new_patient)
    db.session.commit()
    return jsonify({"status": "success", "id": new_patient.id}), 201

if __name__ == '__main__':
    app.run(port=8000, debug=True)
