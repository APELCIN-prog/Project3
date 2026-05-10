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
from data.messages import Message


app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


@app.route("/")
@login_required
def index():
    search_query = request.args.get('q', '').strip()

    with db_session.create_session() as db_sess:
        query = db_sess.query(Job).options(joinedload(Job.author), joinedload(Job.responses)).filter(
            Job.author_id != current_user.id)

        if search_query:
            query = query.filter(
                (Job.title.ilike(f"%{search_query}%")) |
                (Job.description.ilike(f"%{search_query}%"))
            )

        jobs = query.all()

    return render_template("index.html", jobs=jobs, search_query=search_query)


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
        # 1. Мои созданные работы (с откликами)
        my_jobs = db_sess.query(Job).options(joinedload(Job.responses)) \
            .filter(Job.author_id == current_user.id).all()

        # 2. Ожидают одобрения (с авторами работ)
        pending_responses = db_sess.query(Response).options(
            joinedload(Response.job).joinedload(Job.author)
        ).filter(
            Response.user_id == current_user.id,
            Response.status == 'pending'
        ).all()
        pending_jobs = [r.job for r in pending_responses]

        # 3. Мои выполняемые работы
        # Работы, где я — автор (и работа в процессе)
        my_hiring = db_sess.query(Job).options(
            joinedload(Job.executor),
            joinedload(Job.author)
        ).filter(
            Job.author_id == current_user.id,
            Job.status == 'in_progress'
        ).all()

        # Работы, где я — исполнитель (с авторами работ)
        my_work = db_sess.query(Job).options(
            joinedload(Job.author)
        ).filter(
            Job.executor_id == current_user.id,
            Job.status == 'in_progress'
        ).all()

        accepted_jobs = my_hiring + my_work

    return render_template('profile.html',
                           user=current_user,
                           my_jobs=my_jobs,
                           pending_jobs=pending_jobs,
                           accepted_jobs=accepted_jobs)


@app.route('/responses/<int:job_id>')
@login_required
def view_responses(job_id):
    with db_session.create_session() as db_sess:
        # 1. Получаем саму работу (проверяем права доступа)
        job = db_sess.query(Job).filter(Job.id == job_id).first()

        if not job or job.author_id != current_user.id:
            abort(404)

        # 2. Получаем список откликов.
        responses = db_sess.query(Response).options(joinedload(Response.user)) \
            .filter(Response.job_id == job_id).all()

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


@app.route('/send_message/<int:job_id>', methods=['POST'])
@login_required
def send_message(job_id):
    text = request.form.get('text')
    if not text:
        abort(400)

    with db_session.create_session() as db_sess:
        job = db_sess.query(Job).filter(
            Job.id == job_id,
            Job.status == 'in_progress',
            # Даем доступ, если я автор ИЛИ я исполнитель
            ((Job.author_id == current_user.id) | (Job.executor_id == current_user.id))
        ).first()

        if not job:
            abort(403)

        message = Message()
        message.text = text
        message.user_id = current_user.id
        message.job_id = job_id

        db_sess.add(message)
        db_sess.commit()

    return redirect(f'/chat/{job_id}')


@app.route('/chat/<int:job_id>')
@login_required
def chat(job_id):
    with db_session.create_session() as db_sess:
        job = db_sess.query(Job).filter(Job.id == job_id).first()

        if not job or (job.author_id != current_user.id and job.executor_id != current_user.id):
            abort(403)

        messages = db_sess.query(Message).options(joinedload(Message.user)).filter(
            Message.job_id == job_id
        ).order_by(Message.created_date).all()

    return render_template('chat.html', job=job, messages=messages)


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
