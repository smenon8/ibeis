"""
sysres.py == system_resources
Module for dealing with system resoureces in the context of IBEIS
but without the need for an actual IBEIS Controller

"""
from __future__ import absolute_import, division, print_function
import os
from os.path import exists, join, realpath
import utool
import utool as ut
from six.moves import input
from utool import util_cache, util_list
from ibeis import constants as const
from ibeis import params

# Inject utool functions
(print, print_, printDBG, rrr, profile) = utool.inject(
    __name__, '[sysres]', DEBUG=False)

WORKDIR_CACHEID   = 'work_directory_cache_id'
DEFAULTDB_CAHCEID = 'cached_dbdir'
LOGDIR_CACHEID = utool.logdir_cacheid
__APPNAME__ = 'ibeis'


def get_ibeis_resource_dir():
    return ut.ensure_app_resource_dir('ibeis')


def _ibeis_cache_dump():
    util_cache.global_cache_dump(appname=__APPNAME__)


def _ibeis_cache_write(key, val):
    """ Writes to global IBEIS cache """
    print('[sysres] set %s=%r' % (key, val))
    util_cache.global_cache_write(key, val, appname=__APPNAME__)


def _ibeis_cache_read(key, **kwargs):
    """ Reads from global IBEIS cache """
    return util_cache.global_cache_read(key, appname=__APPNAME__, **kwargs)


# Specific cache getters / setters

def set_default_dbdir(dbdir):
    printDBG('[sysres] SETTING DEFAULT DBDIR: %r' % dbdir)
    _ibeis_cache_write(DEFAULTDB_CAHCEID, dbdir)


def get_default_dbdir():
    dbdir = _ibeis_cache_read(DEFAULTDB_CAHCEID, default=None)
    printDBG('[sysres] READING DEFAULT DBDIR: %r' % dbdir)
    return dbdir


def get_syncdir():
    # TODO: Allow dirs in syncdir to count as in workdir
    secret = 'AFETDAKURTJ6WH3PXYOTJDBO3KBC2KJJP'  # NOQA


def get_workdir(allow_gui=True):
    """ Returns the work directory set for this computer.  If allow_gui is true,
    a dialog will ask a user to specify the workdir if it does not exist. """
    work_dir = _ibeis_cache_read(WORKDIR_CACHEID, default='.')
    if work_dir is not '.' and exists(work_dir):
        return work_dir
    if allow_gui:
        work_dir = set_workdir()
        return get_workdir(allow_gui=False)
    return None


ALLOW_GUI = ut.WIN32 or os.environ.get('DISPLAY', None) is not None


def set_workdir(work_dir=None, allow_gui=ALLOW_GUI):
    """ Sets the workdirectory for this computer """
    if work_dir is None:
        if allow_gui:
            work_dir = guiselect_workdir()
        else:
            work_dir = input('specify a workdir: ')
    if work_dir is None or not exists(work_dir):
        raise AssertionError('invalid workdir=%r' % work_dir)
    _ibeis_cache_write(WORKDIR_CACHEID, work_dir)


def set_logdir(log_dir):
    from os.path import realpath, expanduser
    log_dir = realpath(expanduser(log_dir))
    utool.ensuredir(log_dir, verbose=True)
    utool.stop_logging()
    _ibeis_cache_write(LOGDIR_CACHEID, log_dir)
    utool.start_logging(appname=__APPNAME__)


def get_logdir():
    return _ibeis_cache_read(LOGDIR_CACHEID, default=ut.get_logging_dir(appname='ibeis'))


def get_rawdir():
    """ Returns the standard raw data directory """
    workdir = get_workdir()
    rawdir = utool.truepath(join(workdir, '../raw'))
    return rawdir


def guiselect_workdir():
    """ Prompts the user to specify a work directory """
    import guitool
    guitool.ensure_qtapp()
    # Gui selection
    work_dir = guitool.select_directory('Work dir not currently set.' +
                                        'Select a work directory')
    # Make sure selection is ok
    if not exists(work_dir):
        try_again = guitool.user_option(
            paremt=None,
            msg='Directory %r does not exist.' % work_dir,
            title='get work dir failed',
            options=['Try Again'],
            use_cache=False)
        if try_again == 'Try Again':
            return guiselect_workdir()
    return work_dir


