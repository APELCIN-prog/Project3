import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class Response(SqlAlchemyBase):
    __tablename__ = 'responses'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    job_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('jobs.id'))
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    status = sqlalchemy.Column(sqlalchemy.String, default='pending')  # pending, accepted, rejected
    created_at = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    # Связи
    job = orm.relationship('Job', backref='responses')
    user = orm.relationship('User', foreign_keys=[user_id])