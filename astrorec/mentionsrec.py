#!/usr/bin/env python
# encoding: utf-8
"""


2014-12-10 - Created by Jonathan Sick
"""

import numpy as np

from starlit.bib.adsdb import ADSBibDB


class MentionsRecs(object):
    """Citation recommendations based on mention frequency analysis."""
    def __init__(self, ads_cache):
        super(MentionsRecs, self).__init__()
        self._adsdb = ADSBibDB(cache=ads_cache)
        # List of B-level publications
        self._primary_pubs = []
        self._primary_bibcodes = []
        self._primary_mention_counts = []

    def add_primary_ref(self, pub, n_mentions):
        self._primary_pubs.append(pub)
        self._primary_bibcodes.append(pub.bibcode)
        self._primary_mention_counts.append(n_mentions)

    def analyze_secondary(self):
        """Build a secondary set of references to recommend from."""
        # First build the unique set of secondary-level publications.
        # that are not in the B-level (directly cited)
        secondary_bibcodes = []
        for primary_pub in self._primary_pubs:
            try:
                secondary_bibcodes += primary_pub.reference_bibcodes
            except:
                continue
        secondary_bibcodes = list(set(secondary_bibcodes)
                                  - set(self._primary_bibcodes))
        # FIXME hack
        # if "2005ApJ...631..820W" in secondary_bibcodes:
        #     secondary_bibcodes.remove("2005ApJ...631..820W")

        print "Scoring {0:d} publications".format(len(secondary_bibcodes))

        self._secondary_pubs = []
        primary_mentions = np.array(self._primary_mention_counts)
        for bibcode in secondary_bibcodes:
            spub = SecondaryPub(bibcode, self._adsdb, self._primary_bibcodes,
                                primary_mentions)
            self._secondary_pubs.append(spub)

        self._secondary_scores = []
        for spub in self._secondary_pubs:
            self._secondary_scores.append(spub.score)

        # TODO way to return top *n* publications
        print(zip(self._secondary_bibcodes, self._secondary_scores))


class SecondaryPub(object):
    """A publication at the seconary level that will be scored for relevance
    to the original paper via mentions to the tertiary papers
    """
    def __init__(self, bibcode, adsdb, primary_bibcodes, primary_mentions):
        super(SecondaryPub, self).__init__()
        print "Making a SecondaryPub for {0}".format(bibcode)
        self._bibcode = bibcode
        self._adsdb = adsdb
        self._primary_bibcodes = primary_bibcodes

        # Mentions vector for primary references
        self._primary_mentions = primary_mentions

        # Mentions vector for tertiary reference
        self._tertiary_mentions = np.zeros(self._primary_mentions.shape)

        # TODO read and build the rich citations for this publication

        # query ADS for this paper
        pub = adsdb[bibcode]
        if pub is None:
            # nothing we can do
            print "mentionsrec could not get {0} from ADS".format(bibcode)
            return

        # Analyze only quaternay references that appear in the orginal
        # paper too (and thus are likely to be relevant).
        reference_bibcodes = pub.reference_bibcodes
        if reference_bibcodes is None:
            return
            # FIXME nothing can be done
        for bibcode in reference_bibcodes:
            if bibcode not in self._primary_bibcodes:
                continue
            else:
                i = self._primary_bibcodes.index(bibcode)
                # TODO combine bibcode to number of mentions to fill in
                # self._tertiary_mentions
                # FIXME this gives unit weit all all cited tertiary papers
                self._tertiary_mentions[i] = 1

    @property
    def score(self):
        """http://en.wikipedia.org/wiki/Cosine_similarity"""
        return np.sum(self._primary_mentions * self._tertiary_mentions) \
            / (np.hypot(self._primary_mentions)
               * np.hypot(self._tertiary_mentions))
