from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Topic(db.Model):
    __tablename__ = 'topics'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    search_query = db.Column(db.String(200), nullable=False)
    pinned_videos = db.relationship('PinnedVideo', backref='topic', cascade='all, delete-orphan')
    sessions = db.relationship('Session', backref='topic')


class PinnedVideo(db.Model):
    __tablename__ = 'pinned_videos'
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    video_id = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(300), nullable=False)


class Session(db.Model):
    __tablename__ = 'sessions'
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=False)
    work_minutes = db.Column(db.Integer, default=25)
    break_minutes = db.Column(db.Integer, default=5)
    rounds = db.Column(db.Integer, default=4)
    video_id = db.Column(db.String(20), nullable=False, default='')
    video_title = db.Column(db.String(300), nullable=False, default='')
    started_at = db.Column(db.DateTime, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    notes = db.relationship('Note', backref='session', cascade='all, delete-orphan')


class Note(db.Model):
    __tablename__ = 'notes'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
