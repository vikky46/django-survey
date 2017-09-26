# -*- coding: utf-8 -*-

from __future__ import (
    absolute_import, division, print_function, unicode_literals
)

from builtins import str

from django.core.exceptions import ValidationError
from future import standard_library

from survey.models import Answer, Question, Response, Survey
from survey.tests.models import BaseModelTest

standard_library.install_aliases()


class TestQuestion(BaseModelTest):

    def setUp(self):
        BaseModelTest.setUp(self)
        text = "Lorem ipsum dolor sit amët, <strong> consectetur </strong> \
adipiscing elit."
        self.question = Question.objects.get(text=text)
        self.questions[0].choices = "abé cé, Abë-cè, Abé Cé, dé, Dé, dë"
        survey = Survey.objects.create(
            name="Test", is_published=True, need_logged_user=False,
            display_by_question=False
        )
        for choice in self.questions[0].choices.split(", "):
            Answer.objects.create(
                question=self.questions[0], body=choice,
                response=Response.objects.create(survey=survey)
            )
        # Shortcut for the first question's answer cardinality's function
        self.ac = self.questions[0].answers_cardinality
        self.sac = self.questions[0].sorted_answers_cardinality

    def test_unicode(self):
        """ Unicode generation. """
        self.assertIsNotNone(str(self.questions[0]))

    def test_get_choices(self):
        """ We can get a list of choices for a widget from choices text. """
        self.questions[0].choices = "A éa,B éb"
        self.assertEqual(self.questions[0].get_choices(),
                         (('a-ea', 'A éa'), ('b-eb', 'B éb')))
        self.questions[0].choices = "A()a,  ,C()c"
        self.assertEqual(self.questions[0].get_choices(),
                         (('aa', 'A()a'), ('cc', 'C()c')))

    def test_validate_choices(self):
        """  List are validated for comma. """
        question = Question.objects.create(
            text="Q?", choices="a,b,c", order=1, required=True,
            survey=self.survey, type=Question.SELECT_MULTIPLE
        )
        question.choices = "a"
        self.assertRaises(ValidationError, question.save)
        question.choices = ",a"
        self.assertRaises(ValidationError, question.save)
        question.choices = "a,"
        self.assertRaises(ValidationError, question.save)
        question.choices = ",a,  ,"
        self.assertRaises(ValidationError, question.save)

    def test_answers_as_text(self):
        """ We can get a list of answers to this question. """
        qat = self.question.answers_as_text
        self.assertEqual(3, len(qat))
        expected = [u"Yës", 'Maybe', u"Yës"]
        expected.sort()
        qat.sort()
        self.assertEqual(qat, expected)

    def test_answers_cardinality(self):
        """ We can get the cardinality of each answers. """
        self.assertEqual(self.question.answers_cardinality(),
                         {u"Maybe": 1, u"Yës": 2})
        self.assertEqual(self.question.answers_cardinality(min_cardinality=2),
                         {"Other": 1, u"Yës": 2})
        question = Question.objects.get(text="Ipsum dolor sit amët, <strong> \
consectetur </strong>  adipiscing elit.")
        self.assertEqual({'No': 1, "Yës": 1},
                         question.answers_cardinality())
        question = Question.objects.get(text="Dolor sit amët, <strong> \
consectetur</strong>  adipiscing elit.")
        self.assertEqual({'': 1, 'Text for a response': 1},
                         question.answers_cardinality())
        question = Question.objects.get(text="Ipsum dolor sit amët, consectetur\
 <strong> adipiscing </strong> elit.")
        self.assertEqual({'1': 1, "2": 1}, question.answers_cardinality())
        question = Question.objects.get(text="Dolor sit amët, consectetur<stron\
g>  adipiscing</strong>  elit.")
        self.assertEqual({'No': 1, 'Whatever': 1, 'Yës': 1},
                         question.answers_cardinality())
        self.assertEqual(
            {'Näh': 2, 'Yës': 1},
            question.answers_cardinality(
                group_together={"Näh": ["No", "Whatever"]}
            )
        )

    def test_answers_cardinality_grouped(self):
        """ We can group answers foself.sac letter case or slugifying. """
        self.assertEqual(self.ac(), {'abé cé': 1, 'Abé Cé': 1, 'Abë-cè': 1,
                                     'dé': 1, 'dë': 1, 'Dé': 1, })
        rslt = self.ac(group_together={"ABC": ["abé cé", "Abë-cè", "Abé Cé"],
                                       "D": ["dé", "Dé", "dë"]})
        self.assertEqual(rslt, {'ABC': 3, 'D': 3})
        rslt = self.ac(group_by_letter_case=True)
        self.assertEqual(rslt, {'abé cé': 2, 'abë-cè': 1, 'dé': 2, 'dë': 1})
        rslt = self.ac(group_by_slugify=True)
        self.assertEqual(rslt, {'abe-ce': 3, 'de': 3})
        rslt = self.ac(group_by_slugify=True,
                       group_together={"ABCD": ["abe-ce", "de"]})
        self.assertEqual(rslt, {'ABCD': 6})
        rslt = self.ac(
            group_by_letter_case=True,
            group_together={"ABCD": ["Abë-cè", "Abé Cé", "Dé", "dë"]}
        )
        self.assertEqual(rslt, {'ABCD': 6})

    def test_answers_cardinality_filtered(self):
        """ We can filter answer with a csv string. """
        rslt = self.ac(filter=["abé cé", "Abë-cè"], group_by_slugify=True)
        self.assertEqual(rslt, {'de': 3})
        rslt = self.ac(filter=["abe-ce"], group_by_slugify=True)
        self.assertEqual(rslt, {'de': 3})
        rslt = self.ac(
            group_together={"ABC": ["abe-ce"], }, filter=["ABC"],
            group_by_slugify=True
        )
        self.assertEqual(rslt, {'de': 3})
        rslt = self.ac(filter=["abé cé", "Abë-cè"], group_by_letter_case=True)
        self.assertEqual(rslt, {'dé': 2, 'dë': 1})
        rslt = self.ac(filter=["abé cé", "Abë-cè"])
        self.assertEqual(rslt, {'Abé Cé': 1, 'dé': 1, 'dë': 1, 'Dé': 1, })

    def test_sorted_answers_cardinality(self):
        """ We can sort answer with the sort_answer parameter. """
        alphanumeric = [('abé cé', 2), ('abë-cè', 1), ('dé', 2), ('dë', 1)]
        cardinal = [('abé cé', 2), ('dé', 2), ('abë-cè', 1), ('dë', 1)]
        user_defined = {"dé": 1, 'abë-cè': 2, 'dë': 3, 'abé cé': 4, }
        specific = [('dé', 2), ('abë-cè', 1), ('dë', 1), ('abé cé', 2), ]
        self.assertEqual(self.sac(group_by_letter_case=True), alphanumeric)
        rslt = self.sac(group_by_letter_case=True, sort_answer="alphanumeric")
        self.assertEqual(rslt, alphanumeric)
        rslt = self.sac(group_by_letter_case=True, sort_answer="cardinal")
        self.assertEqual(rslt, cardinal)
        rslt = self.sac(group_by_letter_case=True, sort_answer=user_defined)
        self.assertEqual(rslt, specific)