def get_dbalias_dict():
    dbalias_dict = {}
    if utool.is_developer():
        # For jon's convinience
        dbalias_dict.update({
            'NAUTS':            'NAUT_Dan',
            'WD':               'WD_Siva',
            'LF':               'LF_all',
            'GZ':               'GZ_ALL',
            'MOTHERS':          'PZ_MOTHERS',
            'FROGS':            'Frogs',
            'TOADS':            'WY_Toads',
            'SEALS_SPOTTED':    'Seals',

            'OXFORD':           'Oxford_Buildings',
            'PARIS':            'Paris_Buildings',

            'JAG_KELLY':        'JAG_Kelly',
            'JAG_KIERYN':       'JAG_Kieryn',
            'WILDEBEAST':       'Wildebeast',
            'WDOGS':            'WD_Siva',

            'PZ':               'PZ_FlankHack',
            'PZ2':              'PZ-Sweatwater',
            'PZ_MARIANNE':      'PZ_Marianne',
            'PZ_DANEXT_TEST':   'PZ_DanExt_Test',
            'PZ_DANEXT_ALL':    'PZ_DanExt_All',

            'LF_ALL':           'LF_all',
            'WS_HARD':          'WS_hard',
            'SONOGRAMS':        'sonograms',

        })
        dbalias_dict['JAG'] = dbalias_dict['JAG_KELLY']
    return dbalias_dict


def db_to_dbdir(db, allow_newdir=False, extra_workdirs=[], use_sync=False):
    """ Implicitly gets dbdir. Searches for db inside of workdir """
    if utool.VERBOSE:
        print('[sysres] db_to_dbdir: db=%r, allow_newdir=%r' % (db, allow_newdir))

    work_dir = get_workdir()
    dbalias_dict = get_dbalias_dict()

    workdir_list = []
    for extra_dir in extra_workdirs:
        if exists(extra_dir):
            workdir_list.append(extra_dir)
    if use_sync:
        sync_dir = join(work_dir, '../sync')
        if exists(sync_dir):
            workdir_list.append(sync_dir)
    workdir_list.append(work_dir)  # TODO: Allow multiple workdirs

    # Check all of your work directories for the database
    for _dir in workdir_list:
        dbdir = realpath(join(_dir, db))
        # Use db aliases
        if not exists(dbdir) and db.upper() in dbalias_dict:
            dbdir = join(_dir, dbalias_dict[db.upper()])
        if exists(dbdir):
            break

    # Create the database if newdbs are allowed in the workdir
    #print('allow_newdir=%r' % allow_newdir)
    if allow_newdir:
        utool.ensuredir(dbdir, verbose=True)

    # Complain if the implicit dbdir does not exist
    if not exists(dbdir):
        print('!!!')
        print('[sysres] WARNING: db=%r not found in work_dir=%r' %
              (db, work_dir))
        fname_list = os.listdir(work_dir)
        lower_list = [fname.lower() for fname in fname_list]
        index = util_list.listfind(lower_list, db.lower())
        if index is not None:
            print('[sysres] WARNING: db capitalization seems to be off')
            if not utool.STRICT:
                print('[sysres] attempting to fix it')
                db = fname_list[index]
                dbdir = join(work_dir, db)
                print('[sysres] dbdir=%r' % dbdir)
                print('[sysres] db=%r' % db)
        if not exists(dbdir):
            msg = '[sysres!] ERROR: Database does not exist and allow_newdir=False'
            print('<!!!>')
            print(msg)
            print('[sysres!] Here is a list of valid dbs: ' +
                  utool.indentjoin(sorted(fname_list), '\n  * '))
            print('[sysres!] dbdir=%r' % dbdir)
            print('[sysres!] db=%r' % db)
            print('[sysres!] work_dir=%r' % work_dir)
            print('</!!!>')
            raise AssertionError(msg)
        print('!!!')
    return dbdir


