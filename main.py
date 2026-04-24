from flask import Flask, render_template, request, redirect, abort
from data import db_session
from data.users import User
from flask_login import login_user, LoginManager, login_required, current_user, logout_user
from data.login_form import LoginForm
from data.jobs import Job
from data.job_form import JobsForm
from data.register_form import RegisterForm

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'




@app.route("/")
def index():
    db_sess = db_session.create_session()
    jobs = db_sess.query(Job).filter(Job.status != 'in_progress')
    return render_template("index.html", jobs=jobs)



@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(User, user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
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
        db_sess = db_session.create_session()

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
        db_sess = db_session.create_session()
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
    db_sess = db_session.create_session()
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
        return redirect('/')

    return render_template('jobs.html', title='Редактирование работы', form=form)


@app.route('/jobs_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def jobs_delete(id):
    db_sess = db_session.create_session()
    job = db_sess.query(Job).filter(Job.id == id, Job.author_id == current_user.id).first()

    if job:
        db_sess.delete(job)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/take_job/<int:id>')
@login_required
def take_job(id):
    db_sess = db_session.create_session()
    job = db_sess.query(Job).filter(Job.id == id, Job.status == 'open').first()

    if job and job.author_id != current_user.id:
        job.status = 'in_progress'
        job.executor_id = current_user.id
        db_sess.commit()

    return redirect('/')


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

    app.run()


if __name__ == '__main__':
    main()
