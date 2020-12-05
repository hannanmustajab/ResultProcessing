import csv
from datetime import datetime
import pathlib
import os.path
from db import collection,courses_collection


class Students():
    def __init__(self,course_id,course_name,no_of_choices):
        self.course_id = course_id
        self._list = []
        dt = datetime.now()
        self._year = dt.strftime("%Y")
        self.name = course_name
        self.number_of_choices = no_of_choices

    def __read_students(self,file):
        with open('uploads/'+f'{self.course_id}'+file) as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter=',')
            count = 0
            default = ['COBT', 'LEBT', 'EEBT', 'KEBT', 'PKBT', 'MEBT', 'CEBT']
            for row in csv_reader:
                choices = []
                for i in range(1, self.number_of_choices + 1):
                    if row[f'CRS{i}'] == "":
                        choices = default
                        break
                    if row[f'CRS{i}'] == "ARCB":
                        continue
                    choices.append(row[f'CRS{i}'])

                student = {
                    'name':row['NAME'],
                    'roll_number': row['ROLL'],
                    'marks': row['MARKS'],
                    'category': row['IE'],
                    'choices': choices,
                    'rel': row['REL'],
                    'course':self.course_id,
                    'year':self._year,
                    'course_name':self.name
                }
                self._list.append(student)

        return self._list

    def add_students(self,file):
        if collection.count_documents({'course':self.course_id},limit=1):
            return print("Data already Exists")
        else:
            collection.create_index("roll_number")
            collection.create_index("course")
            query = collection.insert_many(self.__read_students(file))
            self.statistics()
            return f'Students added successfully!'

    def statistics(self):
        totalStudents = collection.count_documents({'course': self.course_id})
        internals = collection.count_documents({'$and': [{'course': self.course_id}, {'category': 'I'}]})
        externals = collection.count_documents({'$and': [{'course': self.course_id}, {'category': 'E'}]})
        print(f"Total students: {totalStudents}")
        print(f"Total Internals: {internals}")
        print(f"Total Externals: {externals}")
        return [totalStudents,internals,externals]

    def find_student(self,roll_number):
        return collection.find_one({'roll_number':roll_number},{'course':self.course_id})


class Courses():
    def __init__(self,course_id):
        self.course_id = course_id
        dt = datetime.now()
        self._year = dt.strftime("%Y")
        self.EB = False

    def setEBCategory(self):
        """
        Set EB category for this course to true or false.
        :return:
        """
        self.EB = True
        return self.EB

    def addBranch(self,code,internal,external,EB=0):
        """
        Add Branch
        :param code: Add the name of the branch which should match the choice. eg : 'ELEB'
        :param internal: Number of internal seats
        :param external: Number of external seats
        :param EB: Number of EB seats
        :return: Total number of seats added.
        """
        #If EB is true
        if self.EB :
            data = {
                'course':self.course_id,
                'year':self._year,
                'code': code,
                'seats':
                    {
                        'I': internal,
                        'E': external,
                        'EB': EB
                    }
            }
        else:
            data = {
                'course': self.course_id,
                'year': self._year,
                'code': code,
                'seats':
                    {
                        'I': internal,
                        'E': external
                    }
            }
        courses_collection.insert_one(data)
        return True

    def statistics(self):
        #TODO: Add number of seats remaining in each branch under each category.
        totalBranches = courses_collection.count_documents({'course': self.course_id})
        print(f"Total Branches : {totalBranches}")
        return totalBranches


"""
Create course here and add students. 
# """

