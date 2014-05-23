# -*- coding: utf-8 -*-

# Copyright (c) 2013 CoNWeT Lab., Universidad Politécnica de Madrid

# This file is part of WStore.

# WStore is free software: you can redistribute it and/or modify
# it under the terms of the European Union Public Licence (EUPL)
# as published by the European Commission, either version 1.1
# of the License, or (at your option) any later version.

# WStore is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# European Union Public Licence for more details.

# You should have received a copy of the European Union Public Licence
# along with WStore.
# If not, see <https://joinup.ec.europa.eu/software/page/eupl/licence-eupl>.

from __future__ import unicode_literals

from datetime import datetime

from mock import MagicMock
from nose_parameterized import parameterized

from django.test import TestCase
from django.core.exceptions import PermissionDenied

from wstore.social.reviews import review_manager


##########################################################################
############################## Test data #################################
##########################################################################

EXAMPLE_REVIEW = {
    'title': 'An example review',
    'comment': 'This is an example review for testing',
    'rating': 3
}

REVIEW_INVALID_RATING = {
    'title': 'An example review',
    'comment': 'This is an example review for testing',
    'rating': -1
}

REVIEW_TITLE_INV_TYPE = {
    'title': 3,
    'comment': 'This is an example review for testing',
    'rating': 3
}

REVIEW_COMMENT_INV_TYPE = {
    'title': 'An example review',
    'comment': 1,
    'rating': 4
}

REVIEW_RATING_INV_TYPE = {
    'title': 'An example review',
    'comment': 'This is an example review for testing',
    'rating': '4'
}

REVIEW_MISSING_TITLE = {
    'comment': 'This is an example review for testing',
    'rating': 3
}

REVIEW_MISSING_COMMENT = {
    'title': 'An example review',
    'rating': 3
}

REVIEW_MISSING_RATING = {
    'title': 'An example review',
    'comment': 'This is an example review for testing',
}

REVIEW_TITLE_INV_LENGHT = {
    'title': 'An example review title with more than 60 characters used for testing',
    'comment': 'This is an example review for testing',
    'rating': 3
}

REVIEW_COMMENT_INV_LENGHT = {
    'title': 'An example review',
    'comment': 'This is an example review comment for testing with more than 200 characters used for testing invalid length errors. This is an example review comment for testing with more than 200 characters used for testing invalid length errors. ',
    'rating': 3
}

REVIEW1 = {
    'id': '777777',
    'user': 'test_user',
    'organization': 'test_user',
    'timestamp': '2014-04-01 18:01:00.100000',
    'title': 'An example review',
    'comment': 'This is an example review',
    'rating': 3
}

REVIEW2 = {
    'id': '888888',
    'user': 'test_user1',
    'organization': 'test_org1',
    'timestamp': '2014-04-01 18:02:00.100000',
    'title': 'a review with response',
    'comment': 'a comment',
    'rating': 4,
    'response': {
        'user': 'test_user2',
        'organization': 'test_user2',
        'timestamp': '2014-04-01 18:03:00.100000',
        'title': 'response',
        'response': 'response text'
    }
}

REVIEW3 = {
    'id': '999999',
    'user': 'test_user3',
    'organization': 'test_user3',
    'timestamp': '2014-04-01 18:00:00.100000',
    'title': 'An example review',
    'comment': 'This is an example review',
    'rating': 3
}

RESULT_REVIEWS = [REVIEW1, REVIEW2 , REVIEW3]


##########################################################################
############################## Test case #################################
##########################################################################


