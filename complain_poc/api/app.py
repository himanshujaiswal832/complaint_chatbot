from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from models import db, Complaint

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///complaints.db'
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/complaints', methods=['POST'])
def create_complaint():
    data = request.json
    if not all(k in data for k in ("name", "phone_number", "email", "complaint_details")):
        return jsonify({"error": "Missing fields"}), 400

    complaint = Complaint(**data)
    db.session.add(complaint)
    db.session.commit()
    return jsonify({
        "complaint_id": complaint.complaint_id,
        "message": "Complaint created successfully"
    })

@app.route('/complaints/<complaint_id>', methods=['GET'])
def get_complaint(complaint_id):
    complaint = Complaint.query.filter_by(complaint_id=complaint_id).first()
    if not complaint:
        return jsonify({"error": "Complaint not found"}), 404

    return jsonify({
        "complaint_id": complaint.complaint_id,
        "name": complaint.name,
        "phone_number": complaint.phone_number,
        "email": complaint.email,
        "complaint_details": complaint.complaint_details,
        "created_at": complaint.created_at.strftime("%Y-%m-%d %H:%M:%S")
    })

if __name__ == '__main__':
    app.run(debug=True)