def get_args_dbdir(defaultdb=None, allow_newdir=False, db=None, dbdir=None, cache_priority=True):
    """ Machinery for finding a database directory """
    if not utool.QUIET and utool.VERBOSE:
        print('[sysres] get_args_dbdir: parsing commandline for dbdir')
        print('[sysres] defaultdb=%r, allow_newdir=%r, cache_priority=%r' % (defaultdb, allow_newdir, cache_priority))
        print('[sysres] db=%r, dbdir=%r' % (db, dbdir))

    if ut.get_argflag('--nodbcache'):
        return None

    def _db_arg_priorty(dbdir_, db_):
        invalid = ['', ' ', '.', 'None']
        # Invalidate bad db's
        if dbdir_ in invalid:
            dbdir_ = None
        if db_ in invalid:
            db_ = None
        # Return values with a priority
        if dbdir_ is not None:
            return realpath(dbdir_)
        if db_ is not None:
            return db_to_dbdir(db_, allow_newdir=allow_newdir)
        return None

    if not cache_priority:
        # Check function's passed args
        dbdir = _db_arg_priorty(dbdir, db)
        if dbdir is not None:
            return dbdir
        # Get command line args
        dbdir = params.args.dbdir
        db = params.args.db
        # Check command line passed args
        dbdir = _db_arg_priorty(dbdir, db)
        if dbdir is not None:
            return dbdir
    # Return cached database directory
    if defaultdb == 'cache':
        return get_default_dbdir()
    else:
        return db_to_dbdir(defaultdb, allow_newdir=allow_newdir)


def is_ibeisdb(path):
    """ Checks to see if path contains the IBEIS internal dir """
    return exists(join(path, const.PATH_NAMES._ibsdb))


def is_hsdb(dbdir):
    return is_hsdbv4(dbdir) or is_hsdbv3(dbdir)


def is_hsdbv4(dbdir):
    has4 = (exists(join(dbdir, '_hsdb')) and
            exists(join(dbdir, '_hsdb', 'name_table.csv')) and
            exists(join(dbdir, '_hsdb', 'image_table.csv')) and
            exists(join(dbdir, '_hsdb', 'chip_table.csv')))
    return has4


def is_hsdbv3(dbdir):
    has3 = (exists(join(dbdir, '.hs_internals')) and
            exists(join(dbdir, '.hs_internals', 'name_table.csv')) and
            exists(join(dbdir, '.hs_internals', 'image_table.csv')) and
            exists(join(dbdir, '.hs_internals', 'chip_table.csv')))
    return has3


def get_hsinternal(hsdb_dir):
    internal_dir = join(hsdb_dir, '_hsdb')
    if not is_hsdbv4(hsdb_dir):
        internal_dir = join(hsdb_dir, '.hs_internals')
    return internal_dir


def is_hsinternal(dbdir):
    return exists(join(dbdir, '.hs_internals'))


def get_ibsdb_list(workdir=None):
    r"""
    Lists the available valid ibeis databases inside of a work directory

    Args:
        workdir (None):

    Returns:
        IBEISController: ibsdb_list -  ibeis controller object

    CommandLine:
        python -m ibeis.init.sysres --test-get_ibsdb_list

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis.init.sysres import *  # NOQA
        >>> workdir = None
        >>> ibsdb_list = get_ibsdb_list(workdir)
        >>> result = str('\n'.join(ibsdb_list))
        >>> print(result)
    """
    import numpy as np
    if workdir is None:
        workdir = get_workdir()
    dbname_list = os.listdir(workdir)
    dbpath_list = np.array([join(workdir, name) for name in dbname_list])
    is_ibs_list = np.array(list(map(is_ibeisdb, dbpath_list)))
    ibsdb_list  = dbpath_list[is_ibs_list].tolist()
    return ibsdb_list


