import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class Job(SqlAlchemyBase):
    __tablename__ = 'jobs'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True,
                           autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String,
                              nullable=False)
    description = sqlalchemy.Column(sqlalchemy.String,
                                    nullable=False)
    author_id = sqlalchemy.Column(sqlalchemy.Integer,
                                  sqlalchemy.ForeignKey('users.id'))
    executor_id = sqlalchemy.Column(sqlalchemy.Integer,
                                    sqlalchemy.ForeignKey('users.id'),
                                    nullable=True)
    status = sqlalchemy.Column(sqlalchemy.String,
                               default='open')  # open, in_progress, completed
    created_at = sqlalchemy.Column(sqlalchemy.DateTime,
                                   default=datetime.datetime.now)

    # Связи
    author = orm.relationship('User', foreign_keys=[author_id])
    executor = orm.relationship('User', foreign_keys=[executor_id])
