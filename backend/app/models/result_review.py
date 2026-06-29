from datetime import datetime
import uuid

from app.extensions.db import db


class ResultReview(db.Model):

    __tablename__ = "result_reviews"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    lab_result_id = db.Column(
        db.String(36),
        db.ForeignKey("lab_results.id"),
        nullable=False,
    )

    reviewer_email = db.Column(db.String(255), nullable=False)

    review_status = db.Column(db.String(50), default="SUBMITTED")

    comments = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "lab_result_id": self.lab_result_id,
            "reviewer_email": self.reviewer_email,
            "review_status": self.review_status,
            "comments": self.comments,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