def ensure_pz_mtest():
    """
    Ensures that you have the PZ_MTEST dataset

    Example:
        >>> # DISABLE DOCTEST
        >>> pass
    """
    from ibeis import sysres
    import utool
    workdir = sysres.get_workdir()
    mtest_zipped_url = const.ZIPPED_URLS.PZ_MTEST
    mtest_dir = utool.grab_zipped_url(mtest_zipped_url, ensure=True, download_dir=workdir)
    print('have mtest_dir=%r' % (mtest_dir,))
    # update the the newest database version
    import ibeis
    ibs = ibeis.opendb('PZ_MTEST')
    print('cleaning up old database and ensureing everything is properly computed')
    ibs.db.vacuum()
    valid_aids = ibs.get_valid_aids()
    assert len(valid_aids) == 119
    ibs.update_annot_semantic_uuids(valid_aids)
    if ut.VERYVERBOSE:
        ibs.print_annotation_table()
    nid = ibs.get_name_rowids_from_text('', ensure=False)
    if nid is not None:
        ibs.set_name_texts([nid], ['lostname'])


def ensure_pz_mtest_mergesplit_test():
    r"""

    CommandLine:
        python -m ibeis.init.sysres --test-ensure_pz_mtest_mergesplit_test

    Example:
        >>> # DISABLE_DOCTEST
        >>> from ibeis.init.sysres import *  # NOQA
        >>> ensure_pz_mtest_mergesplit_test()
    """
    import ibeis
    ibeis.ensure_pz_mtest()
    workdir = ibeis.sysres.get_workdir()
    dbpath = join(workdir, 'PZ_MERGESPLIT_MTEST')
    mtest_dbpath = join(workdir, 'PZ_MTEST')
    if ut.checkpath(dbpath):
        return

    source_dbdir = mtest_dbpath
    dest_dbdir = join(workdir, 'PZ_MERGESPLIT_MTEST')

    if False:
        ut.delete(dest_dbdir)

    def copy_ibeisdb(source_dbdir, dest_dbdir):
        # TODO; rectify with rsycn script
        from os.path import normpath
        exclude_dirs = [ut.ensure_unixslash(normpath(rel)) for rel in ibeis.const.EXCLUDE_COPY_REL_DIRS + ['_hsdb', '.hs_internals']]

        rel_tocopy = ut.glob(source_dbdir, '*', exclude_dirs=exclude_dirs, recursive=True, with_files=True, with_dirs=False, fullpath=False)
        rel_tocopy_dirs = ut.glob(source_dbdir, '*', exclude_dirs=exclude_dirs, recursive=True, with_files=False, with_dirs=True, fullpath=False)

        src_list = [join(source_dbdir, relpath) for relpath in rel_tocopy]
        dst_list = [join(dest_dbdir, relpath) for relpath in rel_tocopy]

        # ensure directories exist
        rel_tocopy_dirs = [dest_dbdir] + [join(dest_dbdir, dpath_) for dpath_ in rel_tocopy_dirs]
        for dpath in rel_tocopy_dirs:
            ut.ensuredir(dpath)
        # copy files
        ut.copy(src_list, dst_list)

    copy_ibeisdb(source_dbdir, dest_dbdir)

    ibs = ibeis.opendb('PZ_MERGESPLIT_MTEST')
    assert len(ibs.get_valid_aids()) == 119
    assert len(ibs.get_valid_nids()) == 41

    aid_list = ibs.get_valid_aids()
    aids_list, nid_list = ibs.group_annots_by_name(aid_list)
    num_aids = list(map(len, aids_list))

    # num cases wanted
    num_merge = 3
    num_split = 1
    num_combo = 1

    # num inputs needed
    num_merge_names = num_merge
    num_split_names = num_split * 2
    num_combo_names = num_combo * 3

    total_names = num_merge_names + num_split_names + num_combo_names

    modify_aids = ut.list_take(aids_list, ut.list_argsort(num_aids, reverse=True)[0:total_names])

    merge_nids1 = ibs.make_next_nids(num_merge, location_text='XMERGE')
    merge_nids2 = ibs.make_next_nids(num_merge, location_text='XMERGE')
    split_nid  = ibs.make_next_nids(num_split, location_text='XSPLIT')[0]
    combo_nids = ibs.make_next_nids(num_combo * 2, location_text='XCOMBO')

    # the first 3 become merge cases
    #left = 0
    #right = left + num_merge
    for aids, nid1, nid2 in zip(modify_aids[0:3], merge_nids1, merge_nids2):
        #ibs.get_annot_nids(aids)
        aids_ = aids[::2]
        ibs.set_annot_name_rowids(aids_, [nid1] * len(aids_))
        ibs.set_annot_name_rowids(aids_, [nid2] * len(aids_))

    # the next 2 become split cases
    #left = right
    #right = left + num_split_names
    for aids in modify_aids[3:5]:
        ibs.set_annot_name_rowids(aids, [split_nid] * len(aids))

    #left = right
    #right = left + num_combo_names
    # The final 3 are a combination case
    for aids in modify_aids[5:8]:
        aids_even = aids[::2]
        aids_odd = aids[1::2]
        ibs.set_annot_name_rowids(aids_even, [combo_nids[0]] * len(aids_even))
        ibs.set_annot_name_rowids(aids_odd, [combo_nids[1]] * len(aids_odd))

    final_result = ibs.unflat_map(ibs.get_annot_nids, modify_aids)
    print('final_result = %s' % (ut.list_str(final_result),))


