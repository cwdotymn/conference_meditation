from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask import session as flask_session
from authlib.integrations.flask_client import OAuth
from functools import wraps
from database import get_db, init_db
from datetime import datetime, timezone
import os
import re
import urllib.request
import urllib.parse
import json as json_lib

app = Flask(__name__)
app.config['SECRET_KEY'] = 'conference-meditation-secret'

# ── Auth ──────────────────────────────────────────────────────────────────────

oauth = OAuth(app)
authentik = oauth.register(
    name='authentik',
    client_id='HuU82ZQa3lGoxaIhrXCsdJhWOFmEgR5NUk12c6ZG',
    client_secret='8kqa0JEjFkcrbSV8OxW8qZdADWq00bhM4uZMiqEqXiieXdGgzML3mnPpaBoGFqkI9jPBx6XX6uCxibOezdwxIv5S3GdMwBdJ0aMBKBybXERJ69HhKn1N4AnazlKwdJ3b',
    server_metadata_url='http://localhost:9000/application/o/conference-meditation/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in flask_session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ── Database ──────────────────────────────────────────────────────────────────

init_db()

# ── Helpers ───────────────────────────────────────────────────────────────────

def extract_video_id(url):
    match = re.search(r'(?:v=|youtu\.be/|embed/)([A-Za-z0-9_-]{11})', url)
    return match.group(1) if match else ''

def utcnow():
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

def fmt_time(iso_str):
    if not iso_str:
        return ''
    try:
        dt = datetime.strptime(iso_str[:19], '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%b %d, %Y  %H:%M')
    except Exception:
        return iso_str

def fmt_clock(iso_str):
    if not iso_str:
        return ''
    try:
        dt = datetime.strptime(iso_str[:19], '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%H:%M')
    except Exception:
        return ''

# ── Auth Routes ───────────────────────────────────────────────────────────────

@app.route('/login')
def login():
    redirect_uri = url_for('auth_callback', _external=True)
    return authentik.authorize_redirect(redirect_uri)

@app.route('/auth/callback')
def auth_callback():
    token = authentik.authorize_access_token()
    user = token['userinfo']
    flask_session['user'] = user
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    flask_session.pop('user', None)
    return redirect('http://localhost:9000/application/o/conference-meditation/end-session/')

# ── Home ──────────────────────────────────────────────────────────────────────

@app.route('/')
@login_required
def index():
    with get_db() as conn:
        topics = conn.execute("SELECT * FROM topics ORDER BY name").fetchall()
    return render_template('index.html', topics=topics)

# ── Topics ────────────────────────────────────────────────────────────────────

@app.route('/topics')
@login_required
def topics():
    with get_db() as conn:
        topics = conn.execute("SELECT * FROM topics ORDER BY name").fetchall()
    return render_template('topics.html', topics=topics)

@app.route('/api/topics', methods=['POST'])
@login_required
def create_topic():
    data = request.json
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO topics (name, search_query) VALUES (?, ?)",
            (data['name'], data.get('search_query', data['name']))
        )
        conn.commit()
    return jsonify({'id': cur.lastrowid, 'name': data['name']})

@app.route('/api/topics/<int:topic_id>', methods=['DELETE'])
@login_required
def delete_topic(topic_id):
    with get_db() as conn:
        conn.execute("DELETE FROM topics WHERE id = ?", (topic_id,))
        conn.commit()
    return jsonify({'ok': True})

# ── Pinned Videos ─────────────────────────────────────────────────────────────

@app.route('/api/topics/<int:topic_id>/pins', methods=['GET'])
@login_required
def get_pins(topic_id):
    with get_db() as conn:
        pins = conn.execute(
            "SELECT * FROM pinned_videos WHERE topic_id = ?", (topic_id,)
        ).fetchall()
    return jsonify([dict(p) for p in pins])

@app.route('/api/topics/<int:topic_id>/pins', methods=['POST'])
@login_required
def add_pin(topic_id):
    data = request.json
    url = data['url']
    video_id = extract_video_id(url)
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO pinned_videos (topic_id, url, video_id, title) VALUES (?, ?, ?, ?)",
            (topic_id, url, video_id, data.get('title', 'Pinned Video'))
        )
        conn.commit()
    return jsonify({'id': cur.lastrowid, 'video_id': video_id})

@app.route('/api/pins/<int:pin_id>', methods=['DELETE'])
@login_required
def delete_pin(pin_id):
    with get_db() as conn:
        conn.execute("DELETE FROM pinned_videos WHERE id = ?", (pin_id,))
        conn.commit()
    return jsonify({'ok': True})

