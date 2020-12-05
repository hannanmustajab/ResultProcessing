import datetime
import os.path

import pymongo
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from db import courses_collection, collection, merit, chance_memo_collection


class Merit():
    def __init__(self, course_id, EB: bool, chance_memo, sort_on):
        self.course_id = course_id
        dt = datetime.datetime.now()
        self._year = dt.strftime("%Y")
        self.EB = EB
        self.chance_memo = chance_memo
        self.sort_on = sort_on

    def setChanceMemo(self, chance_memo):
        self.chance_memo = chance_memo

    def generateMerit(self):
        result = collection.find({"$and": [{'course': self.course_id}, {'year': str(self._year)}]})
        result_length = collection.count_documents({"$and": [{'course': self.course_id}, {'year': str(self._year)}]})

        final_list = []
        chance_memo_list = []
        SGMCount = 0
        SIMCount = 0
        SEMCount = 0
        rank = 1
        iteration = 0
        # print(iteration)

        # self.printProgressBar(0, result_length, length = 50)

        for student in result:
            first_choice = student['choices'][0]
            roll_number = student['roll_number']
            category = student['category']
            choices = student['choices']
            rel = student['rel']
            completed = False
            alotted = False
            # print(rank)
            # if rank > 500:
            #     break

            if category == 'I':
                """
                    Logic for handling internal students goes here.
                """
                # Case 1: If first choice is available through General Merit.

                query = courses_collection.find_one(
                    {"$and": [{'course': self.course_id}, {'year': str(self._year)}, {'code': first_choice}]})['seats']

                if query['E'] > 0:
                    # print("Available through External")
                    data = {
                        'name': student['name'],
                        'roll_number': roll_number,
                        'branch': first_choice,
                        'choices': choices,
                        'marks': student['marks'],
                        'type': category,
                        'first_choice': True,
                        'confirmed': True,
                        'Rank': "S%03d" % rank,
                        'flag': 'SGM',
                        'year': self._year,
                        'course': self.course_id
                    }
                    alotted = True
                    rank += 1
                    SGMCount += 1
                    final_list.append(data)
                    courses_collection.update_one(
                        {"$and": [{'course': self.course_id}, {'year': str(self._year)}, {'code': first_choice}]},
                        {'$inc': {'seats.E': -1}})

                # Case 2: If first choice is available through Internal Merit.
                elif query['I'] > 0:
                    # print("Available through Internal Merit")
                    data = {
                        'name': student['name'],
                        'roll_number': roll_number,
                        'branch': first_choice,
                        'choices': choices,
                        'marks': student['marks'],
                        'type': category,
                        'first_choice': True,
                        'confirmed': True,
                        'Rank': "S%03d" % rank,
                        'flag': 'SIM',
                        'year': self._year,
                        'course': self.course_id
                    }
                    alotted = True
                    rank += 1
                    SIMCount += 1
                    final_list.append(data)
                    courses_collection.update_one(
                        {"$and": [{'course': self.course_id}, {'year': str(self._year)}, {'code': first_choice}]},
                        {'$inc': {'seats.I': -1}})

                # Case 3: If first choice is not available so alott next available branch.
                else:
                    # print("Checking for different branches")
                    for choice in choices:
                        if courses_collection.find_one({'code': choice})['seats']['I'] > 0:
                            data = {
                                'name': student['name'],
                                'roll_number': roll_number,
                                'branch': choice,
                                'choices': choices,
                                'marks': student['marks'],
                                'type': category,
                                'first_choice': False,
                                'confirmed': True,
                                'Rank': "S%03d" % rank,
                                'flag': 'SIM',
                                'year': self._year,
                                'course': self.course_id
                            }
                            alotted = True
                            rank += 1
                            SIMCount += 1
                            final_list.append(data)
                            courses_collection.update_one(
                                {"$and": [{'course': self.course_id}, {'year': str(self._year)}, {'code': choice}]},
                                {'$inc': {'seats.I': -1}})
                            break

                # If the student is not alotted any branch, Add him to chance memo list.
                if not alotted:
                    data = {
                        'name': student['name'],
                        'roll_number': roll_number,
                        'branch': first_choice,
                        'choices': choices,
                        'marks': student['marks'],
                        'type': category,
                        'first_choice': False,
                        'confirmed': False,
                        'Rank': "0",
                        'flag': rel,
                        'year': self._year,
                        'course': self.course_id,
                        'rel': student['rel']
                    }
                    chance_memo_list.append(data)


            elif category == 'E':
                """
                    Logic for handling External students goes here.
                """
                for choice in choices:
                    subject = courses_collection.find_one(
                        {"$and": [{'course': self.course_id}, {'year': str(self._year)}, {'code': choice}]})

                    if subject['seats']['E'] > 0:
                        data = {
                            'name': student['name'],
                            'roll_number': roll_number,
                            'branch': choice,
                            'choices': choices,
                            'marks': student['marks'],
                            'type': category,
                            'first_choice': "N.A",
                            'confirmed': True,
                            'Rank': "S%03d" % rank,
                            'flag': 'SGM',
                            'year': self._year,
                            'course': self.course_id
                        }
                        alotted = True
                        rank += 1
                        SGMCount += 1
                        final_list.append(data)
                        courses_collection.update_one(
                            {"$and": [{'course': self.course_id}, {'year': str(self._year)}, {'code': choice}]},
                            {'$inc': {'seats.E': -1}})
                        completed = True
                        break

                if completed is False and rel == 'M' and self.EB:
                    for choice in choices:
                        subject = courses_collection.find_one(
                            {"$and": [{'course': self.course_id}, {'year': str(self._year)}, {'code': choice}]})
                        if subject['seats']['EB'] > 0:
                            data = {
                                'name': student['name'],
                                'roll_number': roll_number,
                                'branch': choice,
                                'choices': choices,
                                'marks': student['marks'],
                                'type': category,
                                'first_choice': "N.A",
                                'confirmed': True,
                                'Rank': "S%03d" % rank,
                                'flag': 'SEB',
                                'year': self._year,
                                'course': self.course_id
                            }
                            alotted = True
                            rank += 1
                            SEMCount += 1
                            final_list.append(data)
                            courses_collection.update_one(
                                {"$and": [{'course': self.course_id}, {'year': str(self._year)}, {'code': choice}]},
                                {'$inc': {'seats.EB': -1}})
                            break

                if not alotted:
                    data = {
                        'name': student['name'],
                        'roll_number': roll_number,
                        'branch': first_choice,
                        'choices': choices,
                        'marks': student['marks'],
                        'type': category,
                        'first_choice': False,
                        'confirmed': False,
                        'Rank': "0",
                        'flag': rel,
                        'year': self._year,
                        'course': self.course_id,
                        'rel': student['rel']
                    }
                    chance_memo_list.append(data)

            iteration += 1
            # self.printProgressBar(iteration, result_length, length=50)

        merit.insert_many(final_list)

        # Generate PDF
        fields = ['Name', 'Roll Number', 'Rank', 'Branch', 'Category', 'Marks']
        sort_on = self.sort_on  # Sort on marks or rollnumber
        type = 'select'
        # self.generatePDF(fields, sort_on, type)

        # for student in final_list:
        #     print(
        #         f" Rank: {student['Rank']} {Fore.WHITE}Roll Number: {Fore.BLUE}{student['roll_number']} {Fore.WHITE} Branch Allotted:{Fore.YELLOW} {student['branch']} {Fore.WHITE}First Choice: {Fore.RED}{student['choices'][0]} {Fore.WHITE} Type: {Fore.YELLOW}{student['type']} {Fore.WHITE}  {Fore.WHITE}Marks: {Fore.YELLOW}{student['marks']}  {Fore.WHITE}Flag: {Fore.YELLOW}{student['flag']} ")
        return chance_memo_list

    def generatePDF(self, fields, sort_on, type):

        if type == 'chance_memo':
            cursor = chance_memo_collection.find(
                {"$and": [{'course': self.course_id}, {'year': str(self._year)}]}).sort(sort_on, pymongo.DESCENDING)
        elif type == 'select':
            cursor = merit.find({"$and": [{'course': self.course_id}, {'year': str(self._year)}]}).sort(sort_on,
                                                                                                        pymongo.DESCENDING)

        for data in cursor:
            fields.append(
                [data['name'], data['roll_number'], data['Rank'], data['branch'], data['type'], data['marks']])

        path = f'results/{self._year}/{self.course_id}/'
        file_name = os.path.join(path, f'{type}.pdf')
        header = Paragraph('ALIGARH MUSLIM UNIVERSITY ' * 5)
        pdf = SimpleDocTemplate(
            file_name,
            pagesize=A4,
        )

        table = Table(fields)

        # Add styles to table here
        style = TableStyle([
            ('BACKGROUND', (0, 0), (6, 0), colors.gray),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke)
        ])
        table.setStyle(style)
        rowNumb = len(fields)
        for i in range(1, rowNumb):
            if i % 2 == 0:
                bc = colors.whitesmoke
            else:
                bc = colors.white
            ts = TableStyle(
                [('BACKGROUND', (0, i), (-1, i), bc), ]
            )
            table.setStyle(ts)

        elems = [table]
        pdf.build(elems)

    
        def return_file():
            return file_name

    def generateChanceMemo(self):
        """
        Logic for chance memo goes here.

        :return:
        """
        rank = 1
        chance_memo_list = []
        cursor = {'next': 'ANY'}
        # Get the list excluding selected students.
        list = self.generateMerit()
        while rank <= self.chance_memo:

            # Any candidate
            if cursor['next'] == 'ANY':
                for student in list:
                    first_choice = student['choices'][0]
                    roll_number = student['roll_number']
                    category = student['type']
                    choices = student['choices']
                    # rel = student['rel']
                    flag = student['confirmed']
                    if flag is False:
                        data = {
                            'name': student['name'],
                            'roll_number': roll_number,
                            'branch': first_choice,
                            'choices': choices,
                            'marks': student['marks'],
                            'type': category,
                            'first_choice': False,
                            'confirmed': True,
                            'Rank': "C%03d" % rank,
                            'flag': 'CGM',
                            'year': self._year,
                            'course': self.course_id
                        }
                        chance_memo_list.append(data)
                        rank += 1
                        cursor['next'] = 'I'
                        # print('Given General : Rank', rank)
                        student['confirmed'] = True
                        break

            # Only Internal
            elif cursor['next'] == 'I':
                for student in list:
                    first_choice = student['choices'][0]
                    roll_number = student['roll_number']
                    category = student['type']
                    choices = student['choices']
                    # rel = student['rel']
                    flag = student['confirmed']
                    if flag is False and category == 'I':
                        data = {
                            'name': student['name'],
                            'roll_number': roll_number,
                            'branch': first_choice,
                            'choices': choices,
                            'marks': student['marks'],
                            'type': category,
                            'first_choice': False,
                            'confirmed': True,
                            'Rank': "C%03d" % rank,
                            'flag': 'CIM',
                            'year': self._year,
                            'course': self.course_id
                        }
                        chance_memo_list.append(data)
                        rank += 1
                        if self.EB:
                            cursor['next'] = 'EB'
                        else:
                            cursor['next'] = 'ANY'
                        # print('Given Internal : Rank', rank)
                        student['confirmed'] = True
                        break
            # EB Logic

            elif cursor['next'] == 'EB':
                for student in list:
                    first_choice = student['choices'][0]
                    roll_number = student['roll_number']
                    category = student['type']
                    choices = student['choices']
                    rel = student['rel']
                    flag = student['confirmed']
                    if flag is False and category == 'E' and rel == 'M':
                        data = {
                            'name': student['name'],
                            'roll_number': roll_number,
                            'branch': first_choice,
                            'choices': choices,
                            'marks': student['marks'],
                            'type': category,
                            'first_choice': False,
                            'confirmed': True,
                            'Rank': "C%03d" % rank,
                            'flag': 'CEM',
                            'year': self._year,
                            'course': self.course_id,

                        }
                        chance_memo_list.append(data)
                        rank += 1
                        cursor['next'] = 'ANY'
                        # print('Given Internal : Rank', rank)
                        student['confirmed'] = True
                        break

        # Add chance memo to database.
        chance_memo_collection.insert_many(chance_memo_list)
        """
        Generate PDF for chance memo here.
        """
        # Generate PDF for chance memo here.

        list = [
            ['Name', 'Roll Number', 'Rank', 'Branch', 'Category', 'Marks']
        ]
        sort_on = self.sort_on  # Sort on marks or rollnumber
        type = 'chance_memo'
        # self.generatePDF(list, sort_on, type)

        return chance_memo_list

    def printProgressBar(self, iteration, total, prefix='Progress', suffix='Complete', decimals=1, length=100, fill='█',
                         printEnd="\r"):
        """
        Call in a loop to create terminal progress bar
        @params:
            iteration   - Required  : current iteration (Int)
            total       - Required  : total iterations (Int)
            prefix      - Optional  : prefix string (Str)
            suffix      - Optional  : suffix string (Str)
            decimals    - Optional  : positive number of decimals in percent complete (Int)
            length      - Optional  : character length of bar (Int)
            fill        - Optional  : bar fill character (Str)
            printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
        """
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)
        # Print New Line on Complete
        if iteration == total:
            print()

#
# start = timeit.default_timer()
# btech_merit = Merit(1234, EB=True, chance_memo=400,sort_on='roll_number')
#
# stop = timeit.default_timer()
# print('Time(s): ', stop - start)
