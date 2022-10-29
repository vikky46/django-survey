import logging

from django.urls.base import reverse

from survey.tests import BaseTest

LOGGER = logging.getLogger(__name__)


class TestSurveyCategory(BaseTest):
    def test_category_description_none_not_shown(self):
        """
        Checks that blank category description is not shown (no 'None').
        """
        response = self.client.get(reverse("survey-detail", args=(13,)))
        self.assertNotContains(response, "None")
