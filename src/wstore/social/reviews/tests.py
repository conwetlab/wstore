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
    'comment': 'This is an example review comment for testing with more than 1000 characters used for testing invalid length errors. This is an example review comment for testing with more than 200 characters used for testing invalid length errors. This is an example review comment for testing with more than 1000 characters used for testing invalid length errors. This is an example review comment for testing with more than 200 characters used for testing invalid length errors. This is an example review comment for testing with more than 1000 characters used for testing invalid length errors. This is an example review comment for testing with more than 200 characters used for testing invalid length errors. This is an example review comment for testing with more than 1000 characters used for testing invalid length errors. This is an example review comment for testing with more than 200 characters used for testing invalid length errors. This is an example review comment for testing with more than 1000 characters used for testing invalid length errors. This is an example review comment for testing with more than 200 characters used for testing invalid length errors. ',
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

RESULT_REVIEWS = [REVIEW1, REVIEW2, REVIEW3]

RESPONSE = {
    'title': 'a valid response',
    'response': 'text of a valid response'
}

RESPONSE_MISSING_TITLE = {
    'response': 'a missing title response'
}

RESPONSE_MISSING_RESPONSE = {
    'title': 'missing response text'
}

RESPONSE_INV_TITLE = {
    'title': 3,
    'response': 'invalid title type response'
}

RESPONSE_INV_RESP = {
    'title': 'a valid title',
    'response': 12
}

RESPONSE_INV_LEN_TITLE = {
    'title': 'An example response title with more than 60 characters used for testing',
    'response': 'a valid response'
}

RESPONSE_INV_LEN_RESP = {
    'title': 'a valid title',
    'response': 'This is an example response comment for testing with more than 1000 characters used for testing invalid length errors. This is an example response comment for testing with more than 200 characters used for testing invalid length errors. This is an example response comment for testing with more than 1000 characters used for testing invalid length errors. This is an example response comment for testing with more than 200 characters used for testing invalid length errors. This is an example response comment for testing with more than 1000 characters used for testing invalid length errors. This is an example response comment for testing with more than 200 characters used for testing invalid length errors. This is an example response comment for testing with more than 1000 characters used for testing invalid length errors. This is an example response comment for testing with more than 200 characters used for testing invalid length errors. This is an example response comment for testing with more than 1000 characters used for testing invalid length errors. This is an example response comment for testing with more than 200 characters used for testing invalid length errors. This is an example response comment for testing with more than 1000 characters used for testing invalid length errors. This is an example response comment for testing with more than 200 characters used for testing invalid length errors. This is an example response comment for testing with more than 1000 characters used for testing invalid length errors. This is an example response comment for testing with more than 200 characters used for testing invalid length errors. This is an example response comment for testing with more than 1000 characters used for testing invalid length errors. This is an example response comment for testing with more than 200 characters used for testing invalid length errors. '
}

##########################################################################
############################## Test case #################################
##########################################################################