# ── Session ───────────────────────────────────────────────────────────────────

@app.route('/session/new', methods=['GET', 'POST'])
@login_required
def new_session():
    if request.method == 'POST':
        data = request.form
        with get_db() as conn:
            cur = conn.execute(
                """INSERT INTO sessions
                   (topic_id, work_minutes, break_minutes, rounds, video_id, video_title, started_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    int(data['topic_id']),
                    int(data.get('work_minutes', 25)),
                    int(data.get('break_minutes', 5)),
                    int(data.get('rounds', 4)),
                    data.get('video_id', ''),
                    data.get('video_title', ''),
                    utcnow()
                )
            )
            conn.commit()
            session_id = cur.lastrowid
        return redirect(url_for('focus_session', session_id=session_id))

    with get_db() as conn:
        topics = conn.execute("SELECT * FROM topics ORDER BY name").fetchall()
    pre_topic = request.args.get('topic_id')
    return render_template('new_session.html', topics=topics, pre_topic=pre_topic)

@app.route('/session/<int:session_id>')
@login_required
def focus_session(session_id):
    with get_db() as conn:
        session = conn.execute(
            """SELECT s.*, t.name as topic_name, t.search_query
               FROM sessions s JOIN topics t ON s.topic_id = t.id
               WHERE s.id = ?""", (session_id,)
        ).fetchone()
        notes = conn.execute(
            "SELECT * FROM notes WHERE session_id = ? ORDER BY created_at",
            (session_id,)
        ).fetchall()
    if not session:
        return "Session not found", 404
    return render_template('session.html', session=dict(session),
                           notes=[dict(n) for n in notes],
                           fmt_clock=fmt_clock)

@app.route('/api/sessions/<int:session_id>/complete', methods=['POST'])
@login_required
def complete_session(session_id):
    with get_db() as conn:
        conn.execute(
            "UPDATE sessions SET completed_at = ? WHERE id = ?",
            (utcnow(), session_id)
        )
        conn.commit()
    return jsonify({'ok': True})

# ── Notes ─────────────────────────────────────────────────────────────────────

@app.route('/api/sessions/<int:session_id>/notes', methods=['POST'])
@login_required
def save_note(session_id):
    data = request.json
    ts = utcnow()
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO notes (session_id, content, created_at) VALUES (?, ?, ?)",
            (session_id, data['content'], ts)
        )
        conn.commit()
    return jsonify({'id': cur.lastrowid, 'created_at': ts})

# ── History ───────────────────────────────────────────────────────────────────

@app.route('/history')
@login_required
def history():
    with get_db() as conn:
        sessions = conn.execute(
            """SELECT s.*, t.name as topic_name
               FROM sessions s JOIN topics t ON s.topic_id = t.id
               ORDER BY s.started_at DESC LIMIT 50"""
        ).fetchall()
        session_list = []
        for s in sessions:
            s_dict = dict(s)
            notes = conn.execute(
                "SELECT * FROM notes WHERE session_id = ? ORDER BY created_at",
                (s_dict['id'],)
            ).fetchall()
            s_dict['notes'] = [dict(n) for n in notes]
            s_dict['started_fmt'] = fmt_time(s_dict['started_at'])
            session_list.append(s_dict)
    return render_template('history.html', sessions=session_list, fmt_clock=fmt_clock)

# ── YouTube Search ────────────────────────────────────────────────────────────

@app.route('/api/youtube/search')
@login_required
def youtube_search():
    query = request.args.get('q', '')
    api_key = os.environ.get('YOUTUBE_API_KEY', '')
    if not api_key:
        return jsonify({'error': 'No YouTube API key configured. Set YOUTUBE_API_KEY env var, or pin videos manually.', 'items': []})
    try:
        url = (
            "https://www.googleapis.com/youtube/v3/search"
            f"?part=snippet&type=video&maxResults=8&q={urllib.parse.quote(query)}&key={api_key}"
        )
        with urllib.request.urlopen(url, timeout=6) as resp:
            data = json_lib.loads(resp.read())
        items = [
            {
                'video_id': item['id']['videoId'],
                'title': item['snippet']['title'],
                'channel': item['snippet']['channelTitle'],
                'thumbnail': item['snippet']['thumbnails']['medium']['url']
            }
            for item in data.get('items', [])
        ]
        return jsonify({'items': items})
    except Exception as e:
        return jsonify({'error': str(e), 'items': []})

@app.route('/debug/user')
def debug_user():
    return jsonify(dict(flask_session.get('user', {})))

if __name__ == '__main__':
    app.run(debug=True)

