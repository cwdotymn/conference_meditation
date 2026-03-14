# Conference Meditation

An immersive focus chamber for conference-mode thinking.
Pick a topic. Set your timer. Let your mind wander.

## Setup

```bash
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000

## YouTube API (optional but recommended)

The app works without a YouTube API key — you can manually pin YouTube URLs to topics.
To enable live search, get a free API key from Google Cloud Console:

1. Go to https://console.cloud.google.com
2. Create a project → Enable "YouTube Data API v3"
3. Create an API Key credential
4. Set the environment variable before running:

```bash
export YOUTUBE_API_KEY=your_key_here
python app.py
```

On PythonAnywhere, set the env var in your WSGI config file.

## PythonAnywhere Deployment

1. Upload the project folder to your PythonAnywhere home directory
2. Create a new Web App → Manual configuration → Python 3.x
3. Edit the WSGI config file:

```python
import sys
sys.path.insert(0, '/home/yourusername/conference_meditation')
from app import app as application
```

4. Set environment variables in the WSGI file or via the PA console:
```python
import os
os.environ['YOUTUBE_API_KEY'] = 'your_key_here'
```

5. Reload the web app

## Features

- **Topics** — keyword filters that drive YouTube search (Nexthink, Claude, DEX, etc.)
- **Pinned Videos** — manually pin specific YouTube URLs to any topic
- **YouTube Search** — live search via YouTube Data API v3 (requires API key)
- **Custom Pomodoro** — configure work duration, break duration, and number of rounds
- **Focus Chamber** — immersive dark UI with embedded YouTube player + side-by-side notes
- **Session History** — review all notes from past sessions

## Project Structure

```
conference_meditation/
├── app.py              # Flask routes
├── models.py           # SQLAlchemy models (Topic, PinnedVideo, Session, Note)
├── requirements.txt
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── new_session.html
│   ├── session.html    # The focus chamber
│   ├── topics.html
│   └── history.html
└── static/
    └── css/
        └── main.css
```
