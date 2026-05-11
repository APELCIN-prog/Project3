from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired

class JobsForm(FlaskForm):
    title = StringField('Название работы', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[DataRequired()])
    file = FileField('Дополнительный файл (необязательно)',
                     validators=[FileAllowed(['txt', 'md', 'pdf', 'docx'])])
    submit = SubmitField('Создать')