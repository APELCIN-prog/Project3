from flask import jsonify, request
from data import db_session
from data.users import User
from data.jobs import Job
from data.responses import Response


def register_api_routes(app):
    #РАБОТЫ

    @app.route('/api/jobs')
    def api_get_jobs():
        with db_session.create_session() as db_sess:
            jobs = db_sess.query(Job).all()
            result = []
            for job in jobs:
                result.append({
                    'id': job.id,
                    'title': job.title,
                    'description': job.description,
                    'author_id': job.author_id,
                    'executor_id': job.executor_id,
                    'author_name': job.author.name if job.author else None,
                    'executor_name': job.executor.name if job.executor else None,
                    'created_at': job.created_at.isoformat()
                })
            return jsonify(result)

    @app.route('/api/jobs/<int:job_id>')
    def api_get_job(job_id):
        with db_session.create_session() as db_sess:
            job = db_sess.query(Job).filter(Job.id == job_id).first()
            if not job:
                return jsonify({'error': 'Работа не найдена'}), 404

            result = {
                'id': job.id,
                'title': job.title,
                'description': job.description,
                'author_id': job.author_id,
                'executor_id': job.executor_id,
                'author_name': job.author.name if job.author else None,
                'executor_name': job.executor.name if job.executor else None,
                'created_at': job.created_at.isoformat()
            }
            return jsonify(result)

    #ПОЛЬЗОВАТЕЛИ

    @app.route('/api/users')
    def api_get_users():
        with db_session.create_session() as db_sess:
            users = db_sess.query(User).all()
            result = []
            for user in users:
                result.append({
                    'id': user.id,
                    'username': user.username,
                    'name': user.name,
                    'email': user.email,
                    'created_at': user.created_at.isoformat()
                })
            return jsonify(result)

    @app.route('/api/users/<int:user_id>')
    def api_get_user(user_id):
        with db_session.create_session() as db_sess:
            user = db_sess.query(User).filter(User.id == user_id).first()
            if not user:
                return jsonify({'error': 'Пользователь не найден'}), 404

            result = {
                'id': user.id,
                'username': user.username,
                'name': user.name,
                'email': user.email,
                'created_at': user.created_at.isoformat()
            }
            return jsonify(result)

    #ОТКЛИКИ

    @app.route('/api/responses/<int:job_id>')
    def api_get_responses(job_id):
        with db_session.create_session() as db_sess:
            responses = db_sess.query(Response).filter(Response.job_id == job_id).all()
            result = []
            for resp in responses:
                result.append({
                    'id': resp.id,
                    'job_id': resp.job_id,
                    'user_id': resp.user_id,
                    'user_name': resp.user.name,
                    'status': resp.status,
                    'created_at': resp.created_at.isoformat()
                })
            return jsonify(result)