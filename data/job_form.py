from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired

class JobsForm(FlaskForm):
    title = StringField('Название работы', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[DataRequired()])

    submit = SubmitField('Создать')