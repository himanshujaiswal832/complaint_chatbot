from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

def generate_complaint_id():
    return str(uuid.uuid4())[:8]

class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.String(50), unique=True, default=generate_complaint_id)
    name = db.Column(db.String(100))
    phone_number = db.Column(db.String(15))
    email = db.Column(db.String(100))
    complaint_details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
