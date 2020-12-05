from flask_wtf import FlaskForm
from wtforms import TextField, PasswordField, StringField, BooleanField, FileField, SubmitField, IntegerField
from wtforms.validators import DataRequired, EqualTo, Length
from flask_wtf import Form
# Set your classes here.


class AddStudents(FlaskForm):
    name = StringField(
        'Course Name', validators=[DataRequired(), Length(min=2, max=25)]
    )
    course_id = StringField(
        'Course ID', validators=[DataRequired(), Length(min=4, max=4)]
    )

    no_of_choices = IntegerField('Number of choices',validators=[DataRequired()])

    special_category = BooleanField(
        'Special Category'
    )
    file = FileField(
        'File Upload', validators=[DataRequired()]
    )

    submit = SubmitField('Submit')

class AddBranchForm(FlaskForm):
    name = StringField(
        'Name', validators=[DataRequired(), Length(min=2, max=25)]
    )
    internal_seats = IntegerField('Internal', validators=[DataRequired()])
    external_seats = IntegerField('External', validators=[DataRequired()])
    extra_seats = IntegerField('Special ')
    submit = SubmitField('Add Branch')

class GenerateChanceMemoForm(FlaskForm):
    pass