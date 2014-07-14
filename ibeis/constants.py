from __future__ import absolute_import, division, print_function
import utool
import numpy as np


class PATH_NAMES(object):
    """ Path names for internal IBEIS database """
    sqldb     = '_ibeis_database.sqlite3'
    _ibsdb    = '_ibsdb'
    cache     = '_ibeis_cache'
    chips     = 'chips'
    flann     = 'flann'
    images    = 'images'
    qres      = 'qres'
    bigcache  = 'bigcache'
    detectimg = 'detectimg'
    thumbs    = 'thumbs'

UNKNOWN_NID = 0
# Names normalized to the standard UNKNOWN_NAME
ACCEPTED_UNKNOWN_NAMES = set(['Unassigned'])

# Name used to denote that idkwtfthisis
ENCTEXT_PREFIX = 'enc_'

INDIVIDUAL_KEY = 'INDIVIDUAL_KEY'
SPECIES_KEY    = 'SPECIES_KEY'
EMPTY_KEY      = ''
UNKNOWN        = '____'
KEY_DEFAULTS   = {
    INDIVIDUAL_KEY : '____',
    SPECIES_KEY    : '____',
}

# Define the special metadata for annotation

ROSEMARY_ANNOT_METADATA = [
    ('local_name'    , 'Local name:',    str),
    ('sun'           , 'Sun:',           ['FS', 'PS', 'NS']),
    ('wind'          , 'Wind:',          ['NW', 'LW', 'MW', 'SW']),
    ('rain'          , 'Rain:',          ['NR', 'LR', 'MR', 'HR']),
    ('cover'         , 'Cover:',         float),
    ('grass'         , 'Grass:',         ['less hf', 'less hk', 'less belly']),
    ('grass_color'   , 'Grass Colour:',  ['B', 'BG', 'GB', 'G']),
    ('grass_species' , 'Grass Species:', str),
    ('bush_type'     , 'Bush type:',     ['OG', 'LB', 'MB', 'TB']),
    ('bit'           , 'Bit:',           int),
    ('other_speceis' , 'Other Species:', str),
]

ROSEMARY_KEYS = utool.get_list_column(ROSEMARY_ANNOT_METADATA, 0)
KEY_DEFAULTS.update(**{key: UNKNOWN for key in ROSEMARY_KEYS})


AL_RELATION_TABLE = 'annotation_lblannot_relationship'
ANNOTATION_TABLE  = 'annotations'
CHIP_TABLE        = 'chips'
CONFIG_TABLE      = 'configs'
EG_RELATION_TABLE = 'encounter_image_relationship'
ENCOUNTER_TABLE   = 'encounters'
FEATURE_TABLE     = 'features'
GL_RELATION_TABLE = 'image_lblimage_relationship'
IMAGE_TABLE       = 'images'
LBLANNOT_TABLE    = 'lblannot'
LBLIMAGE_TABLE    = 'lblimage'
LBLTYPE_TABLE     = 'keys'

UNKNOWN_PURPLE_RGBA255 = np.array((102,   0, 153, 255))
NAME_BLUE_RGBA255      = np.array((20, 20, 235, 255))
NAME_RED_RGBA255       = np.array((235, 20, 20, 255))
NEW_YELLOW_RGBA255     = np.array((235, 235, 20, 255))

UNKNOWN_PURPLE_RGBA01 = UNKNOWN_PURPLE_RGBA255 / 255.0
NAME_BLUE_RGBA01      = NAME_BLUE_RGBA255 / 255.0
NAME_RED_RGBA01       = NAME_RED_RGBA255 / 255.0
NEW_YELLOW_RGBA01     = NEW_YELLOW_RGBA255 / 255.0

EXEMPLAR_ENCTEXT = 'Exemplars'
ALL_IMAGE_ENCTEXT = 'All Images'
UNREVIEWED_IMAGE_ENCTEXT = 'Unreviewed Images'
REVIEWED_IMAGE_ENCTEXT = 'Reviewed Images'

IMAGE_THUMB_SUFFIX = '_thumb.png'
CHIP_THUMB_SUFFIX  = '_chip_thumb.png'

# FIXME UNKNOWN should not be a valid species
VALID_SPECIES = ['zebra_plains', 'zebra_grevys', 'giraffe', UNKNOWN]
SPECIES_NICE = ['Plains Zebras', 'Grevy\'s Zebras', 'Giraffes', 'Unknown']


# clean namespace
del utool
del np
