"""
AUTOGENERATED ON 17:57:41 2015/11/17
AutogenCommandLine:
    python -m ibeis.control.DB_SCHEMA --test-autogen_db_schema --force-incremental-db-update --write
    python -m ibeis.control.DB_SCHEMA --test-autogen_db_schema --force-incremental-db-update --diff=1
    python -m ibeis.control.DB_SCHEMA --test-autogen_db_schema --force-incremental-db-update
"""
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
from ibeis import constants as const


# =======================
# Schema Version Current
# =======================


VERSION_CURRENT = '1.4.6'


def update_current(db, ibs=None):
    db.add_table(const.AL_RELATION_TABLE, [
        ('alr_rowid',                    'INTEGER PRIMARY KEY'),
        ('annot_rowid',                  'INTEGER NOT NULL'),
        ('lblannot_rowid',               'INTEGER NOT NULL'),
        ('config_rowid',                 'INTEGER DEFAULT 0'),
        ('alr_confidence',               'REAL DEFAULT 0.0'),
    ],
        docstr='''
        Used to store one-to-many the relationship between annotations
        (annots) and labels
        ''',
        superkeys=[('annot_rowid', 'lblannot_rowid', 'config_rowid')],
        relates=('annotations', 'lblannot'),
        shortname='alr',
    )

    db.add_table(const.ANNOTATION_TABLE, [
        ('annot_rowid',                  'INTEGER PRIMARY KEY'),
        ('annot_parent_rowid',           'INTEGER'),
        ('annot_uuid',                   'UUID NOT NULL'),
        ('image_rowid',                  'INTEGER NOT NULL'),
        ('annot_xtl',                    'INTEGER NOT NULL'),
        ('annot_ytl',                    'INTEGER NOT NULL'),
        ('annot_width',                  'INTEGER NOT NULL'),
        ('annot_height',                 'INTEGER NOT NULL'),
        ('annot_theta',                  'REAL DEFAULT 0.0'),
        ('annot_num_verts',              'INTEGER NOT NULL'),
        ('annot_verts',                  'TEXT'),
        ('annot_yaw',                    'REAL'),
        ('annot_detect_confidence',      'REAL DEFAULT -1.0'),
        ('annot_exemplar_flag',          'INTEGER DEFAULT 0'),
        ('annot_note',                   'TEXT'),
        ('annot_visual_uuid',            'UUID NOT NULL'),
        ('annot_semantic_uuid',          'UUID'),
        ('name_rowid',                   'INTEGER DEFAULT 0'),
        ('species_rowid',                'INTEGER DEFAULT 0'),
        ('annot_quality',                'INTEGER'),
        ('contributor_rowid',            'INTEGER'),
        ('annot_age_months_est_min',     'INTEGER DEFAULT -1'),
        ('annot_age_months_est_max',     'INTEGER DEFAULT -1'),
        ('annot_tags',                   'TEXT'),
    ],
        docstr='''
        Mainly used to store the geometry of the annotation within its parent
        image The one-to-many relationship between images and annotations is
        encoded here
        ''',
        superkeys=[('annot_uuid',), ('annot_visual_uuid',)],
        shortname='annot',
        extern_tables=['names', 'species', 'images'],
        primary_superkey=('annot_visual_uuid',),
        dependsmap={
            'annot_parent_rowid': ('annotations', ('annot_rowid',), ('annot_visual_uuid',)),
            'contributor_rowid' : ('contributors', None, None),
            'image_rowid'       : ('images', ('image_rowid',), ('image_uuid',)),
            'name_rowid'        : ('names', ('name_rowid',), ('name_text',)),
            'species_rowid'     : ('species', ('species_rowid',), ('species_text',)),
    },
    )

    db.add_table(const.GA_RELATION_TABLE, [
        ('gar_rowid',                    'INTEGER PRIMARY KEY'),
        ('annotgroup_rowid',             'INTEGER NOT NULL'),
        ('annot_rowid',                  'INTEGER'),
    ],
        docstr='''
        Relationship between annotgroups and annots (many to many mapping) the
        many-to-many relationship between annots and annotgroups is encoded
        here annotgroup_annotation_relationship stands for annotgroup-
        annotation-pairs.
        ''',
        superkeys=[('annotgroup_rowid', 'annot_rowid')],
    )

    db.add_table(const.ANNOTGROUP_TABLE, [
        ('annotgroup_rowid',             'INTEGER PRIMARY KEY'),
        ('annotgroup_uuid',              'UUID NOT NULL'),
        ('annotgroup_text',              'TEXT NOT NULL'),
        ('annotgroup_note',              'TEXT NOT NULL'),
    ],
        docstr='''
        List of all annotation groups (annotgroups)
        ''',
        superkeys=[('annotgroup_text',)],
    )

    db.add_table(const.ANNOTMATCH_TABLE, [
        ('annotmatch_rowid',             'INTEGER PRIMARY KEY'),
        ('annot_rowid1',                 'INTEGER NOT NULL'),
        ('annot_rowid2',                 'INTEGER NOT NULL'),
        ('annotmatch_truth',             'INTEGER DEFAULT 2'),
        ('annotmatch_confidence',        'REAL DEFAULT 0'),
        ('annotmatch_is_hard',           'INTEGER'),
        ('annotmatch_is_scenerymatch',   'INTEGER'),
        ('annotmatch_is_photobomb',      'INTEGER'),
        ('annotmatch_is_nondistinct',    'INTEGER'),
        ('annotmatch_note',              'TEXT'),
        ('annotmatch_reviewed',          'INTEGER'),
        ('annotmatch_reviewer',          'TEXT'),
    ],
        docstr='''
        Sparsely stores explicit matching / not matching information. This
        serves as marking weather or not an annotation pair has been reviewed.
        ''',
        superkeys=[('annot_rowid1', 'annot_rowid2')],
        relates=('annotations', 'annotations'),
        dependsmap={
            'annot_rowid1': ('annotations', ('annot_rowid',), ('annot_visual_uuid',)),
            'annot_rowid2': ('annotations', ('annot_rowid',), ('annot_visual_uuid',)),
    },
    )

    db.add_table(const.CONFIG_TABLE, [
        ('config_rowid',                 'INTEGER PRIMARY KEY'),
        ('contributor_rowid',            'UUID'),
        ('config_suffix',                'TEXT NOT NULL'),
    ],
        docstr='''
        Used to store the ids of algorithm configurations that generate
        annotation lblannots.  Each user will have a config id for manual
        contributions
        ''',
        superkeys=[('config_suffix',)],
        dependsmap={
            'contributor_rowid': ('contributors', ('contributor_rowid',), ('contributor_tag',)),
    },
    )

    db.add_table(const.CONTRIBUTOR_TABLE, [
        ('contributor_rowid',            'INTEGER PRIMARY KEY'),
        ('contributor_uuid',             'UUID NOT NULL'),
        ('contributor_tag',              'TEXT'),
        ('contributor_name_first',       'TEXT'),
        ('contributor_name_last',        'TEXT'),
        ('contributor_location_city',    'TEXT'),
        ('contributor_location_state',   'TEXT'),
        ('contributor_location_country', 'TEXT'),
        ('contributor_location_zip',     'TEXT'),
        ('contributor_note',             'TEXT'),
    ],
        docstr='''
        Used to store the contributors to the project
        ''',
        superkeys=[('contributor_tag',)],
    )

    db.add_table(const.EG_RELATION_TABLE, [
        ('egr_rowid',                    'INTEGER PRIMARY KEY'),
        ('image_rowid',                  'INTEGER NOT NULL'),
        ('encounter_rowid',              'INTEGER'),
    ],
        docstr='''
        Relationship between encounters and images (many to many mapping) the
        many-to-many relationship between images and encounters is encoded
        here encounter_image_relationship stands for encounter-image-pairs.
        ''',
        superkeys=[('image_rowid', 'encounter_rowid')],
        relates=('images', 'encounters'),
        shortname='egr',
        dependsmap={
            'encounter_rowid': ('encounters', ('encounter_rowid',), ('encounter_text',)),
            'image_rowid'    : ('images', ('image_rowid',), ('image_uuid',)),
    },
    )

    db.add_table(const.ENCOUNTER_TABLE, [
        ('encounter_rowid',              'INTEGER PRIMARY KEY'),
        ('encounter_uuid',               'UUID NOT NULL'),
        ('config_rowid',                 'INTEGER'),
        ('encounter_text',               'TEXT NOT NULL'),
        ('encounter_note',               'TEXT NOT NULL'),
        ('encounter_start_time_posix',   'INTEGER'),
        ('encounter_end_time_posix',     'INTEGER'),
        ('encounter_gps_lat',            'INTEGER'),
        ('encounter_gps_lon',            'INTEGER'),
        ('encounter_processed_flag',     'INTEGER DEFAULT 0'),
        ('encounter_shipped_flag',       'INTEGER DEFAULT 0'),
        ('encounter_smart_xml_fname',    'TEXT'),
        ('encounter_smart_waypoint_id',  'INTEGER'),
    ],
        docstr='''
        List of all encounters
        ''',
        superkeys=[('encounter_text',)],
        dependsmap={
            'config_rowid': ('configs', ('config_rowid',), ('config_suffix',)),
    },
    )

    db.add_table(const.GL_RELATION_TABLE, [
        ('glr_rowid',                    'INTEGER PRIMARY KEY'),
        ('image_rowid',                  'INTEGER NOT NULL'),
        ('lblimage_rowid',               'INTEGER NOT NULL'),
        ('config_rowid',                 'INTEGER DEFAULT 0'),
        ('glr_confidence',               'REAL DEFAULT 0.0'),
    ],
        docstr='''
        Used to store one-to-many the relationship between images and labels
        ''',
        superkeys=[('image_rowid', 'lblimage_rowid', 'config_rowid')],
        relates=('images', 'lblimage'),
        shortname='glr',
    )

    db.add_table(const.IMAGE_TABLE, [
        ('image_rowid',                  'INTEGER PRIMARY KEY'),
        ('contributor_rowid',            'INTEGER'),
        ('image_uuid',                   'UUID NOT NULL'),
        ('image_uri',                    'TEXT NOT NULL'),
        ('image_ext',                    'TEXT NOT NULL'),
        ('image_original_name',          'TEXT NOT NULL'),
        ('image_width',                  'INTEGER DEFAULT -1'),
        ('image_height',                 'INTEGER DEFAULT -1'),
        ('image_time_posix',             'INTEGER DEFAULT -1'),
        ('image_gps_lat',                'REAL DEFAULT -1.0'),
        ('image_gps_lon',                'REAL DEFAULT -1.0'),
        ('image_toggle_enabled',         'INTEGER DEFAULT 0'),
        ('image_toggle_reviewed',        'INTEGER DEFAULT 0'),
        ('image_note',                   'TEXT'),
        ('image_timedelta_posix',        'INTEGER DEFAULT 0'),
        ('image_original_path',          'TEXT'),
        ('image_location_code',          'TEXT'),
        ('party_rowid',                  'INTEGER'),
    ],
        docstr='''
        First class table used to store image locations and meta-data
        ''',
        superkeys=[('image_uuid',)],
        shortname='image',
        extern_tables=['party', 'contributors'],
        dependsmap={
            'contributor_rowid': ('contributors', ('contributor_rowid',), ('contributor_tag',)),
            'party_rowid'      : ('party', ('party_rowid',), ('party_tag',)),
    },
    )

    db.add_table(const.LBLTYPE_TABLE, [
        ('lbltype_rowid',                'INTEGER PRIMARY KEY'),
        ('lbltype_text',                 'TEXT NOT NULL'),
        ('lbltype_default',              'TEXT NOT NULL'),
    ],
        docstr='''
        List of keys used to define the categories of annotation lables, text
        is for human-readability. The lbltype_default specifies the
        lblannot_value of annotations with a relationship of some
        lbltype_rowid
        ''',
        superkeys=[('lbltype_text',)],
    )

    db.add_table(const.LBLANNOT_TABLE, [
        ('lblannot_rowid',               'INTEGER PRIMARY KEY'),
        ('lblannot_uuid',                'UUID NOT NULL'),
        ('lbltype_rowid',                'INTEGER NOT NULL'),
        ('lblannot_value',               'TEXT NOT NULL'),
        ('lblannot_note',                'TEXT'),
    ],
        docstr='''
        Used to store the labels / attributes of annotations. E.G name,
        species
        ''',
        superkeys=[('lbltype_rowid', 'lblannot_value')],
    )

    db.add_table(const.LBLIMAGE_TABLE, [
        ('lblimage_rowid',               'INTEGER PRIMARY KEY'),
        ('lblimage_uuid',                'UUID NOT NULL'),
        ('lbltype_rowid',                'INTEGER NOT NULL'),
        ('lblimage_value',               'TEXT NOT NULL'),
        ('lblimage_note',                'TEXT'),
    ],
        docstr='''
        Used to store the labels (attributes) of images
        ''',
        superkeys=[('lbltype_rowid', 'lblimage_value')],
    )

    db.add_table(const.METADATA_TABLE, [
        ('metadata_rowid',               'INTEGER PRIMARY KEY'),
        ('metadata_key',                 'TEXT'),
        ('metadata_value',               'TEXT'),
    ],
        docstr='''
        The table that stores permanently all of the metadata about the
        database (tables, etc)
        ''',
        superkeys=[('metadata_key',)],
    )

    db.add_table(const.NAME_TABLE, [
        ('name_rowid',                   'INTEGER PRIMARY KEY'),
        ('name_uuid',                    'UUID NOT NULL'),
        ('name_text',                    'TEXT NOT NULL'),
        ('name_note',                    'TEXT'),
        ('name_temp_flag',               'INTEGER DEFAULT 0'),
        ('name_alias_text',              'TEXT'),
        ('name_sex',                     'INTEGER DEFAULT -1'),
    ],
        docstr='''
        Stores the individual animal names
        ''',
        superkeys=[('name_text',)],
    )

    db.add_table(const.PARTY_TABLE, [
        ('party_rowid',                  'INTEGER PRIMARY KEY'),
        ('party_tag',                    'TEXT NOT NULL'),
    ],
        docstr='''
        Serves as a group for contributors
        ''',
        superkeys=[('party_tag',)],
    )

    db.add_table(const.SPECIES_TABLE, [
        ('species_rowid',                'INTEGER PRIMARY KEY'),
        ('species_uuid',                 'UUID NOT NULL'),
        ('species_text',                 'TEXT NOT NULL'),
        ('species_note',                 'TEXT'),
    ],
        docstr='''
        Stores the different animal species
        ''',
        superkeys=[('species_text',)],
    )
