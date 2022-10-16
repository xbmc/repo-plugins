# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Implements VRT MAX GraphQL API functionality"""

from __future__ import absolute_import, division, unicode_literals


EPISODE_TILE = """
    fragment episodeTile on EpisodeTile {
      __typename
      id
      title
      episode {
        __typename
        id
        name
        available
        whatsonId
        title
        description
        subtitle
        permalink
        logo
        brand
        brandLogos {
          type
          mono
          primary
        }
        image {
          alt
          templateUrl
        }

        ageRaw
        ageValue

        durationRaw
        durationValue
        durationSeconds

        episodeNumberRaw
        episodeNumberValue
        episodeNumberShortValue

        onTimeRaw
        onTimeValue
        onTimeShortValue

        offTimeRaw
        offTimeValue
        offTimeShortValue

        productPlacementValue
        productPlacementShortValue

        regionRaw
        regionValue
        program {
          title
          id
          link
          programType
          description
          shortDescription
          subtitle
          announcementType
          announcementValue
          whatsonId
          image {
            alt
            templateUrl
          }
          posterImage {
            alt
            templateUrl
          }
        }
        season {
          id
          titleRaw
          titleValue
          titleShortValue
        }
        analytics {
          airDate
          categories
          contentBrand
          episode
          mediaSubtype
          mediaType
          name
          pageName
          season
          show
        }
        primaryMeta {
          longValue
          shortValue
          type
          value
          __typename
        }
        secondaryMeta {
          longValue
          shortValue
          type
          value
          __typename
        }
        watchAction {
          avodUrl
          completed
          resumePoint
          resumePointTotal
          resumePointProgress
          resumePointTitle
          episodeId
          videoId
          publicationId
          streamId
        }
        favoriteAction {
          favorite
          id
          title
        }
      }
    }
"""
