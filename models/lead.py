from . import db

class Lead(db.Model):
    __tablename__ = 'leads'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    # NOTE: 'type' field should be ['student', 'parent', 'alumni', 'staff', 'other]
    type = db.Column(db.String(20), nullable=False, default='other')

    def __repr__(self):
        return f'<Lead {self.name}>'