def ensure_nauts():
    """ Ensures that you have the NAUT_test dataset """
    from ibeis import sysres
    import utool
    workdir = sysres.get_workdir()
    nauts_zipped_url = const.ZIPPED_URLS.NAUTS
    nauts_dir = utool.grab_zipped_url(nauts_zipped_url, ensure=True, download_dir=workdir)
    print('have nauts_dir=%r' % (nauts_dir,))


def get_global_distinctiveness_modeldir(ensure=True):
    resource_dir = get_ibeis_resource_dir()
    global_distinctdir = join(resource_dir, const.PATH_NAMES.distinctdir)
    if ensure:
        ut.ensuredir(global_distinctdir)
    return global_distinctdir


def resolve_species(species_code):
    r"""
    Args:
        species_code (str): can either be species_code or species_text

    CommandLine:
        python -m ibeis.init.sysres --test-resolve_species

    Example:
        >>> # DISABLE_DOCTEST
        >>> from ibeis.init.sysres import *  # NOQA
        >>> # build test data
        >>> species = 'GZ'
        >>> # execute function
        >>> result = resolve_species(species)
        >>> # verify results
        >>> print(result)
        zebra_grevys
    """
    species_text = const.SPECIES_CODE_TO_TEXT.get(species_code.upper(), species_code).lower()
    assert species_text in const.VALID_SPECIES, 'cannot resolve species_text=%r' % (species_text,)
    return species_text


def grab_example_smart_xml_fpath():
    """ Gets smart example xml

    CommandLine:
        python -m ibeis.init.sysres --test-grab_example_smart_xml_fpath

    Example:
        >>> # DISABLE_DOCTEST
        >>> import ibeis
        >>> import utool as ut
        >>> import os
        >>> smart_xml_fpath = ibeis.sysres.grab_example_smart_xml_fpath()
        >>> os.system('gvim ' + smart_xml_fpath)
        >>> #ut.editfile(smart_xml_fpath)

    """
    import utool
    smart_xml_url = 'https://www.dropbox.com/s/g1mpjzp57wfnhk6/LWC_000261.xml'
    smart_sml_fpath = utool.grab_file_url(smart_xml_url, ensure=True, appname='ibeis')
    return smart_sml_fpath


if __name__ == '__main__':
    """
    CommandLine:
        python -m ibeis.init.sysres
        python -m ibeis.init.sysres --allexamples
        python -m ibeis.init.sysres --allexamples --noface --nosrc
    """
    import multiprocessing
    multiprocessing.freeze_support()  # for win32
    import utool as ut  # NOQA
    ut.doctest_funcs()