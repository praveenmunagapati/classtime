=======
The API
=======

Responses are communicated in `JavaScript Object Notation (javascript) <http://javascript.org>`__. Each endpoint returns a list of ``objects``. A few useful book-keeping items are also included in each response.

.. code:: javascript

    {
        "num_results": <int>,
        "objects": [
            {
                <key>: <value>,
                <key>: <value>,
                ...
                <key>: <value>
            },
            { <response object 2> },
            ...
            { <response object N> }
        ],
        "page": <int>,
        "total_pages": <int>
    }

The exception is :ref:`api/v1/courses/\<course> <api-courses>`, which returns a single object (not a list), and no book-keeping items.

It is possible for zero ``<response object>``\ s to be returned.

--------------------------------------

Versioning
~~~~~~~~~~

Versions should be assumed incompatible with one another. Versions are prefixed with their version number. A maximum of 2 versions will be supported at any one time.

Current versions, with their prefixes.

- v0 ``/api/<endpoint>`` (deprecated)
- v1 ``/api/v1/<endpoint>``

Pagination
~~~~~~~~~~

Each response includes:
 * ``page`` := page number returned
 * ``total_pages`` := total number of pages

To get the nth page, append ``?page=<n>`` to any endpoint::

 GET /api/v1/courses-min?page=2

If you are using a search query, append the page number with ``&``::

 GET /api/v1/courses-min?q=<search_query>&page=2

 Compression
 ~~~~~~~~~~~

 All responses are compressed with gzip. Your client should handle the gzipping automagically for you. You shouldn't need to worry about this at all.

--------------------------------------

Search queries
~~~~~~~~~~~~~~

`Search queries <http://flask-restless.readthedocs.org/en/latest/searchformat.html#searchformat>`__ are used to restrict an endpoint's output. This is useful both for performance and semantic reasons.

Format is::

 /api/v1/<endpoint>?q={"filters":[{"name":<attribute_name>,"op":<comparison>,"val":<attribute_value>},{ ... },...]}

Examples:

 * Get courses for a certain institution and a certain term::

	 GET /api/v1/courses-min?q={"filters":[{"name":"institution","op":"equals","val":"ualberta"},{"name":"term","op":"equals","val":"1490"}]}

 * Get terms for a certain institution::

 	 GET /api/v1/terms?q={"filters":[{"name":"institution","op":"equals","val":"ualberta"}]}

Available operators `listed here <http://flask-restless.readthedocs.org/en/latest/searchformat.html#operators>`__. As of this writing, they are::

    ==, eq, equals, equals_to
    !=, neq, does_not_equal, not_equal_to
    >, gt, <, lt
    >=, ge, gte, geq, <=, le, lte, leq
    in, not_in
    is_null, is_not_null
    like
    has
    any

--------------------------------------


Formats used in responses
~~~~~~~~~~~~~~~~~~~~~~~~~

.. _day-format:

Day format
''''''''''

String containing one or more of the characters "MTWRF", with each
corresponding to a day from Monday through Friday.

| eg "MWF"
| eg "TR"

.. _time-format:

Time format
'''''''''''

"HH:MM XM"

:HH: 2-digit hour between 00 and 12
:MM: 2-digit minute between 00 and 59
:X: ``A`` or ``P``

| eg "08:00 AM"
| eg "09:50 PM"

--------------------------------------

.. _api-institutions:

api/v1/institutions
~~~~~~~~~~~~~~~~

Retrieve a list of available institutions. Each institution contains all available information.

Request
'''''''

::

 GET localhost:5000/api/v1/institutions

Response
''''''''

.. code:: javascript

    {
        "objects": [
            {
                "institution": "ualberta",
                "name": "University of Alberta"
            },
            { <institution object 2> },
            ...
            { <institution object N> }
        ]
        ...
    }

:objects: list of <institution object>s

.. _institution-identifier:
.. _api-institution-object:

<institution object>
--------------------

:institution: variable length institution identifier
:name: semantic institution name

.. _api-terms:

api/v1/terms
~~~~~~~~~

Retrieve a list of available terms. Each term contains all available information.

Request
'''''''

::

 GET localhost:5000/api/v1/terms

Response
''''''''

.. code:: javascript

    {
        "objects": [
            {
                "endDate": "2007-12-05",
                "startDate": "2007-09-05",
                "term": "1210",
                "termTitle": "Fall Term 2007"
            },
            { <term object 2> },
            ...
            { <term object N> }
        ],
        ...
    }

:objects: list of <term object>s

.. _api-term-object:
.. _4-digit-term-identifier:

<term object>
-------------

:endDate: YYYY-MM-DD
:startDate: YYYY-MM-DD
:term: 4-digit term identifier
:termTitle: semantic term name

.. _api-courses-min:

