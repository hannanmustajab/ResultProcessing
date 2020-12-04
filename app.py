#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from flask import Flask, render_template, request, redirect, url_for, send_file

from flask_celery import make_celery
# from werkzeug import secure_filename
from db import collection,courses_collection,course_information
from werkzeug.datastructures import FileStorage
import logging

from merit_class import Merit
from student_class import Students,Courses
from logging import Formatter, FileHandler
import os
import io

from forms import AddStudents,AddBranchForm

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
app.config.from_object('config')
app.config['CELERY_BROKER_URL'] ='redis://localhost:6379/0'

celery = make_celery(app)


#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def home():
    return render_template('pages/placeholder.home.html')

# Add new course and students to it.
@app.route('/students/add',methods = ['GET', 'POST'])
def uploadStudents():
    form = AddStudents()
    if form.validate_on_submit():
        filename = form.file.data.filename
        form.file.data.save(filename)
        course_id = form.course_id.data
        course_name = form.name.data
        no_of_choices = form.no_of_choices.data
        special_category = form.special_category.data

        student = Students(course_id,course_name,no_of_choices)
        student.add_students(filename)
        information = {
            'name':course_name,
            'course_id':int(course_id),
            'EB':special_category,
            'no_of_branches':no_of_choices,
            'year':'2020',
            'processed':False
        }
        course_information.insert_one(information)

        course = Courses(course_id)
        if form.special_category.data:
            course.setEBCategory()

        return render_template('pages/placeholder.home.html')

    return render_template('forms/addCourse.html',form=form)

# View the particular Course Page
@app.route('/students/view/<course_id>',methods=['GET','POST'])
def viewStudents(course_id):
    form = AddBranchForm()
    if form.validate_on_submit():
        name = form.name.data
        internal_seats = form.internal_seats.data
        external = form.external_seats.data
        special = form.extra_seats.data
        course = Courses(course_id)
        course.setEBCategory()
        course.addBranch(name,internal_seats,external,special)
    total = collection.count_documents({'course': course_id})
    internals = collection.count_documents({'$and': [{'course': course_id}, {'category': 'I'}]})
    externals = collection.count_documents({'$and': [{'course': course_id}, {'category': 'E'}]})
    record = course_information.find_one({'course_id':int(course_id)})
    courses = courses_collection.find({'course':course_id})
    courses_len = courses_collection.count_documents({'course':course_id})

    return render_template('pages/view_students.html',total=total,courses_len=courses_len,internals=internals,externals=externals,record=record,courses=courses,form=form,course_id=course_id)

# Generate the merit
@app.route('/merit/generate/<course_id>', methods=['GET', 'POST'])
def generateMeritFunction(course_id):
    task = generateMerit(course_id).apply_async()
    return jsonify({}), 202, {'Location': url_for('taskstatus',
                                                  task_id=task.id)}

@app.route('/status/<task_id>')
def taskstatus(task_id):
    task = generateMeritFunction.AsyncResult(task_id)
    if task.state == 'PENDING':
        # job did not start yet
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)

# Generate the merit
@app.route('/pdf/generate/<course_id>', methods=['GET', 'POST'])
def generatePDFRoute(course_id):
    courses = course_information.find()
    return render_template('pages/pdf.html',course_id=course_id,courses=courses)


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')


#----------------------------------------------------------------------------#
# DOWNLOAD PDF
#----------------------------------------------------------------------------#
@app.route('/file-download')
def return_file():
    return send_file(Merit.generatePDF.return_file(), attachment_filename="Result.pdf")

#----------------------------------------------------------------------------#
# ALL CELERY TASKS GO HERE...
#----------------------------------------------------------------------------#

# Create celery task here.
@celery.task(bind=True)
def generateMerit(self,course_id):
    merit = Merit(course_id, EB=True, chance_memo=400, sort_on='marks')
    merit.generateChanceMemo()
    self.update_state(state='PROGRESS')
    course_information.update_one({'course_id': course_id},{'$set':{'processed':True}})
    return { 'status': 'Task completed!'}



#
#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run(debug=True,port='2000')

