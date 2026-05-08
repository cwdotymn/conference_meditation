import sys
import os

path = '/home/cwdoty/conference_meditation'
if path not in sys.path:
    sys.path.insert(0, path)

from app import app as application
