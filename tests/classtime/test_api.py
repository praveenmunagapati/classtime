
from __future__ import absolute_import

import json

from classtime import app
from classtime.core import db

class TestAPI(object):

    @classmethod
    def setup_class(cls):
        app.config['TESTING'] = True
        cls.client = app.test_client()
        db.create_all()

    @classmethod
    def teardown_class(cls):
        db.drop_all()

    def setup(self):
        pass

    def teardown(self):
        pass

    def get(self, endpoint, query=None):
        if query is not None:
            querystring = "?q=" + json.dumps(query.get('q'))
            assert querystring.count('q=') == 1
            endpoint += querystring
        return json.loads(self.client.get(endpoint).data)

    def test_institutions(self):
        response = self.get('/api/v1/institutions')
        assert_valid_response(response)

    def test_terms(self):
        response = self.get('/api/v1/terms')
        assert_valid_response(response)

    def test_terms_with_query(self):
        query = {
            "q": {
                "filters": [
                    {
                        "name": "institution",
                        "op": "equals",
                        "val": "ualberta"
                    }
                ]
            }
        }
        response = self.get('/api/terms', query)
        assert_valid_response(response)

    def test_courses(self):
        response = self.get('/api/v1/courses')
        assert_valid_response(response)

    def test_courses_with_query(self):
        filters = [
            {
                "name": "institution",
                "op": "equals",
                "val": "ualberta"
            },
            {
                "name": "term",
                "op": "equals",
                "val": "1490"
            }
        ]
        query = {
            "q": {
                  "filters": filters
            }
        }
        response = self.get('/api/courses', query)
        assert_valid_response(response)

    def test_courses_min(self):
        response = self.get('/api/v1/courses-min')
        assert_valid_response(response)

    def test_courses_min_with_query(self):
        filters = [
            {
                "name": "institution",
                "op": "equals",
                "val": "ualberta"
            },
            {
                "name": "term",
                "op": "equals",
                "val": "1490"
            }
        ]
        query = {
            "q": {
                  "filters": filters
            }
        }
        response = self.get('/api/courses-min', query)
        assert_valid_response(response)

    def test_generate_schedules(self):
        queries = [
            {
                "q": {  # Fall 2015 ECE 304, has 3 components and has a dependency, github.com/rosshamish/classtime/issues/98
                        "institution": "ualberta",
                        "term": "1530",
                        "courses": ["105005"] # ECE 304
                }
            },
            {
                "q": {  # Fall 2015 MEC E 460, has 3 components and has a dependency, github.com/rosshamish/classtime/issues/98
                        "institution": "ualberta",
                        "term": "1530",
                        "courses": ["094556"] # MEC E 460
                }
            },
            {
                "q": {  # Fall 2015 EN PH 131, has 3 components and has a dependency, github.com/rosshamish/classtime/issues/98v
                        "institution": "ualberta",
                        "term": "1530",
                        "courses": ["004051"] # EN PH 131
                }
            },
            {
                "q": {  # Random courses
                        "institution": "ualberta",
                        "term": "1490",
                        "courses": ["001343",
                                    "009019"],
                        "busy-times": [{
                            "day": "MWF",
                            "startTime": "04:00 PM",
                            "endTime": "06:00 PM"
                            }
                        ]
                }
            },
            {
                "q": {  # 1st year engineering 2014 Fall Term
                        "institution": "ualberta",
                        "term": "1490",
                        "courses": ["001343",
                                    "004093",
                                    "004096",
                                    "006768",
                                    "009019"],
                        "busy-times": []
                }
            },
            {
                "q": {  # 3rd year CompE 2014 Fall Term
                        "institution": "ualberta",
                        "term": "1490",
                        "courses": ["010344",
                                    "105014",
                                    "105006",
                                    "105471",
                                    "006708",
                                    "010812"]
                }
            },
            {
                "q": {  # 2nd year MecE Fall Term 2014
                        "institution": "ualberta",
                        "term": "1490",
                        "courses": ["006973", # MEC E 260
                                    "006790", # MATH 209
                                    "006974", # MEC E 265
                                    "098325", # MEC E 230
                                    "001607", # CIV E 270
                                    "004104", # ENGG 299
                                    ]
                }
            },
            {
                "q": {  # 2nd year MecE Fall Term 2014
                        "institution": "ualberta",
                        "term": "1490",
                        "courses": ["006973", # MEC E 260
                                    "006790", # MATH 209
                                    "006974", # MEC E 265
                                    "098325", # MEC E 230
                                    ],
                        "electives": [
                            {
                                "courses": ["001607", # CIV E 270
                                            "004104", # ENGG 299
                                           ]
                            }
                        ]
                        }
            },
            {
                "q": {  # 1st year engineering Fall Term 2014
                        # With tons of busy time
                        "institution": "ualberta",
                        "term": "1490",
                        "courses": ["001343",
                                    "004093",
                                    "004096",
                                    "006768",
                                    "009019"],
                        "busy-times": [
                            {
                                "day": "MWF",
                                "startTime": "07:00 AM",
                                "endTime": "09:50 AM"
                            },
                            {
                                "day": "TR",
                                "startTime": "04:00 PM",
                                "endTime": "10:00 PM"
                            }
                        ]
                },
                "zero_expected": True
            },
            {
                "q": {  # 1st year engineering Fall Term 2014
                        # With the elective (6th course, complementary elec)
                        "institution": "ualberta",
                        "term": "1490",
                        "courses": ["001343", # Chem 103
                                    "004093",
                                    "004096",
                                    "006768",
                                    "009019"],
                        "electives": [
                            {
                                "courses": ["000268", # Anthr 101
                                            "000269", # Anthr 110
                                            "000270", # Anthr 150
                                            ]
                            }
                        ]
                }
            },
            {
                "q": {  # 1st year engineering Fall Term 2014
                        # preferences => start late, marathon class blocks
                        "institution": "ualberta",
                        "term": "1490",
                        "courses": ["001343", # Chem 103
                                    "004093",
                                    "004096",
                                    "006768",
                                    "009019"],
                        "electives": [
                            {
                                "courses": ["000268", # Anthr 101
                                            "000269", # Anthr 110
                                            "000270", # Anthr 150
                                            ]
                            }
                        ],
                        "preferences": {
                            "start-early": -10,
                            "no-marathons": -10
                        }
                }
            },
            {
                "q": {  # 1st year engineering Fall Term 2014
                        # get realtime open/closed & active/cancelled status
                        # obey open/closed & active/cancelled status
                        "institution": "ualberta",
                        "term": "1490",
                        "courses": ["001343", # Chem 103
                                    "004093",
                                    "004096",
                                    "006768",
                                    "009019"],
                        "electives": [
                            {
                                "courses": ["000268", # Anthr 101
                                            "000269", # Anthr 110
                                            "000270", # Anthr 150
                                            ]
                            }
                        ],
                        "preferences": {
                            "start-early": -10,
                            "no-marathons": -10,
                            "current-status": True, # 'true' in javascript
                            "obey-status": True # 'true' in javascript
                        }
                }
            }
        ]
        for query in queries:
            response = self.get('/api/v1/generate-schedules', query)
            assert_valid_response(response)
            schedules = response.get('objects')
            yield assert_valid_schedules, schedules, query

def assert_valid_response(response):
    assert response.get('num_results') is not None
    assert response.get('objects') is not None
    assert response.get('page') is not None
    assert response.get('total_pages') is not None

def assert_valid_schedules(schedules, query):
    if 'zero_expected' in query and query['zero_expected'] == True:
        assert len(schedules) == 0
    else:
        assert len(schedules) > 0
    for schedule in schedules:
        assert 'sections' in schedule
        sections = schedule.get('sections')
        assert len(sections) > 0
        for section in sections:
            assert section.get('institution') == query['q']['institution']
            assert section.get('term') == query['q']['term']

            assert section.get('asString') is not None
            elective_courses = [course
                for elective in query['q'].get('electives', dict())
                for course in elective.get('courses')]
            assert section.get('course') in query['q']['courses'] \
                or section.get('course') in elective_courses
            assert section.get('component') is not None
