from . import db
from datetime import datetime

class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    description = db.Column(db.Text)
    
    notes = db.relationship("Note", back_populates="subject", cascade="all, delete-orphan")
    resources = db.relationship("Resource", back_populates="subject", cascade="all, delete-orphan")
    events = db.relationship("Event", back_populates="subject", cascade="all, delete-orphan")
    activities = db.relationship("Activity", back_populates="subject", cascade="all, delete-orphan")

class Note(db.Model):
    __tablename__ = 'notes'
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    subject = db.relationship("Subject", back_populates="notes")

class Resource(db.Model):
    __tablename__ = 'resources'
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    type = db.Column(db.String, nullable=False) # 'apuntes', 'ejercicios', 'examenes', 'enlaces'
    title = db.Column(db.String, nullable=False)
    path_or_url = db.Column(db.String, nullable=False)
    
    subject = db.relationship("Subject", back_populates="resources")

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=True)
    title = db.Column(db.String, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text)
    google_event_id = db.Column(db.String)
    
    subject = db.relationship("Subject", back_populates="events")

class Activity(db.Model):
    __tablename__ = 'activities'
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime, nullable=True)
    is_completed = db.Column(db.Integer, default=0) 
    grade = db.Column(db.String, nullable=True)
    comments = db.Column(db.Text, nullable=True)
    
    subject = db.relationship("Subject", back_populates="activities")
    files = db.relationship("ActivityFile", back_populates="activity", cascade="all, delete-orphan")

class ActivityFile(db.Model):
    __tablename__ = 'activity_files'
    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)
    filename = db.Column(db.String, nullable=False)
    drive_file_id = db.Column(db.String, nullable=False)
    
    activity = db.relationship("Activity", back_populates="files")
