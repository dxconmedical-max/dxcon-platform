from app import create_app
from app.extensions.db import db
from flask import request, jsonify

app = create_app()

# Đăng ký route tạm thời ngay sau khi app được tạo
@app.route('/api/v1/patients', methods=['POST'])
def test_curl():
    return jsonify({"message": "Đã bắt được lệnh CURL!"}), 201

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True, port=8000)