class ReviewTestCase(TestCase):

    tags = ('reviews',)

    @classmethod
    def setUpClass(cls):
        super(ReviewTestCase, cls).setUpClass()

    def setUp(self):
        # Mock context
        context_object = MagicMock()
        cont = MagicMock()
        context_object.objects.all.return_value = [cont]
        review_manager.Context = context_object

        # Mock datetime
        self.datetime = datetime.now()
        review_manager.datetime = MagicMock()
        review_manager.datetime.now.return_value = self.datetime

        # Create test offering mock
        self.offering = MagicMock()
        self.offering.pk = '222222'
        self.offering.comments = ['333333', '444444', '555555']
        self.offering.rating = 5.0

        # Create user objects mock
        self.org = MagicMock()
        self.org.name = 'test_user'
        self.org.rated_offerings = []
        self.user = MagicMock()
        self.user.username = 'test_user'
        self.user.pk = '666666'
        self.user.userprofile.current_organization = self.org
        self.user.userprofile.rated_offerings = []

    def _no_rated(self):
        self.offering.rating = 0.0
        self.offering.comments = []

    def _org_rated(self):
        self.org.name = 'test_org'
        self.user.userprofile.is_user_org.return_value = False
        self.org.has_rated_offering.return_value = False

    def _usr_not_allowed(self):
        self.user.userprofile.rated_offerings.append(self.offering.pk)

    def _usr_not_allowed_org(self):
        self._org_rated()
        self.org.rated_offerings.append({
            'user': self.user.pk,
            'offering': self.offering.pk
        })
        self.org.has_rated_offering.return_value = True

    @parameterized.expand([
        (EXAMPLE_REVIEW, 4.5),
        (EXAMPLE_REVIEW, 3, _no_rated),
        (EXAMPLE_REVIEW, 4.5, _org_rated, True),
        (EXAMPLE_REVIEW, None, _usr_not_allowed, False, PermissionDenied, 'The user cannot review this offering'),
        (EXAMPLE_REVIEW, None, _usr_not_allowed_org, False, PermissionDenied, 'The user cannot review this offering'),
        (('user',), None, None, False, TypeError, 'Invalid review data'),
        (REVIEW_MISSING_TITLE, None, None, False, ValueError, 'Missing required field'),
        (REVIEW_MISSING_COMMENT, None, None, False, ValueError, 'Missing required field'),
        (REVIEW_MISSING_RATING, None, None, False, ValueError, 'Missing required field'),
        (REVIEW_TITLE_INV_TYPE, None, None, False, TypeError, 'Invalid title format'),
        (REVIEW_COMMENT_INV_TYPE, None, None, False, TypeError, 'Invalid comment format'),
        (REVIEW_RATING_INV_TYPE, None, None, False, TypeError, 'Invalid rating format'),
        (REVIEW_TITLE_INV_LENGHT, None, None, False, ValueError, 'The title cannot contain more than 60 characters'),
        (REVIEW_COMMENT_INV_LENGHT, None, None, False, ValueError, 'The comment cannot contain more than 200 characters'),
        (REVIEW_INVALID_RATING, None, None, False, ValueError, 'Rating must be an integer between 0 and 5'),
    ])
    def test_create_review(self, review, exp_rating, side_effect=None, org_comment=False, err_type=None, err_msg=None):

        # Create review mock
        review_object = MagicMock()
        rev = MagicMock()
        rev.pk = '111111'
        review_object.objects.create.return_value = rev
        review_manager.Review = review_object

        # Create review manager
        rm = review_manager.ReviewManager()

        if side_effect:
            side_effect(self)

        exception = None
        try:
            rm.create_review(self.user, self.offering, review)
        except Exception as e:
            exception = e

        # Check calls and objects
        if not err_type:
            self.assertEquals(exception, None)

            review_object.objects.create.assert_called_once_with(
                user=self.user,
                organization=self.org,
                offering=self.offering,
                timestamp=self.datetime,
                title=review['title'],
                comment=review['comment'],
                rating=review['rating']
            )
            self.assertEquals(self.offering.rating, exp_rating)
            self.assertEquals(self.offering.comments[0], rev.pk)

            if not org_comment:
                self.assertTrue(self.offering.pk in self.user.userprofile.rated_offerings)
                self.user.userprofile.save.assert_called_once_with()
            else:
                self.assertTrue({'user': self.user.pk, 'offering': self.offering.pk} in self.org.rated_offerings)
                self.org.save.assert_called_once_with()
        else:
            self.assertTrue(isinstance(exception, err_type))
            self.assertEquals(unicode(e), err_msg)

    def _create_review_mock(self, rev_data):
        review = MagicMock()
        review.pk = rev_data['id']

        usr = MagicMock()
        usr.username = rev_data['user']

        org = MagicMock()
        org.name = rev_data['organization']
        if usr.name == rev_data['organization']:
            usr.userprofile.current_organization = org

        review.user = usr
        review.organization = org
        review.title = rev_data['title']
        review.comment = rev_data['comment']
        review.rating = rev_data['rating']
        review.offering = self.offering
        review.timestamp = datetime.strptime(rev_data['timestamp'], '%Y-%m-%d %H:%M:%S.%f')

        if 'response' in rev_data:
            response = MagicMock()
            resp_user = MagicMock()
            resp_user.username = rev_data['response']['user']
            resp_org = MagicMock()
            resp_org.name = rev_data['response']['organization']
            if resp_user.name == rev_data['response']['organization']:
                resp_user.userprofile.current_organization = resp_org

            response.user = resp_user
            response.organization = resp_org
            response.title = rev_data['response']['title']
            response.response = rev_data['response']['response']
            response.timestamp = datetime.strptime(rev_data['response']['timestamp'], '%Y-%m-%d %H:%M:%S.%f')

            review.response = response
        else:
            review.response = None

        return review

    @parameterized.expand([
        (RESULT_REVIEWS,),
        (RESULT_REVIEWS[:2], '1', '2'),
        (None, '1a', '2', TypeError, 'Invalid pagination params'),
        (None, '1', '2b', TypeError, 'Invalid pagination params'),
        (None, '-1', '2', ValueError, 'Start parameter should be higher than 0'),
        (None, '1', '-2', ValueError, 'Limit parameter should be higher than 0'),
    ])
    def test_get_reviews(self, expected_result, start=None, limit=None, err_type=None, err_msg=None):

        # Create review mock
        rev = MagicMock()

        #import ipdb; ipdb.set_trace()
        # Create review mock objects
        review1 = self._create_review_mock(REVIEW1)
        review2 = self._create_review_mock(REVIEW2)
        review3 = self._create_review_mock(REVIEW3)

        rev.objects.filter = MagicMock()
        filter_obj = MagicMock()
        filter_obj.order_by.return_value = [review1, review2, review3]

        rev.objects.filter.return_value = filter_obj
        review_manager.Review = rev

        # Call get reviews method
        excp = None
        rm = review_manager.ReviewManager()
        try:
            response = rm.get_reviews(self.offering, start, limit)
        except Exception as e:
            excp = e

        if not err_type:
            self.assertEquals(excp, None)
            # Check calls and returned data
            rev.objects.filter.assert_called_once_with(offering=self.offering)
            filter_obj.order_by.assert_called_once_with('-timestamp')

            self.assertEquals(response, expected_result)
        else:
            # Check raised exception
            self.assertTrue(isinstance(excp, err_type))
            self.assertEquals(unicode(excp), err_msg)

    def test_update_reviews(self):
        pass

    def test_remove_review(self):
        pass

    def test_create_response(self):
        pass

    def test_remove_response(self):
        pass


