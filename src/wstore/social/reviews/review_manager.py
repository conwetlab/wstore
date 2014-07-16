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

import os
from datetime import datetime

from django.core.exceptions import PermissionDenied
from django.conf import settings

from wstore.models import Offering, Context
from wstore.social.reviews.models import Review, Response
from wstore.search.search_engine import SearchEngine


class ReviewManager():

    def _validate_content(self, review_data):
        """
        Validate review JSON data
        """
        exception = None

        # Check review data type
        if not isinstance(review_data, dict):
            exception = TypeError('Invalid review data')

        # Check review data contents
        if not exception and (not 'title' in review_data or not 'comment' in review_data or not 'rating' in review_data):
            exception = ValueError('Missing required field')

        if not exception and (not isinstance(review_data['title'], str) and not isinstance(review_data['title'], unicode)):
            exception = TypeError('Invalid title format')

        if not exception and (not isinstance(review_data['comment'], str) and not isinstance(review_data['comment'], unicode)):
            exception = TypeError('Invalid comment format')

        if not exception and len(review_data['title']) > 60:
            exception = ValueError('The title cannot contain more than 60 characters')

        if not exception and len(review_data['comment']) > 200:
            exception = ValueError('The comment cannot contain more than 200 characters')

        if not exception and not isinstance(review_data['rating'], int):
            exception = TypeError('Invalid rating format')

        if not exception and not (review_data['rating'] > 0 and review_data['rating'] < 6):
            exception = ValueError('Rating must be an integer between 0 and 5')

        return exception

    def _update_top_rated(self):
        """
        Updates top rated list to new rating
        """
        # Check the top rated structure
        context = Context.objects.all()[0]

        context.top_rated = [off.pk for off in Offering.objects.filter(state="published").order_by('-rating')[:8]]
        context.save()

    def _get_and_validate_review(self, user, review_id, owner=False):
        """
        Returns and validates review object
        """
        # Check review id type
        if not isinstance(review_id, str) and not isinstance(review_id, unicode):
            raise TypeError('The review id must be an string')

        # Get review model
        try:
            rev = Review.objects.get(pk=review_id)
        except:
            raise ValueError('Invalid review id')

        if not owner:
            # Check if the user can update the review
            if not user == rev.user or not user.userprofile.current_organization == rev.organization:
                raise PermissionDenied('The user cannot update the current review')
        else:
            #Check if the user is the owner of the reviewed offering
            if not (user.userprofile.current_organization == rev.offering.owner_organization) or \
            not user.pk in user.userprofile.current_organization.managers:
                raise PermissionDenied('The user cannot respond the current review')

        return rev

    def create_review(self, user, offering, review):
        """
        Creates a new review for a given offering
        """
        # Check if the user can review the offering.
        if (user.userprofile.is_user_org() and offering.pk in user.userprofile.rated_offerings)\
        or (not user.userprofile.is_user_org() and user.userprofile.current_organization.has_rated_offering(user, offering)):
            raise PermissionDenied('The user cannot review this offering')

        # Validate review data
        validation = self._validate_content(review)
        if validation:
            raise validation

        # Create the review
        rev = Review.objects.create(
            user=user,
            organization=user.userprofile.current_organization,
            offering=offering,
            timestamp=datetime.now(),
            title=review['title'],
            comment=review['comment'],
            rating=review['rating']
        )

        offering.comments.insert(0, rev.pk)

        # Calculate new offering rate
        old_rate = offering.rating

        if old_rate == 0:
            offering.rating = review['rating']
        else:
            offering.rating = ((old_rate * (len(offering.comments) - 1)) + review['rating']) / len(offering.comments)

        offering.save()

        # Update offering indexes
        index_path = os.path.join(settings.BASEDIR, 'wstore')
        index_path = os.path.join(index_path, 'search')
        index_path = os.path.join(index_path, 'indexes')

        se = SearchEngine(index_path)
        se.update_index(offering)

        # Save the offering as rated
        if user.userprofile.is_user_org():
            user.userprofile.rated_offerings.append(offering.pk)
            user.userprofile.save()
        else:
            user.userprofile.current_organization.rated_offerings.append({
                'user': user.pk,
                'offering': offering.pk
            })
            user.userprofile.current_organization.save()

        # Update top rated list
        self._update_top_rated()

    def get_reviews(self, offering, start=None, limit=None):
        """
        Gets reviews of a given offering
        """
        # Check parameters
        if (start and limit):
            try:
                start = int(start)
                limit = int(limit)
            except:
                raise TypeError('Invalid pagination params')

            if not start > 0:
                raise ValueError('Start parameter should be higher than 0')

            if not limit > 0:
                raise ValueError('Limit parameter should be higher than 0')

            # Get Review objects
            reviews = Review.objects.filter(offering=offering).order_by('-timestamp')[start - 1:(start + limit) - 1]
        else:
            reviews = Review.objects.filter(offering=offering).order_by('-timestamp')

        # Create JSON structure
        result = []
        for review in reviews:
            review_data = {
                'id': review.pk,
                'user': review.user.username,
                'organization': review.organization.name,
                'timestamp': unicode(review.timestamp),
                'title': review.title,
                'comment': review.comment,
                'rating': review.rating,
            }
            if review.response:
                review_data['response'] = {
                    'user': review.response.user.username,
                    'organization': review.response.organization.name,
                    'timestamp': unicode(review.response.timestamp),
                    'title': review.response.title,
                    'response': review.response.response,
                }
            result.append(review_data)

        return result

    def update_review(self, user, review, review_data):
        """
        Updates a given review
        """

        # Check data
        validation = self._validate_content(review_data)
        if validation:
            raise validation

        rev = self._get_and_validate_review(user, review)

        # Calculate new rating
        rate = ((rev.offering.rating * len(rev.offering.comments)) - rev.rating + review_data['rating']) / len(rev.offering.comments)

        # update review
        rev.title = review_data['title']
        rev.comment = review_data['comment']
        rev.rating = review_data['rating']
        rev.timestamp = datetime.now()

        rev.save()

        # Update offering rating
        rev.offering.rating = rate
        rev.offering.save()

        # Update offering indexes
        index_path = os.path.join(settings.BASEDIR, 'wstore')
        index_path = os.path.join(index_path, 'search')
        index_path = os.path.join(index_path, 'indexes')

        se = SearchEngine(index_path)
        se.update_index(rev.offering)

        # Update top rated offerings
        self._update_top_rated()

    def remove_review(self, user, review):
        """
        Removes a given review
        """

        rev = self._get_and_validate_review(user, review)

        # Remove review from offering
        rev.offering.comments.remove(review)

        # Update offering rating
        rev.offering.rating = ((rev.offering.rating * (len(rev.offering.comments) + 1)) - rev.rating) / len(rev.offering.comments)
        rev.offering.save()

        # Update offering indexes
        index_path = os.path.join(settings.BASEDIR, 'wstore')
        index_path = os.path.join(index_path, 'search')
        index_path = os.path.join(index_path, 'indexes')

        se = SearchEngine(index_path)
        se.update_index(rev.offering)

        # Update top rated offerings
        self._update_top_rated()

        rev.delete()

    def _validate_response(self, response):

        exception = None
        # Validate response type
        if not isinstance(response, dict):
            exception = TypeError('Invalid response type')

        # Validate response contents
        if not exception and (not 'title' in response or not 'response' in response):
            exception = ValueError('Missing a required field in response')

        # Validate contents type
        if not exception and (not isinstance(response['title'], str) and not isinstance(response['title'], unicode)):
            exception = TypeError('Invalid title format')

        if not exception and (not isinstance(response['response'], str) and not isinstance(response['response'], unicode)):
            exception = TypeError('Invalid response text format')

        # Validate contents length
        if not exception and len(response['title']) > 60:
            exception = ValueError('Response title cannot contain more than 60 characters')

        if not exception and len(response['response']) > 200:
            exception = ValueError('Response text cannot contain more than 200 characters')

        return exception

    def create_response(self, user, review, response):
        """
        Creates a response in a given review
        """

        # Validate response fields
        validation = self._validate_response(response)
        if validation:
            raise validation

        rev = self._get_and_validate_review(user, review, owner=True)

        # Create the response
        rev.response = Response(
            user=user,
            organization=user.userprofile.current_organization,
            timestamp=datetime.now(),
            title=response['title'],
            response=response['response']
        )
        rev.save()

    def remove_response(self, user, review):
        """
        Removes a response from a given review
        """

        rev = self._get_and_validate_review(user, review, owner=True)
        rev.response.delete()