class ReviewTestCase(TestCase):

    tags = ('reviews',)

    @classmethod
    def setUpClass(cls):
        cls._old_context = review_manager.Context
        se_obj = MagicMock()
        review_manager.SearchEngine = MagicMock();
        review_manager.SearchEngine.return_value = se_obj

        super(ReviewTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        review_manager.Context = cls._old_context
        reload(review_manager)
        super(ReviewTestCase, cls).tearDownClass()

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

        # Mock Purchase object
        review_manager.Purchase = MagicMock()

        # Create test offering mock
        self.offering = MagicMock()
        self.offering.pk = '222222'
        self.offering.comments = ['333333', '444444', '555555']
        self.offering.rating = 5.0
        self.offering.open = False
        self.offering.is_owner.return_value = False

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

    def _invalid_rev(self):
        review_manager.Review = MagicMock()
        review_manager.Review.objects.get.side_effect = Exception('Invalid review')

    def _invalid_usr_resp(self):
        self.user.userprofile.current_organization = MagicMock()

    def _not_manager(self):
        self.user.pk = '909090'

    def _update_not_allowed(self, rev):
        rev.user = MagicMock()

    def _not_purchased(self):
        review_manager.Purchase.objects.get.side_effect = Exception('Not purchased')

    def _open_offering(self):
        self._not_purchased()
        self.offering.open = True

    def _owner_review(self):
        self._open_offering()
        self.offering.is_owner.return_value = True

    @parameterized.expand([
        (EXAMPLE_REVIEW, 4.5),
        (EXAMPLE_REVIEW, 4.5, _open_offering),
        (EXAMPLE_REVIEW, 3, _no_rated),
        (EXAMPLE_REVIEW, 4.5, _org_rated, True),
        (EXAMPLE_REVIEW, None, _owner_review, False, PermissionDenied, 'You cannot review your own offering'),
        (EXAMPLE_REVIEW, None, _usr_not_allowed, False, PermissionDenied, 'You cannot review this offering again. Please update your review to provide new comments'),
        (EXAMPLE_REVIEW, None, _not_purchased, False, PermissionDenied, 'You cannot review this offering since you has not acquire it'),
        (EXAMPLE_REVIEW, None, _usr_not_allowed_org, False, PermissionDenied, 'You cannot review this offering again. Please update your review to provide new comments'),
        (('user',), None, None, False, TypeError, 'Invalid review data'),
        (REVIEW_MISSING_TITLE, None, None, False, ValueError, 'Missing required field'),
        (REVIEW_MISSING_COMMENT, None, None, False, ValueError, 'Missing required field'),
        (REVIEW_MISSING_RATING, None, None, False, ValueError, 'Missing required field'),
        (REVIEW_TITLE_INV_TYPE, None, None, False, TypeError, 'Invalid title format'),
        (REVIEW_COMMENT_INV_TYPE, None, None, False, TypeError, 'Invalid comment format'),
        (REVIEW_RATING_INV_TYPE, None, None, False, TypeError, 'Invalid rating format'),
        (REVIEW_TITLE_INV_LENGHT, None, None, False, ValueError, 'The title cannot contain more than 60 characters'),
        (REVIEW_COMMENT_INV_LENGHT, None, None, False, ValueError, 'The comment cannot contain more than 1000 characters'),
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

            if not self.offering.open:
                review_manager.Purchase.objects.get.assert_called_once_with(
                    owner_organization=self.org,
                    offering=self.offering
                )

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

    @parameterized.expand([
        (EXAMPLE_REVIEW, '999999', 3.5),
        (EXAMPLE_REVIEW, 999999, 0, None, TypeError, 'The review id must be an string'),
        (EXAMPLE_REVIEW, '999999', 0, _update_not_allowed, PermissionDenied, 'The user cannot update the current review'),
        (REVIEW_MISSING_TITLE, '999999', 0, None, ValueError, 'Missing required field')
    ])
    def test_update_reviews(self, review_data, review_id, exp_rate, side_effect=None, err_type=None, err_msg=None):

        #import ipdb; ipdb.set_trace()
        # Create mocks
        rev_object = MagicMock()
        rev_object.user = self.user
        rev_object.organization = self.org
        self.offering.rating = 3.75
        self.offering.comments = ['333333', '444444', '555555', '666666']
        rev_object.offering = self.offering
        rev_object.rating = 4
        review_manager.Review = MagicMock()
        review_manager.Review.objects.get.return_value = rev_object

        if side_effect:
            side_effect(self, rev_object)

        # Call the method
        error = None
        try:
            rm = review_manager.ReviewManager()
            rm.update_review(self.user, review_id, review_data)
        except Exception as e:
            error = e

        if not error:
            self.assertEquals(error, None)
            # Check new review info
            self.assertEquals(rev_object.title, review_data['title'])
            self.assertEquals(rev_object.comment, review_data['comment'])
            self.assertEquals(rev_object.rating, review_data['rating'])
            self.assertEquals(rev_object.timestamp, self.datetime)

            # Check info saved
            rev_object.save.assert_called_once_with()

            # Check new offering rating
            self.assertEquals(self.offering.rating, exp_rate)

            self.offering.save.assert_called_once_with()
        else:
            self.assertTrue(isinstance(error, err_type))
            self.assertEquals(unicode(error), err_msg)

    def _check_user_rev_del(self):
        self.assertEquals(self.offering.rating, 4.0)
        self.assertEquals(len(self.user.userprofile.rated_offerings), 0)
        self.user.userprofile.save.assert_called_once_with()

    def _check_user_org_rev_del(self):
        self.assertEquals(self.offering.rating, 0)
        self.assertEquals(len(self.offering.comments), 0)
        self.assertEquals(len(self.org.rated_offerings), 0)
        self.org.save.assert_called_once_with()

    def _check_user_org_manager_rev_del(self):
        self.assertEquals(self.offering.rating, 4.0)
        self.assertEquals(len(self.offering.comments), 3)
        self.assertEquals(len(self.org.rated_offerings), 0)
        self.org.save.assert_called_once_with()

    def _last_review(self, rev):
        self.offering.comments = ['333333']
        self.user.userprofile.is_user_org.return_value = False
        self.org.name = 'test_organization'
        self.org.rated_offerings = [{
            'user': self.user.pk,
            'offering': self.offering.pk
        }]

    def _manager_del(self, rev):
        rev.user = MagicMock()
        rev.user.username = 'test_user2'
        rev.user.pk = 'tu2pk'
        rev.user.userprofile.current_organization = self.org
        rev.user.userprofile.is_user_org.return_value = False
        self.org.managers = [self.user.pk]
        self.org.rated_offerings = [{
            'user': rev.user.pk,
            'offering': self.offering.pk
        }]
        self.org.name = 'test_organization'

    @parameterized.expand([
        ('usr', _check_user_rev_del),
        ('usr_org_last_rev', _check_user_org_rev_del, _last_review),
        ('manager', _check_user_org_manager_rev_del, _manager_del)
    ])
    def test_remove_review(self, name, user_check, side_effect=None):
        # Create Mocks
        #if name == 'manager':
        #    import ipdb; ipdb.set_trace()

        rev_object = MagicMock()
        rev_object.pk = '333333'
        rev_object.user = self.user
        rev_object.organization = self.org
        self.user.userprofile.rated_offerings = [self.offering.pk]
        self.offering.rating = 3.75
        self.offering.comments = ['333333', '444444', '555555', '666666']
        rev_object.offering = self.offering
        rev_object.rating = 3
        review_manager.Review = MagicMock()
        review_manager.Review.objects.get.return_value = rev_object

        if side_effect:
            side_effect(self, rev_object)

        error = False
        try:
            rm = review_manager.ReviewManager()
            rm.remove_review(self.user, '333333')
        except:
            error = True

        # Check result
        self.assertFalse(error)
        self.assertFalse('333333' in self.offering)

        self.offering.save.assert_called_once_with()
        rev_object.delete.assert_called_once_with()
        # Check user or organization models
        user_check(self)

    @parameterized.expand([
        (RESPONSE, '999999'),
        (('title',), '999999', None, TypeError, 'Invalid response type'),
        (RESPONSE_MISSING_TITLE, '999999', None, ValueError, 'Missing a required field in response'),
        (RESPONSE_MISSING_RESPONSE, '999999', None, ValueError, 'Missing a required field in response'),
        (RESPONSE_INV_TITLE, '999999', None, TypeError, 'Invalid title format'),
        (RESPONSE_INV_RESP, '999999', None, TypeError, 'Invalid response text format'),
        (RESPONSE_INV_LEN_TITLE, '999999', None, ValueError, 'Response title cannot contain more than 60 characters'),
        (RESPONSE_INV_LEN_RESP, '999999', None, ValueError, 'Response text cannot contain more than 200 characters'),
        (RESPONSE, 100, None, TypeError, 'The review id must be an string'),
        (RESPONSE, '111111', _invalid_rev, ValueError, 'Invalid review id'),
        (RESPONSE, '111111', _invalid_usr_resp, PermissionDenied, 'The user cannot respond the current review'),
        (RESPONSE, '111111', _not_manager, PermissionDenied, 'The user cannot respond the current review')
    ])
    def test_create_response(self, response, review_id, side_effect=None, err_type=None, err_msg=None):

        # Create offering and user mocks
        review_manager.Review = MagicMock()
        rev_object = MagicMock()
        self.offering.owner_organization = self.org
        self.org.managers = [self.user.pk]
        rev_object.offering = self.offering
        review_manager.Review.objects.get.return_value = rev_object

        resp_object = MagicMock()
        review_manager.Response = MagicMock()
        review_manager.Response.return_value = resp_object

        # Create review mock
        if side_effect:
            side_effect(self)

        # Call the method
        error = None
        try:
            rm = review_manager.ReviewManager()
            rm.create_response(self.user, review_id, response)
        except Exception as e:
            error = e

        if not err_type:
            self.assertEquals(error, None)
            # Check calls
            self.assertEquals(rev_object.response, resp_object)

            rev_object.save.assert_called_once_with()
            review_manager.Response.assert_called_once_with(
                user=self.user,
                organization=self.org,
                timestamp=self.datetime,
                title=response['title'],
                response=response['response']
            )
        else:
            self.assertTrue(isinstance(error, err_type))
            self.assertEquals(unicode(e), err_msg)

    @parameterized.expand([
        ({}, '999999', ),
        ({}, 9999999, None, TypeError, 'The review id must be an string'),
        ({}, '999999', _invalid_usr_resp, PermissionDenied, 'The user cannot respond the current review'),
        ({}, '999999', _not_manager, PermissionDenied, 'The user cannot respond the current review')
    ])
    def test_remove_response(self, c, review_id, side_effect=None, err_type=None, err_msg=None):
        # Create mocks
        review_manager.Review = MagicMock()
        rev_object = MagicMock()
        self.offering.owner_organization = self.org
        self.org.managers = [self.user.pk]
        rev_object.offering = self.offering
        review_manager.Review.objects.get.return_value = rev_object

        # Call the side effect if needed
        if side_effect:
            side_effect(self)

        error = None
        try:
            rm = review_manager.ReviewManager()
            rm.remove_response(self.user, review_id)
        except Exception as e:
            error = e

        if not err_type:
            self.assertEquals(error, None)
            # Check calls
            rev_object.response.delete.assert_called_with()
        else:
            self.assertTrue(isinstance(error, err_type))
            self.assertEquals(unicode(error), err_msg)