api/v1/courses-min
~~~~~~~~~~~~~~~

Quickly retrieve a hierarchy of available courses.

Each course object contains only essential information. More detailed information about a specific course is retrieved with :ref:`/api/v1/courses <api-courses>`.

Request
'''''''

::
 
 GET localhost:5000/api/v1/courses-min

Response
''''''''

.. code:: javascript

    objects = [
        {
            "faculty": "Faculty of Business",
            "subjects": [
                {
                  "subject": "ACCTG",
                  "subjectTitle": "Accounting",
                  "courses": [
                         {
                              "course": "000001",
                              "asString": "ACCTG 300",
                              "courseTitle": "Intermediate Accounting"
                         },
                         { <course object> }
                         ...
                   ]
               },
               { <subject object> }
               ...
            ]
        },
        { <faculty object> }
        ...
    ]

:objects: list of :ref:`faculty objects <api-faculty-object>`

.. _api-faculty-object:

<faculty object>
----------------

:faculty: semantic faculty name
:subjects: list of :ref:`subject objects <api-subject-object>`

.. _api-subject-object:

<subject object>
----------------

:subject: variable-length subject identifier
:subjectTitle: semantic subject name
:courses: list of :ref:`course-min objects <api-course-min-object>`

.. _api-course-min-object:
.. _6-digit-course-identifier:

<course-min object>
-------------------

:course: 6-digit course identifier
:asString: <subject> <level>
:courseTitle: semantic course name

.. _api-courses:

api/v1/courses/<course>
~~~~~~~~~~~~~~~~~~~~

Retrieve detailed information about a single course.

Request
'''''''

::

 GET localhost:5000/api/v1/courses/<course>

:course: :ref:`6-digit unique course identifier <6-digit-course-identifier>`

Response
''''''''

.. code:: javascript

    {
        "asString": "ACCTG 300",
        "career": "UGRD",
        "catalog": 300,
        "course": "000001",
        "courseDescription": "Provides a basic understanding of accounting: how accounting numbers 
            are generated, the meaning of accounting reports, and how to use accounting reports to 
            make decisions. Note: Not open to students registered in the Faculty of Business. Not 
            for credit in the Bachelor of Commerce Program.",
        "courseTitle": "Introduction to Accounting",
        "department": "Department of Accounting, Operations and Information Systems",
        "departmentCode": "AOIS",
        "faculty": "Faculty of Business",
        "facultyCode": "BC",
        "subject": "ACCTG",
        "subjectTitle": "Accounting",
        "term": "1490",
        "units": 3
    }

:asString: <subject> <level>
:career: variable-length abbrevation of university program type (undergrad, grad, ..)
:catalog: catalog id
:course: :ref:`6-digit unique course identifier <6-digit-course-identifier>`
:courseDescription: often long description of the course
:courseTitle: semantic course name
:department: semantic department name
:departmentCode: variable-length department identifier
:faculty: semantic faculty name
:facultyCode: variable-length faculty identifier
:subject: variable-length subject identifier
:subjectTitle: semantic subject name
:term: :ref:`4-digit unique term identifier <4-digit-term-identifier>`
:units: integer weight of the course

.. _api-generate-schedules:

api/v1/generate-schedules
~~~~~~~~~~~~~~~~~~~~~~

Request
'''''''

::
 
 GET localhost:5000/api/v1/generate-schedules?q=<q>

::

 q = {
        "institution": institution,
        "term": term,
        "courses": [course, course2, .., courseN],
        "busy-times": [
            {
                "day": "[MTWRF]{1,5}"
                "startTime": "##:## [AP]M",
                "endTime": "##:## [AP]M"
            },
            { <busytime object_2> },
            ...
            { <busytime object_n> }
        ],
        "electives": [
            {
                "courses": [course, course2, .., courseN]
            },
            { <electives object_2> },
            ...
            { <electives object_n> }
        ],
        "preferences": {
            "start-early": <integer>,
            "no-marathons": <integer>,
            "day-classes": <integer>,

            "current-status": <boolean>,
            "obey-status": <boolean>
        }

 }

See the method ``TestAPI.test_generate_schedules`` in ``tests/angular_flask/test_api.py`` for concrete examples.

:institution: :ref:`unique institution identifier <institution-identifier>`
:term: :ref:`4-digit unique term identifier <4-digit-term-identifier>`
:courses: list of :ref:`6-digit unique course identifier <6-digit-course-identifier>`
:busy-times: (optional) list of <busytime> objects
:electives: (optional) list of <electives> objects
:preferences: (optional) specify the weight of each :ref:`preference <api-preference-identifier>`. There are sensible defaults.

.. _api-busytime-object:

<busytime object>
-----------------

