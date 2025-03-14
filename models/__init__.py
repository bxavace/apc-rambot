from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .session import Session
from .conversation import Conversation
from .feedback import Feedback
from .document import Document
from .lead import Lead