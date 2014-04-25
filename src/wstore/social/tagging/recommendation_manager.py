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


import json
import decimal
from threading import Thread
from stemming.porter2 import stem
from whoosh.analysis import StemmingAnalyzer

from wstore.social.tagging.tag_manager import TagManager
from wstore.search.search_engine import SearchEngine


class RecommendationManager():
    """
      This class is used for generating recommendations for tagging
    """

    _coocurrence_tags = []
    _usdl_coocurrence_tags = []
    _offering = None
    _user_tags = None

    def __init__(self, offering, user_tags):
        self._offering = offering
        self._user_tags = user_tags

    def get_recommended_tags(self):

        # Create usdl tags thread
        usdl_ent = USDLEntitiesRetrieving(self._offering)
        entities = usdl_ent.get_named_entities()

        # Create co-occurrence thread
        co_thd = CooccurrenceThead(self._coocurrence_tags, self._user_tags)
        # Get USDL co-occurrence tags
        co_u_thd = CooccurrenceThead(self._usdl_coocurrence_tags, entities, include_user_tags=True)

        # Run co-occurrence thread
        co_thd.start()
        co_u_thd.start()

        # Wait for co-occurrence thread
        co_thd.join()
        co_u_thd.join()

        # Aggregate tags
        return self._aggregate_tags()
        

    def _aggregate_tags(self):
        """
        Creates a single tag list with the higher score and
        without the user tags
       """
        result = []
        aux_map = {}
        stemmed_user_tags = [stem(tag) for tag in self._user_tags]

        tag_lists = [
            self._coocurrence_tags,
            self._usdl_coocurrence_tags
        ]
        # Map tags
        for tag_list in tag_lists:
            for tag, named_tag, rank in tag_list:
                if not tag in stemmed_user_tags:
                    if not tag in aux_map:
                        aux_map[tag] = {
                            'named_tag': named_tag,
                            'ranks': set([rank])
                        }
                    else:
                        aux_map[tag]['ranks'].add(rank)

        # Reduce tags
        for tag in aux_map:
            rank = 0
            for r in aux_map[tag]['ranks']:
                if r > rank:
                    rank = r
            result.append((aux_map[tag]['named_tag'], rank))

        # Sort by rank
        result = sorted(result, key=lambda tag: tag[1], reverse=True)

        # Only 50 recommendations are shown
        if len(result) > 50:
            result = result[:50]

        return result


class CooccurrenceThead(Thread):
    """
      Creates a thread that generates and rank co-occurrence tags
    """

    _tag_container = None
    _user_tags = None
    _include_user_tags = None

    def __init__(self, tag_container, user_tags, include_user_tags=False):
        self._tag_container = tag_container
        self._user_tags = user_tags
        self._include_user_tags = include_user_tags
        Thread.__init__(self)

    def _rank_tags(self, frequency_map):
        """
        Rank tags based on co-occurrence frequency
        pi = sum(|ti intersection tj| / |tj|) / n
       """
        decimal.getcontext().prec = 2
        # Calculate tag rank
        for co_tag in frequency_map['co-tags']:
            co_tag_prob = frequency_map['co-tags'][co_tag]

            rank = decimal.Decimal(0)
            # Calculate and sum partial probabilities
            for user_tag in frequency_map['user_tags_freq']:
                if user_tag in co_tag_prob['user_tags']:
                    rank += decimal.Decimal(co_tag_prob['user_tags'][user_tag]) / decimal.Decimal(frequency_map['user_tags_freq'][user_tag])

            # Divide by the number of user tags
            rank = rank / decimal.Decimal(len(frequency_map['user_tags_freq']))
            self._tag_container.append((co_tag, co_tag_prob['named_tag'], rank))

    def run(self):
        tag_manager = TagManager()
        frequency_map = {
            'user_tags_freq': {},  # Absolute frequencies of user tags
            'co-tags':{}  # tags and user tags intersection frequency
        }

        # Iterate over user tags
        for tag in self._user_tags:
            # Stem the tag
            st_tag = stem(tag)

            # Get indexed documents where the tag is included
            docs = tag_manager.get_index_doc_by_tag(st_tag)

            # Include user tags frequency
            if len(docs) > 0:
                frequency_map['user_tags_freq'][st_tag] = len(docs)

            for doc in docs:
                # Get tags
                tags = doc['named_tags'].split(' ')

                # Populate the frequencies map: for user tags it contains the absolute
                # frequency of the tag, for co-occurrence tags it contains the frequency
                # of the intersection with the corresponding user tag

                for not_stem_tag in tags:
                    t = stem(not_stem_tag)
                    if t and (self._include_user_tags or (not self._include_user_tags and t != st_tag)):
                        if not t in frequency_map['co-tags']:
                            frequency_map['co-tags'][t] = {
                                'named_tag': not_stem_tag,
                                'user_tags': {
                                    st_tag: 1
                                }
                            }
                        else:
                            if st_tag in frequency_map['co-tags'][t]['user_tags']:
                                frequency_map['co-tags'][t]['user_tags'][st_tag] += 1
                            else:
                                frequency_map['co-tags'][t]['user_tags'][st_tag] = 1

        # Calculate tag rank and populate tag container
        self._rank_tags(frequency_map)
                


class USDLEntitiesRetrieving(Thread):
    """
      Creates a thread that generates and rank tags from USDL documents
    """
    _offering = None

    def __init__(self, offering):
        self._offering = offering
        Thread.__init__(self)
       
    def get_named_entities(self):
        # Get USDL text aggregator
        se = SearchEngine('')

        # Get usdl text
        text = se._aggregate_text(self._offering)

        # Get stemmed tokens
        analyzer = StemmingAnalyzer()
        named_entities = set([token.text for token in analyzer(unicode(text))])
        return named_entities