:day: day(s) which are busy. Uses :ref:`day format <day-format>`
:startTime: time the user starts being busy. Uses :ref:`time format <time-format>`
:endTime: time the user is not busy anymore. Uses :ref:`time format <time-format>`. 

.. _api-electives-object:

<electives object>
------------------

:courses: list of :ref:`course identifiers <6-digit-course-identifier>`

One course from each <electives object>'s ``courses`` list will be present in each schedule.

.. _api-preference-identifier:

Preferences
-----------

In `preferences`, each key's value is the preference's **weighting**.  
Positive, negative, and zero-valued weightings are described for each preference type.

There are sensible defaults for each preference, and all preferences are optional.

Currently supported preferences:

- ``no-marathons``
    - ``weight > 0`` = avoid long stretches of classes in a row
    - ``weight < 0`` = prefer long stretches of classes in a row
    - ``weight = 0`` = no preference

- ``day-classes``
    - ``weight > 0`` = prefer daytime classes
    - ``weight < 0`` = prefer night classes (5pm and on)
    - ``weight = 0`` = no preference

- ``start-early``
    - ``weight > 0`` = prefer early starts
    - ``weight < 0`` = prefer late starts
    - ``weight = 0`` = no preference

> Note: ``start-early`` can be used in tandem with ``busy_times`` to specify *how* early to start

There is also:

- ``current-status``
    - a boolean: ``true`` or ``false``
    - specifies whether the open/closed and active/cancelled status of sections should be updated
- ``obey-status``
    - a boolean: ``true`` or ``false``
    - specifies whether the open/closed and active/cancelled status of sections should be respected when scheduling
    - if true, closed or cancelled sections will not be scheduled


Response
''''''''

.. code:: javascript

    {
        "objects": [
            {
                "sections": [
                    {
                        ...
                        <course attributes>
                        ...
                        "class_": "62293",
                        "component": "LEC",
                        "day": "MWF",
                        "startTime": "10:00 AM",
                        "endTime": "10:50 AM",
                        ...
                        "section": "A02",
                        "campus": "MAIN",
                        "capacity": 0,
                        "instructorUid": "jdavis",
                        "location": "CCIS L2 190"
                    },
                    { <section object 2> },
                    ...
                    { <section object N> }
                ],
                "more_like_this": [<schedule-identifier>, <schedule-identifier>, ..]
            },
            { <schedule object 2> },
            ...
            { <schedule object M> }
        ],
        ...
    }

:objects: list of :ref:`schedule objects <api-schedule-object>`

.. _api-schedule-object:

<schedule object>
-----------------
:sections: list of :ref:`section objects <api-section-object>`
:more_like_this: list of :ref:`schedule identifiers <api-schedule-identifier>`

.. _5-digit-section-identifier:
.. _api-section-object:

<section object>
---------------- 

:<course attributes>: all attributes from the parent :ref:`course <api-courses>` object

:class\_: 5-digit unique section identifier
:component: section type identifier, often 'LEC', 'LAB', 'SEM', 'LBL'
:day: day(s) the section is on. Uses :ref:`day format <day-format>`
:startTime: time the section begins. Uses :ref:`time format <time-format>`
:endTime: time the section ends. Uses :ref:`time format <time-format>`

:section: section identifier. usually a letter and a number
:campus: variable-length campus identifier
:capacity: number of seats
:instructorUid: instructor identifier
:location: semantic location name

.. _api-schedule-identifier:

<schedule-identifier>
---------------------

:schedule-identifier: variable length unique schedule identifier. Details about the schedule
                      can be obtained by accessing :ref:`api/v1/schedules <api-schedules>` and
                      passing in this identifier.

.. _api-schedules:

api/v1/schedules
~~~~~~~~~~~~~~~~~~~~~~

Request
'''''''

::

 GET localhost:5000/api/v1/schedules/<schedule-identifier>

:course: :ref:`schedule identifier <api-schedule-identifier>`

Response
''''''''
.. code:: javascript

    {
        "hash_id": "48c3df652685a23acd9a759b91f25b",
        "institution": "ualberta",
        "term": "1490",
        "sections": [
            {
                "asString": "ENGG 100 LEC A2",
                "autoEnroll": null,
                "campus": "MAIN",
                "capacity": 516,
                "classNotes": null,
                "classStatus": "A",
                "classType": "E",
                "class_": "61383",
                "component": "LEC",
                "course": "004093",
                "day": "R",
                "endTime": "01:50 PM",
                "enrollStatus": "O",
                "institution": "ualberta",
                "instructorUid": null,
                "location": "CCIS 1 430",
                "schedule": null,
                "section": "A2",
                "session": "Regular Academic Session",
                "startTime": "01:00 PM",
                "term": "1490"
            },
            ... < more section objects >
        ]
    }
