"""
TODO: Rename to ibeis/init/commands.py
"""
from __future__ import absolute_import, division, print_function
import utool as ut
import sys
from ibeis import constants
from ibeis import params
from ibeis import ibsfuncs
from ibeis.init import sysres
from os.path import join
print, print_, printDBG, rrr, profile = ut.inject(__name__, '[commands]')


def vdq(dbdir):
    """view directory and quit"""
    _ibsdb = constants.PATH_NAMES._ibsdb
    ut.util_cplat.view_directory(join(dbdir, _ibsdb))
    sys.exit(1)


def vdd(ibs):
    " view data dir "
    ut.util_cplat.view_directory(ibs.dbdir)


def vwd():
    """ view work dir """
    ut.util_cplat.view_directory(sysres.get_workdir())


def preload_convert_hsdb(dbdir):
    """ Convert the database before loading (A bit hacky) """
    from ibeis.dbio import ingest_hsdb
    ingest_hsdb.convert_hsdb_to_ibeis(dbdir, force_delete=params.args.force_delete)


def preload_commands(dbdir, **kwargs):
    """ Preload commands work with command line arguments and global caches """
    #print('[main_cmd] preload_commands')
    if params.args.dump_argv:
        print(ut.dict_str(vars(params.args), sorted_=False))
    if params.args.dump_global_cache:
        ut.global_cache_dump()  # debug command, dumps to stdout
    if params.args.set_workdir is not None:
        sysres.set_workdir(params.args.set_workdir)
    if params.args.get_workdir:
        print(' Current work dir = %s' % sysres.get_workdir())
    if params.args.logdir is not None:
        sysres.set_logdir(params.args.logdir)
    if params.args.get_logdir:
        print(' Current log dir = %s' % (sysres.get_logdir(),))
    if params.args.view_logdir:
        ut.view_directory(sysres.get_logdir())
    if ut.get_argflag('--vwd'):
        vwd()
    if ut.get_argflag('--vdq'):
        print('got arg --vdq')
        vdq(dbdir)
    if kwargs.get('delete_ibsdir', False):
        ibsfuncs.delete_ibeis_database(dbdir)
    if params.args.convert:
        preload_convert_hsdb(dbdir)
    if params.args.preload_exit:
        print('[main_cmd] preload exit')
        sys.exit(1)


def postload_commands(ibs, back):
    """ Postload commands deal with a specific ibeis database """
    if ut.NOT_QUIET:
        print('\n[main_cmd] postload_commands')
    if params.args.view_database_directory:
        print('got arg --vdd')
        vdd(ibs)
    if params.args.set_default_dbdir:
        sysres.set_default_dbdir(ibs.get_dbdir())
    if params.args.update_query_cfg is not None:
        # Set query parameters from command line using the --cfg flag
        cfgdict = ut.parse_cfgstr_list(params.args.update_query_cfg)
        print('Custom cfgdict specified')
        print(ut.dict_str(cfgdict))
        ibs.update_query_cfg(**cfgdict)
        #print(ibs.cfg.query_cfg.get_cfgstr())
    if params.args.edit_notes:
        ut.editfile(ibs.get_dbnotes_fpath(ensure=True))
    if params.args.delete_cache:
        ibs.delete_cache()
    if params.args.delete_cache_complete:
        ibs.delete_cache(delete_chips=True, delete_encounters=True)
    if params.args.delete_query_cache:
        ibs.delete_qres_cache()
    if params.args.set_notes is not None:
        ibs.set_dbnotes(params.args.set_notes)
    if params.args.set_aids_as_hard is not None:
        aid_list = params.args.set_aids_as_hard
        ibs.set_annot_is_hard(aid_list, [True] * len(aid_list))
    if params.args.set_all_species is not None:
        ibs._overwrite_all_annot_species_to(params.args.set_all_species)
    if params.args.dump_schema:
        ibs.db.print_schema()

    # Send commands to GUIBack
    if params.args.select_aid is not None:
        if back is not None:
            try:
                ibsfuncs.assert_valid_aids(ibs, (params.args.select_aid,))
            except AssertionError:
                print('Valid RIDs are: %r' % (ibs.get_valid_aids(),))
                raise
            back.select_aid(params.args.select_aid)
    if params.args.query_aid is not None:
        import ibeis.constants as const
        qaid_list = params.args.query_aid
        # fix stride case
        if len(qaid_list) == 1 and isinstance(qaid_list[0], tuple):
            qaid_list = list(qaid_list[0])
        daids_mode = ut.get_argval('--daids-mode', type_=str, default=const.VS_EXEMPLARS_KEY)
        back.compute_queries(qaid_list=qaid_list,
                             daids_mode=daids_mode, ranks_lt=10)
    if params.args.select_gid is not None:
        back.select_gid(params.args.select_gid)
    if params.args.select_nid is not None:
        back.select_nid(params.args.select_nid)

    select_eid = ut.get_argval(('--select-eid', '--eid',), int, None)
    if select_eid is not None:
        print('\n+ --- CMD SELECT EID=%r ---' % (select_eid,))
        # Whoa: this doesnt work. weird.
        #back.select_eid(select_eid)
        # This might be the root of gui problems
        #back.front._change_enc(select_eid)
        back.front.select_encounter_tab(select_eid)
        print('L ___ CMD SELECT EID=%r ___\n' % (select_eid,))

    if ut.get_argflag('--inc-query'):
        back.incremental_query()

    #screengrab_fpath = ut.get_argval('--screengrab')
    #if screengrab_fpath:
    #    from guitool.__PYQT__.QtGui import QPixmap
    #    from PyQt4.QtTest import QTest
    #    from PyQt4.QtCore import Qt
    #    fpath = ut.truepath(screengrab_fpath)
    #    import guitool
    #    #ut.embed()
    #    timer2 = guitool.__PYQT__.QtCore.QTimer()
    #    done = [1000]
    #    def delayed_screenshot_func():
    #        if done[0] == 500:
    #            #back.mainwin.menubar.triggered.emit(back.mainwin.menuFile)
    #            print('Mouseclick')
    #            QTest.mouseClick(back.mainwin.menuFile, Qt.LeftButton)
    #            # This works
    #            #QTest.mouseClick(back.front.import_button, Qt.LeftButton)
    #        if done[0] == 1:
    #            timer2.stop()
    #            print('screengrab to %r' % (fpath,))
    #            screenimg = QPixmap.grabWindow(back.mainwin.winId())
    #            screenimg.save(fpath, 'jpg')
    #            ut.startfile(fpath)
    #            print('lub dub2')
    #        done[0] -= 1
    #        return None
    #    CLICK_FILE_MENU = True
    #    if CLICK_FILE_MENU:
    #        #ut.embed()
    #        #QTest::keyClick(menu, Qt::Key_Down)
    #        pass
    #    timer2.delayed_screenshot_func = delayed_screenshot_func
    #    timer2.timeout.connect(timer2.delayed_screenshot_func)
    #    timer2.start(1)
    #    back.mainwin.timer2 = timer2
    #    guitool.activate_qwindow(back.mainwin)
    #    #QPixmap.grabWindow(back.mainwin.winId()).save(fpath, 'jpg')
    #    #ut.startfile(fpath)
    #    #ut.embed()
    #    pass
    if params.args.postload_exit:
        print('[main_cmd] postload exit')
        sys.exit(1)