from flask import Flask, render_template, request, redirect, abort
from data import db_session
from data.users import User
from flask_login import login_user, LoginManager, login_required, current_user, logout_user
from data.login_form import LoginForm
from data.jobs import Job
from data.job_form import JobsForm
from data.register_form import RegisterForm
from data.responses import Response
from sqlalchemy.orm import joinedload

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


@app.route("/")
@login_required
def index():
    with db_session.create_session() as db_sess:
        jobs = db_sess.query(Job).filter(Job.author_id != current_user.id).all()
        for job in jobs:
            _ = job.author.name
    return render_template("index.html", jobs=jobs)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')


@login_manager.user_loader
def load_user(user_id):
    with db_session.create_session() as db_sess:
        return db_sess.get(User, int(user_id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        with db_session.create_session() as db_sess:
            user = db_sess.query(User).filter(User.email == form.email.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                return redirect("/")
            return render_template('login.html',
                                   message="Неправильный логин или пароль",
                                   form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        with db_session.create_session() as db_sess:
            if db_sess.query(User).filter(User.email == form.email.data).first():
                return render_template('register.html', title='Регистрация',
                                       form=form, message="Email уже используется")

            if db_sess.query(User).filter(User.username == form.username.data).first():
                return render_template('register.html', title='Регистрация',
                                       form=form, message="Логин уже используется")

            user = User()
            user.username = form.username.data
            user.name = form.name.data
            user.email = form.email.data
            user.set_password(form.password.data)

            db_sess.add(user)
            db_sess.commit()

            login_user(user)
            return redirect('/')

    return render_template('register.html', title='Регистрация', form=form)


@app.route('/add_job', methods=['GET', 'POST'])
@login_required
def add_jobs():
    form = JobsForm()
    if form.validate_on_submit():
        with db_session.create_session() as db_sess:
            job = Job()
            job.title = form.title.data
            job.description = form.description.data
            job.author_id = current_user.id
            db_sess.add(job)
            db_sess.commit()
            return redirect('/')
    return render_template('jobs.html', title='Создание работы', form=form)


@app.route('/jobs/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_jobs(id):
    form = JobsForm()
    with db_session.create_session() as db_sess:
        job = db_sess.query(Job).filter(Job.id == id, Job.author_id == current_user.id).first()

        if not job:
            abort(404)

        if request.method == "GET":
            form.title.data = job.title
            form.description.data = job.description

        if form.validate_on_submit():
            job.title = form.title.data
            job.description = form.description.data
            db_sess.commit()
            return redirect('/profile')

    return render_template('jobs.html', title='Редактирование работы', form=form)


@app.route('/jobs_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def jobs_delete(id):
    with db_session.create_session() as db_sess:
        job = db_sess.query(Job).filter(Job.id == id, Job.author_id == current_user.id).first()

        if job:
            db_sess.delete(job)
            db_sess.commit()
        else:
            abort(404)
    return redirect('/profile')


@app.route('/respond/<int:id>')
@login_required
def respond_to_job(id):
    with db_session.create_session() as db_sess:
        job = db_sess.query(Job).filter(Job.id == id).first()

        if not job or job.author_id == current_user.id:
            abort(404)

        existing = db_sess.query(Response).filter(
            Response.job_id == id,
            Response.user_id == current_user.id,
            Response.status.in_(['pending', 'accepted'])
        ).first()

        if existing:
            if existing.status == 'accepted':
                return "✅ Вы уже выполняете эту работу"
            else:
                return "⏳ Вы уже откликнулись на эту работу. Ожидайте решения автора"

        response = Response()
        response.job_id = id
        response.user_id = current_user.id
        response.status = 'pending'
        db_sess.add(response)
        db_sess.commit()

    return redirect('/')


@app.route('/profile')
@login_required
def profile():
    with db_session.create_session() as db_sess:
        my_jobs = db_sess.query(Job).filter(Job.author_id == current_user.id).all()
        for job in my_jobs:
            _ = len(job.responses)

        pending_responses = db_sess.query(Response).filter(
            Response.user_id == current_user.id,
            Response.status == 'pending'
        ).all()
        pending_jobs = [r.job for r in pending_responses]

        accepted_responses = db_sess.query(Response).filter(
            Response.user_id == current_user.id,
            Response.status == 'accepted'
        ).all()
        accepted_jobs = [r.job for r in accepted_responses]

        for job in pending_jobs + accepted_jobs:
            _ = job.author.name

    return render_template('profile.html',
                           user=current_user,
                           my_jobs=my_jobs,
                           pending_jobs=pending_jobs,
                           accepted_jobs=accepted_jobs)


@app.route('/responses/<int:job_id>')
@login_required
def view_responses(job_id):
    with db_session.create_session() as db_sess:
        job = db_sess.query(Job).filter(Job.id == job_id).first()

        if not job or job.author_id != current_user.id:
            abort(404)

        responses = db_sess.query(Response).filter(Response.job_id == job_id).all()

        for response in responses:
            _ = response.user.name
            _ = response.user.email

    return render_template('responses.html', job=job, responses=responses)


@app.route('/accept_response/<int:response_id>')
@login_required
def accept_response(response_id):
    with db_session.create_session() as db_sess:
        response = db_sess.query(Response).filter(Response.id == response_id).first()

        if not response or response.job.author_id != current_user.id:
            abort(404)

        response.status = 'accepted'
        job = response.job
        job.executor_id = response.user_id
        job.status = 'in_progress'

        other_responses = db_sess.query(Response).filter(
            Response.job_id == job.id,
            Response.id != response_id
        ).all()

        for r in other_responses:
            r.status = 'rejected'

        db_sess.commit()
        job_id = job.id

    return redirect(f'/responses/{job_id}')


@app.route('/reject_response/<int:response_id>')
@login_required
def reject_response(response_id):
    with db_session.create_session() as db_sess:
        response = db_sess.query(Response).filter(Response.id == response_id).first()

        if not response or response.job.author_id != current_user.id:
            abort(404)

        response.status = 'rejected'
        db_sess.commit()
        job_id = response.job.id

    return redirect(f'/responses/{job_id}')


def main():
    db_session.global_init('db/Mydb.db')
    # user1 = User()
    # user1.username = 'APELCIN'
    # user1.name = 'Ваня'
    # user1.email = 'email@email1.ru'
    # user1.set_password('1234')
    #
    # db_sess = db_session.create_session()
    # db_sess.add(user1)
    # db_sess.commit()
    #
    # user2 = User()
    # user2.username = 'A555'
    # user2.name = 'Данил'
    # user2.email = 'email@email2.ru'
    # user2.set_password('123')
    #
    # db_sess = db_session.create_session()
    # db_sess.add(user2)
    # db_sess.commit()

    app.run()


if __name__ == '__main__':
    main()
