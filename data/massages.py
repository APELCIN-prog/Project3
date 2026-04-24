import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class Message(SqlAlchemyBase):
    __tablename__ = 'messages'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True,
                           autoincrement=True)
    job_id = sqlalchemy.Column(sqlalchemy.Integer,
                               sqlalchemy.ForeignKey('jobs.id'))
    sender_id = sqlalchemy.Column(sqlalchemy.Integer,
                                  sqlalchemy.ForeignKey('users.id'))
    content = sqlalchemy.Column(sqlalchemy.String,
                                nullable=False)
    created_at = sqlalchemy.Column(sqlalchemy.DateTime,
                                   default=datetime.datetime.now)

    # Связи
    job = orm.relationship('Job', backref='messages')
    sender = orm.relationship('User', foreign_keys=[sender_id])