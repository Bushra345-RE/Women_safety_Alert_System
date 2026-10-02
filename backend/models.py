from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id        = db.Column(db.Integer, primary_key=True)
    name      = db.Column(db.String(100), nullable=False)
    email     = db.Column(db.String(120), unique=True, nullable=False)
    password  = db.Column(db.String(200), nullable=False)
    contact1  = db.Column(db.String(20), default='')
    contact2  = db.Column(db.String(20), default='')
    contact3  = db.Column(db.String(20), default='')
    contact4  = db.Column(db.String(20), default='')
    contact5  = db.Column(db.String(20), default='')
    alerts    = db.relationship('Alert', backref='user', lazy=True)

    def to_dict(self):
        return {
            'id':       self.id,
            'name':     self.name,
            'email':    self.email,
            'contact1': self.contact1 or '',
            'contact2': self.contact2 or '',
            'contact3': self.contact3 or '',
            'contact4': self.contact4 or '',
            'contact5': self.contact5 or '',
        }


class Alert(db.Model):
    __tablename__ = 'alerts'
    id        = db.Column(db.Integer, primary_key=True)
    user_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    latitude  = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    address   = db.Column(db.String(400), default='')
    time      = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':        self.id,
            'user_id':   self.user_id,
            'latitude':  self.latitude,
            'longitude': self.longitude,
            'address':   self.address or 'Unknown location',
            'time':      self.time.strftime('%Y-%m-%d %H:%M:%S'),
        }