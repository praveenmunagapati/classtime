
import os
import json
from collections import defaultdict

from classtime.logging import logging

from classtime.core import api_manager, db
from classtime.models import Institution, Term, Schedule, Course, Section

import classtime.brain.institutions
import classtime.brain.scheduling as scheduling

def fill_institutions(search_params=None): #pylint: disable=W0613
    db.create_all()
    if Institution.query.first() is None:
        config_file = os.path.join(classtime.brain.institutions.CONFIG_FOLDER_PATH,
            'institutions.json')
        with open(config_file, 'r') as config:
            config = json.loads(config.read())
        institutions = config.get('institutions')
        for institution in institutions:
            if not Institution.query.get(institution.get('institution')):
                db.session.add(Institution(institution))
        try:
            db.session.commit()
        except:
            logging.error('Institutions failed to add to database')
            return None

api_manager.create_api(Institution,
                       collection_name='institutions',
                       methods=['GET'],
                       preprocessors={
                           'GET_MANY': [fill_institutions]
                       },
                       url_prefix='/api/v1')

api_manager.create_api(Term,
                       collection_name='terms',
                       methods=['GET'],
                       exclude_columns=['courses', 'courses.sections'],
                       url_prefix='/api/v1')

api_manager.create_api(Schedule,
                       collection_name='schedules',
                       methods=['GET'],
                       url_prefix='/api/v1')

api_manager.create_api(Course,
                       collection_name='courses',
                       methods=['GET'],
                       exclude_columns=['sections'],
                       url_prefix='/api/v1')

def courses_min_order_faculty_subject(search_params=None):
    if search_params is None:
        return
    if 'order_by' not in search_params:
        search_params['order_by'] = list()
    search_params['order_by'].extend([
        {
            'field': 'faculty',
            'direction': 'asc'
        },
        {
            'field': 'subject',
            'direction': 'asc'
        },
        {
            'field': 'asString',
            'direction': 'asc'
        }
    ])

def courses_min_structured(result=None, search_params=None):
    """Depends on result list being sorted by:
    - faculty, then subject, then asString
    """
    def new_list_and_set():
        return list(defaultdict(list)), set()
    if result is None:
        return
    obj_courses = result['objects']
    faculty_list, faculty_set = new_list_and_set()
    subject_list, subject_set = new_list_and_set()
    for course in obj_courses:
        if course.get('faculty') not in faculty_set:
            faculty_set.add(course.get('faculty'))
            faculty_list.append({
                'faculty': course.get('faculty'),
                'subjects': list()
            })
            subject_list, subject_set = new_list_and_set()

        if course.get('subject') not in subject_set:
            subject_set.add(course.get('subject'))
            subject_list.append({
                'subject': course.get('subject'),
                'subjectTitle': course.get('subjectTitle'),
                'courses': list()
            })
            faculty_list[-1]['subjects'] = subject_list

        subject_list[-1]['courses'].append({
            'course': course.get('course'),
            'asString': course.get('asString'),
            'courseTitle': course.get('courseTitle')
        })
    result['objects'] = faculty_list
    return

COURSES_PER_PAGE = 1000
api_manager.create_api(Course,
                       collection_name='courses-min',
                       methods=['GET'],
                       include_columns=['asString',
                                        'faculty',
                                        'subject',
                                        'subjectTitle',
                                        'course',
                                        'courseTitle'],
                       preprocessors={
                           'GET_MANY': [courses_min_order_faculty_subject]
                       },
                       postprocessors={
                           'GET_MANY': [courses_min_structured]
                       },
                       results_per_page=COURSES_PER_PAGE,
                       max_results_per_page=COURSES_PER_PAGE,
                       url_prefix='/api/v1')

  
# --------------------------------
# Schedule Generation
# --------------------------------

NUM_SCHEDULES = 50
def find_schedules(result=None, search_params=None):
    if result is None:
        result = dict()
    result['page'] = 1
    result['total_pages'] = 1

    schedules = scheduling.find_schedules(search_params, NUM_SCHEDULES)
    result['num_results'] = len(schedules)
    result['objects'] = list()
    for schedule in schedules:
        result['objects'].append({
            'sections': schedule.sections,
            'more_like_this': schedule.more_like_this
        })
    return

api_manager.create_api(Section,
                       collection_name='generate-schedules',
                       include_columns=[],
                       methods=['GET'],
                       postprocessors={
                           'GET_MANY': [find_schedules]
                       },
                       url_prefix='/api/v1')
