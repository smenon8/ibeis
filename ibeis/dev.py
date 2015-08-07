#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""
DEV SCRIPT

This is a hacky script meant to be run mostly automatically with the option of
interactions.

dev.py is supposed to be a developer non-gui interface into the IBEIS software.
dev.py runs experiments and serves as a scratchpad for new code and quick scripts

TODO:

    Test to find typical "good" descriptor scores.  Find nearest neighbors and
    noramlizers for each feature in a query image.  Based on ground truth and
    spatial verification mark feature matches as true or false.  Visualize the
    feature scores of good matches vs bad matches. Lowe shows the pdf of
    correct matches and the PDF for incorrect matches. We should also show the
    same thing.

Done:
    Cache nearest neighbors so different parameters later in the pipeline dont
    take freaking forever.

CommandLine:
    python dev.py --wshow -t query --db PZ_MTEST --qaid 110 --cfg score_method:nsum prescore_method:nsum
    python dev.py --wshow -t query --db PZ_MTEST --qaid 110
    python dev.py --wshow -t query --db PZ_MTEST --qaid 110 --cfg fg_on=True
    python dev.py --wshow -t query --db PZ_MTEST --qaid 110 --cfg
"""
# TODO: ADD COPYRIGHT TAG
from __future__ import absolute_import, division, print_function
import multiprocessing
# Dev
import sys
from ibeis._devscript import devcmd,  DEVCMD_FUNCTIONS, DEVPRECMD_FUNCTIONS
import utool as ut
from utool.util_six import get_funcname
import utool
#from ibeis.model.hots import smk
import plottool
import plottool as pt
import ibeis
if __name__ == '__main__':
    multiprocessing.freeze_support()
    ibeis._preload()
    from ibeis.all_imports import *  # NOQA
#utool.util_importer.dynamic_import(__name__, ('_devcmds_ibeis', None),
#                                   developing=True)
from ibeis._devcmds_ibeis import *  # NOQA
# IBEIS
from ibeis.init import main_helpers
from ibeis.other import dbinfo
from ibeis.experiments import experiment_configs
from ibeis.experiments import experiment_harness
from ibeis.experiments import results_all
from ibeis import params, constants
print, print_, printDBG, rrr, profile = utool.inject(__name__, '[dev]')


#------------------
# DEV DEVELOPMENT
#------------------
# This is where you write all of the functions that will become pristine
# and then go in _devcmds_ibeis.py


@devcmd('scores', 'score', 'namescore_roc')
def annotationmatch_scores(ibs, qaid_list, daid_list=None):
    """
    TODO: plot the difference between the top true score and the next best false score
    CommandLine:
        ib
        python dev.py -t scores --db PZ_MTEST --allgt -w --show
        python dev.py -t scores --db PZ_MTEST --allgt -w --show --cfg fg_on:True
        python dev.py -t scores --db PZ_MTEST --allgt -w --show --cfg codename='vsmany' fg_on:True
        python dev.py -t scores --db PZ_MTEST --allgt -w --show --cfg codename='vsmany' fg_on:True
        python dev.py -t scores --db GZ_ALL --allgt -w --show --cfg codename='vsmany' fg_on:True
        python dev.py -t scores --db PZ_Master0 --allgt -w --show --cfg codename='vsmany' fg_on:True
        python dev.py -t scores --db GZ_ALL --allgt -w --show

        python dev.py -t scores --db GZ_ALL --allgt -w --show --cfg codename='vsmany'
        python dev.py -t scores --db PZ_Master0 --allgt -w --show --cfg codename='vsmany'

        python dev.py -t scores --db PZ_Master0 --allgt --show
        python dev.py -t scores --db PZ_MTEST --allgt --show

        python dev.py -t scores --db PZ_Master0 --show --controlled
        python dev.py -t scores --db PZ_Master0 --show --controlled --cfg bar_l2_on:True lnbnn_on:False
        python dev.py -t scores --db PZ_Master0 --show --controlled --cfg fg_on:False
        python dev.py -t scores --db PZ_Master0 --show --controlled --cfg fg_on:False
    """
    import vtool as vt
    print('[dev] annotationmatch_scores')
    #allres = results_all.get_allres(ibs, qaid_list, daid_list)
    #ut.embed()
    #orgres = allres.allorg['rank0_true']
    qaid2_qres, qreq_ = results_all.get_qres_and_qreq_(ibs, qaid_list, daid_list)
    qres_list = ut.dict_take(qaid2_qres, qaid_list)

    def get_labeled_name_scores(ibs, qres_list):
        """
        TODO: rectify with score_normalization.get_ibeis_score_training_data
        This function does not return only the "good values".
        It is more for testing and validation than training.
        """
        tp_nscores = []
        tn_nscores = []
        for qx, qres in enumerate(qres_list):
            qaid = qres.get_qaid()
            if not qres.is_nsum():
                raise AssertionError('must be nsum')
            if not ibs.get_annot_has_groundtruth(qaid):
                continue
            qnid = ibs.get_annot_name_rowids(qres.get_qaid())
            # Get name scores for this query
            nscoretup = qres.get_nscoretup(ibs)
            (sorted_nids, sorted_nscores, sorted_aids, sorted_scores) = nscoretup
            # TODO: take into account viewpoint / quality difference
            sorted_nids = np.array(sorted_nids)
            is_positive  = sorted_nids == qnid
            is_negative = np.logical_and(~is_positive, sorted_nids > 0)
            if np.any(is_positive):
                # Take only the top true name score
                num_true = min(sum(is_positive), 1)
                gt_rank = np.nonzero(is_positive)[0][0:num_true]
                tp_nscores.extend(sorted_nscores[gt_rank])
            if np.any(is_negative):
                # Take the top few false name scores
                num_false = min(sum(is_negative), 3)
                #num_false = min(sum(is_negative), 100000)
                gf_rank = np.nonzero(is_negative)[0][0:num_false]
                tn_nscores.extend(sorted_nscores[gf_rank])
        tp_nscores = np.array(tp_nscores).astype(np.float64)
        tn_nscores = np.array(tn_nscores).astype(np.float64)
        return tp_nscores, tn_nscores

    tp_nscores, tn_nscores = get_labeled_name_scores(ibs, qres_list)

    #encoder = vt.ScoreNormalizer(target_tpr=.7)
    encoder = vt.ScoreNormalizer()
    name_scores, labels = encoder._to_xy(tp_nscores, tn_nscores)
    encoder.fit(name_scores, labels)
    encoder.visualize(figtitle='Learned Name Score Normalizer\n' + qreq_.get_cfgstr())
    #confusions = vt.ConfusionMetrics.from_tp_and_tn_scores(tp_nscores, tn_nscores)
    #confusions.draw_roc_curve()
    #ut.embed()

    #scorenorm.test_score_normalization(tp_nscores, tn_nscores)
    #scorenorm.plot_support(tn_nscores, tp_nscores, figtitle='sorted name scores', markersizes=[8, 4])

    #from ibeis.model.hots import score_normalization
    #tp_support, tn_support, tp_support_labels, tn_support_labels = score_normalization.get_ibeis_score_training_data(ibs, qaid_list, qres_list)
    #ut.embed()
    #x_data, y_data = results_all.get_stem_data(ibs, qaid2_qres)
    #pt.plots.plot_stems(x_data, y_data)

    #pt.present()
    #pt.show()
    #locals_ = viz_allres_annotation_scores(allres)
    locals_ = locals()
    return locals_


@devcmd('dists', 'dist', 'vecs_dist')
def vecs_dist(ibs, qaid_list, daid_list=None):
    """
    Plots the distances between matching descriptors
        with groundtruth (true/false) data

    True distances are spatially verified descriptor matches
    Top false distances distances are spatially verified descriptor matches

    SeeAlso:
        python -m ibeis.experiments.results_analyzer --test-get_orgres_desc_match_dists --db PZ_MTEST --distkeys=fs,lnbnn --show
        python -m ibeis.experiments.results_analyzer --test-get_orgres_desc_match_dists --db PZ_MTEST --distkeys=lnbnn --show
        python -m ibeis.experiments.results_analyzer --test-get_orgres_desc_match_dists --db PZ_MTEST --distkeys=fs,lnbnn,bar_L2_sift,cos_sift --show
        python -m ibeis.experiments.results_analyzer --test-get_orgres_desc_match_dists --db PZ_Master0 --distkeys=fs,lnbnn,bar_L2_sift,cos_sift --show --nosupport


    CommandLine:
        python dev.py -t vecs_dist --db NAUT_test --allgt -w --show
        python dev.py -t vecs_dist --db PZ_MTEST --allgt -w --show
        python dev.py -t vecs_dist --db PZ_Master0 --allgt -w --show
        python dev.py -t vecs_dist --db NNP_Maser3 --allgt -w --show
        python dev.py -t vecs_dist --db GZ_ALL --allgt -w --show
        python dev.py -t vecs_dist --db PZ_MTEST --allgt -w --show
    """
    print('[dev] vecs_dist')
    allres = results_all.get_allres(ibs, qaid_list)
    # Get the descriptor distances of true matches
    orgtype_list = ['top_false', 'true']
    #disttype = 'L2'
    disttype = 'lnbnn'
    # Get descriptor match distances
    orgres2_distmap = results_analyzer.get_orgres_desc_match_dists(allres, orgtype_list)
    results_analyzer.print_desc_distances_map(orgres2_distmap)
    #true_desc_dists  = orgres2_distmap['true']['L2']
    #false_desc_dists = orgres2_distmap['false']['L2']
    #scores_list = [false_desc_dists, true_desc_dists]
    dists_list = [orgres2_distmap[orgtype][disttype] for orgtype in orgtype_list]
    if False:
        dists_lbls = orgtype_list
        dists_markers = ['x--', 'o--']
        pt.plots.plot_sorted_scores(dists_list, dists_lbls, dists_markers)
    else:
        encoder = vt.ScoreNormalizer()
        tn_scores, tp_scores = dists_list
        name_scores, labels = encoder._to_xy(tp_scores, tn_scores)
        encoder.fit(name_scores, labels)
        encoder.visualize(figtitle='Descriptor Distance')

    pt.set_figtitle('Descriptor Sorted Distance d(x)\n' + allres.get_cfgstr())
    return locals()


@devcmd('tune', 'autotune')
def tune_flann(ibs, qaid_list, daid_list=None):
    r"""
    CommandLine:
        python dev.py -t tune --db PZ_MTEST
        python dev.py -t tune --db GZ_ALL
        python dev.py -t tune --db GIR_Tanya
        python dev.py -t tune --db PZ_Master0

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis._devscript import *  # NOQA
        >>> # build test data
        >>> # execute function
        >>> result = func_wrapper()
        >>> # verify results
        >>> print(result)
    """
    all_aids = ibs.get_valid_aids()
    vecs = np.vstack(ibs.get_annot_vecs(all_aids))
    print('Tunning flann for species={species}:'.format(species=ibs.get_database_species(all_aids)))
    tuned_params = vt.tune_flann(vecs,
                                 target_precision=.98,
                                 build_weight=0.05,
                                 memory_weight=0.00,
                                 sample_fraction=0.1)
    tuned_params

    #tuned_params2 = vt.tune_flann(vecs,
    #                              target_precision=.90,
    #                              build_weight=0.001,
    #                              memory_weight=0.00,
    #                              sample_fraction=0.5)
    #tuned_params2


@devcmd('incremental', 'inc')
def incremental_test(ibs, qaid_list, daid_list=None):
    """
    Adds / queries new images one at a time to a clean test database.
    Tests the complete system.

    Args:
        ibs       (list) : IBEISController object
        qaid_list (list) : list of annotation-ids to query

    CommandLine:
        python dev.py -t inc --db PZ_MTEST --qaid 1:30:3 --cmd

        python dev.py --db PZ_MTEST --allgt --cmd

        python dev.py --db PZ_MTEST --allgt -t inc

        python dev.py -t inc --db PZ_MTEST --qaid 1:30:3 --cmd

        python dev.py -t inc --db GZ_ALL --ninit 100 --noqcache

        python dev.py -t inc --db PZ_MTEST --noqcache --interactive-after 40
        python dev.py -t inc --db PZ_Master0 --noqcache --interactive-after 10000 --ninit 400

    Example:
        >>> from ibeis.all_imports import *  # NOQA
        >>> ibs = ibeis.opendb('PZ_MTEST')
        >>> qaid_list = ibs.get_valid_aids()
        >>> daid_list = None
    """
    from ibeis.model.hots import automated_matcher
    ibs1 = ibs
    num_initial = ut.get_argval('--ninit', type_=int, default=0)
    return automated_matcher.incremental_test(ibs1, num_initial)


def viz_allres_annotation_scores(allres):
    """
    chip vs chip scores

    CommandLine:
        python dev.py -t viz_allres_annotation_scores --db PZ_Master0 --allgt
    """
    # Get the descriptor distances of true matches
    #orgtype_list = ['false', 'true']
    #orgtype_list = ['top_false', 'top_true']
    orgtype_list = ['rank0_false', 'rank0_true']
    #markers_map = {'false': 'o', 'true': 'o-', 'top_true': 'o-', 'top_false': 'o'}
    markers_map = defaultdict(lambda: 'o')
    cmatch_scores_map = results_analyzer.get_orgres_annotationmatch_scores(allres, orgtype_list)
    results_analyzer.print_annotationmatch_scores_map(cmatch_scores_map)
    #true_cmatch_scores  = cmatch_scores_map['true']
    #false_cmatch_scores = cmatch_scores_map['false']
    scores_list = [cmatch_scores_map[orgtype] for orgtype in orgtype_list]
    scores_lbls = orgtype_list
    scores_markers = [markers_map[orgtype] for orgtype in orgtype_list]
    plottool.plots.plot_sorted_scores(scores_list, scores_lbls, scores_markers)
    pt.set_figtitle('Chip-vs-Chip Scores ' + allres.make_title())
    return locals()


@devcmd('upsize', 'upscale')
def up_dbsize_expt(ibs, qaid_list, daid_list=None):
    """
    Plots the scores/ranks of correct matches while varying the size of the
    database.

    Args:
        ibs       (list) : IBEISController object
        qaid_list (list) : list of annotation-ids to query

    CommandLine:
        python dev.py -t upsize --db PZ_MTEST --qaid 1:30:3 --cmd

    Example:
        >>> from ibeis.all_imports import *  # NOQA
        >>> #ibs = ibeis.opendb('PZ_FlankHack')
        >>> ibs = ibeis.opendb('PZ_MTEST')
        >>> qaid_list = ibs.get_valid_aids()
        >>> daid_list = None
    """
    print('updbsize_expt')
    upsizekw = dict(
        num_samp=utool.get_argval('--num-samples', int, 5),
        clamp_gt=utool.get_argval('--clamp-gt', int, 1),
        clamp_gf=utool.get_argval('--clamp-gf', int, 1),
        seed=143039
    )
    upsizetup = ibs.get_upsize_data(qaid_list, daid_list, **upsizekw)
    qaid_list, qaid_trues_list, qaid_false_samples_list, nTotal = upsizetup
    # Create a progress marking function
    progkw = dict(nTotal=nTotal, flushfreq=20, approx=False)
    mark_, end_ = utool.log_progress('[upscale] progress: ',  **progkw)
    count = 0
    # Set up output containers and run test iterations
    upscores_dict = utool.ddict(lambda: utool.ddict(list))
    input_iter = zip(qaid_list, qaid_trues_list, qaid_false_samples_list)
    # For each query annotation runs it as a query multiple times
    # each time it increases the number of false annotation in the database
    # so we can see how a score degrades as the number of false
    # database annotations increases
    for qaid, true_aids, false_aids_samples in input_iter:
        #print('qaid = %r' % (qaid,))
        #print('true_aids=%r' % (true_aids,))
        # For each true match and false sample
        for gt_aid, false_sample in utool.iprod(true_aids, false_aids_samples):
            #print('  gt_aid=%r' % (gt_aid,))
            #print('  false_sample=%r' % (false_sample,))
            mark_(count)
            count += 1
            # Execute query
            daids = false_sample + [gt_aid]
            qres = ibs._query_chips4([qaid], daids)[qaid]
            # Elicit information
            score = qres.get_gt_scores(gt_aids=[gt_aid])[0]
            # Append result
            upscores_dict[(qaid, gt_aid)]['dbsizes'].append(len(false_sample))
            upscores_dict[(qaid, gt_aid)]['score'].append(score)
    end_()

    if not utool.get_argflag('--noshow'):
        colors = pt.distinct_colors(len(upscores_dict))
        pt.figure(fnum=1, doclf=True, docla=True)
        for ix, ((qaid, gt_aid), upscores) in enumerate(upscores_dict.items()):
            xdata = upscores['dbsizes']
            ydata = upscores['score']
            pt.plt.plot(xdata, ydata, 'o-', color=colors[ix])
        figtitle = 'Effect of Database Size on Match Scores'
        figtitle += '\n' + ibs.get_dbname()
        figtitle += '\n' + ibs.cfg.query_cfg.get_cfgstr()
        pt.set_figtitle(figtitle, font='large')
        pt.set_xlabel('# Annotations in database')
        pt.set_ylabel('Groundtruth Match Scores (annot-vs-annot)')
        pt.dark_background()
        dumpkw = {
            'subdir'    : 'upsize',
            'quality'   : False,
            'overwrite' : True,
            'verbose'   : 0
        }
        figdir = ibs.get_fig_dir()
        ph.dump_figure(figdir, **dumpkw)

    #---------
    # Find highest
    if False:
        dbsample_index = 1
        line_index = 0

        highscore = 0
        highpair = None
        none_pairs = []
        pair_list  = []
        score_list = []
        for pair, dict_ in six.iteritems(upscores_dict):
            scores = dict_['score']
            if any([s is None for s in scores]):
                none_pairs.append(pair)
            if dbsample_index >= len(scores):
                continue
            score = scores[dbsample_index]
            if score is None:
                continue
            score_list.append(score)
            pair_list.append(pair)

        sorted_tups = sorted(list(zip(score_list, pair_list)))
        print(sorted_tups[0])
        print(sorted_tups[-1])

        qaid, gt_aid = sorted_tups[line_index][1]
        print('qaid = %r' % qaid)
        print('gt_aid = %r' % gt_aid)
        index = qaid_list.index(qaid)
        print(index)
        false_aids_samples = qaid_false_samples_list[index]
        false_sample = false_aids_samples[dbsample_index]
        print(false_sample)
        daids = false_sample + [gt_aid]
        qres = ibs._query_chips4([qaid], daids)[qaid]
        #for score in scores:
        #    if score is None:
        #        continue
        #    if score > highscore:
        #        highpair = pair
        #        highscore = score
        #print(scores)

    # TODO: Should be separate function. Previous code should be intergrated
    # into the experiment_harness
    locals_ = locals()
    return locals_  # return in dict format for execstr_dict


@devcmd('vsone_gt')
def vsone_gt(ibs, qaid_list, daid_list=None):
    """
    dev.py --db PZ_MTEST --allgt --cmd
    """
    cfgdict = dict(fg_on=True)
    allres = results_all.get_allres(ibs, qaid_list, daid_list, cfgdict)
    #orgtype_list = ['top_false', 'top_true']
    org_top_false = allres.get_orgtype('rank0_false')
    top_false_aid_pairs = zip(org_top_false.qaids, org_top_false.aids)
    gtaids_list = ibs.get_annot_groundtruth(qaid_list, daid_list=daid_list)
    # Add groundtruth pairs to query
    qaid2_vsoneaids_ = dict(zip(qaid_list, gtaids_list))
    qaid2_vsoneaids = ut.ddict(list)
    # Add problem cases
    for qaid, daid in top_false_aid_pairs:
        qaid2_vsoneaids[qaid].append(daid)
        qaid2_vsoneaids[qaid].extend(qaid2_vsoneaids_.get(qaid, []))
    cfgdict = dict(codename='vsone')
    qaid2_vsoneqres = {}
    for qaid, vsoneaids in six.iteritems(qaid2_vsoneaids):
        qres = ibs._query_chips4([qaid], vsoneaids, cfgdict=cfgdict)[qaid]
        qaid2_vsoneqres[qaid] = qres
    vsone_allres = results_all.init_allres(ibs, qaid2_vsoneqres)
    viz_allres_annotation_scores(vsone_allres)
    #cmatch_scores_map = results_analyzer.get_orgres_annotationmatch_scores(allres, orgtype_list)


@devcmd('inspect')
def inspect_matches(ibs, qaid_list, daid_list):
    print('<inspect_matches>')
    from ibeis.gui import inspect_gui
    return inspect_gui.test_inspect_matches(ibs, qaid_list, daid_list)


@devcmd('gv')
def gvcomp(ibs, qaid_list, daid_list):
    """
    GV = With gravity vector
    RI = With rotation invariance
    """
    print('[dev] gvcomp')
    assert isinstance(ibs, IBEISControl.IBEISController), 'bad input'  # let jedi know whats up
    def testcomp(ibs, qaid_list):
        allres = results_all.get_allres(ibs, qaid_list)
        for qaid in qaid_list:
            qres = allres.get_qres(qaid)
            qres.ishow_top(ibs, annot_mode=2, in_image=True, figtitle='Qaid=%r %s' % (qres.qaid, qres.cfgstr))
        return allres
    ibs_GV = ibs
    ibs_RI = ibs.clone_handle(nogravity_hack=True)
    #utool.embed()

    allres_GV = testcomp(ibs_GV, qaid_list)
    allres_RI = testcomp(ibs_RI, qaid_list)
    return locals()


def get_ibslist(ibs):
    print('[dev] get_ibslist')
    ibs_GV  = ibs
    ibs_RI  = ibs.clone_handle(nogravity_hack=True)
    ibs_RIW = ibs.clone_handle(nogravity_hack=True, gravity_weighting=True)
    ibs_list = [ibs_GV, ibs_RI, ibs_RIW]
    return ibs_list


@devcmd('gv_scores')
def compgrav_annotationmatch_scores(ibs, qaid_list, daid_list):
    print('[dev] compgrav_annotationmatch_scores')
    ibs_list = get_ibslist(ibs)
    for ibs_ in ibs_list:
        annotationmatch_scores(ibs_, qaid_list)

#--------------------
# RUN DEV EXPERIMENTS
#--------------------


def run_devprecmds():
    """
    Looks for pre-tests specified with the -t flag and runs them
    """
    input_precmd_list = params.args.tests[:]
    valid_precmd_list = []
    def intest(*args, **kwargs):
        for precmd_name in args:
            valid_precmd_list.append(precmd_name)
            ret = precmd_name in input_precmd_list
            ret2 = precmd_name in params.unknown  # Let unparsed args count towards tests
            if ret or ret2:
                if ret:
                    input_precmd_list.remove(precmd_name)
                else:
                    ret = ret2
                print('+===================')
                print('| running precmd = %s' % (args,))
                return ret
        return False

    # Implicit (decorated) test functions
    for (func_aliases, func) in DEVPRECMD_FUNCTIONS:
        if intest(*func_aliases):
            with utool.Indenter('[dev.' + get_funcname(func) + ']'):
                func()
                print('Exiting after first precommand')
            sys.exit(1)


#@utool.indent_func('[dev]')
def run_devcmds(ibs, qaid_list, daid_list):
    """
    This function runs tests passed in with the -t flag
    """
    print('\n')
    print('[dev] run_devcmds')
    print('==========================')
    print('RUN EXPERIMENTS %s' % ibs.get_dbname())
    print('==========================')
    input_test_list = params.args.tests[:]
    print('input_test_list = %r' % (input_test_list,))
    # fnum = 1

    valid_test_list = []  # build list for printing in case of failure
    valid_test_helpstr_list = []  # for printing

    def mark_test_handled(testname):
        input_test_list.remove(testname)

    def intest(*args, **kwargs):
        helpstr = kwargs.get('help', '')
        valid_test_helpstr_list.append('   -t ' + ', '.join(args) + helpstr)
        for testname in args:
            valid_test_list.append(testname)
            ret = testname in input_test_list
            ret2 = testname in params.unknown  # Let unparsed args count towards tests
            if ret or ret2:
                if ret:
                    mark_test_handled(testname)
                else:
                    ret = ret2
                print('+===================')
                print('| running testname = %s' % (args,))
                return ret
        return False

    valid_test_helpstr_list.append('    # --- Simple Tests ---')

    # Explicit (simple) test functions
    if intest('export'):
        export(ibs)
    if intest('dbinfo'):
        dbinfo.get_dbinfo(ibs)
    if intest('headers', 'schema'):
        ibs.db.print_schema()
    if intest('info'):
        print(ibs.get_infostr())
    if intest('printcfg'):
        printcfg(ibs)
    if intest('tables'):
        ibs.print_tables()
    if intest('imgtbl'):
        ibs.print_image_table()

    valid_test_helpstr_list.append('    # --- Decor Tests ---')

    locals_ = locals()

    # Implicit (decorated) test functions
    for (func_aliases, func) in DEVCMD_FUNCTIONS:
        if intest(*func_aliases):
            funcname = get_funcname(func)
            with utool.Indenter('[dev.' + funcname + ']'):
                with utool.Timer(funcname):
                    #print('[dev] qid_list=%r' % (qaid_list,))
                    # FIXME: , daid_list
                    ret = func(ibs, qaid_list, daid_list)
                    # Add variables returned by the function to the
                    # "local scope" (the exec scop)
                    if hasattr(ret, 'items'):
                        for key, val in ret.items():
                            if utool.is_valid_varname(key):
                                locals_[key] = val

    valid_test_helpstr_list.append('    # --- Config Tests ---')

    # ------
    # RUNS EXPERIMENT HARNESS OVER VALID TESTNAMES SPECIFIED WITH -t
    # ------

    # Config driven test functions
    # Allow any testcfg to be in tests like: vsone_1 or vsmany_3
    test_cfg_name_list = []
    for test_cfg_name in experiment_configs.TEST_NAMES:
        if intest(test_cfg_name):
            test_cfg_name_list.append(test_cfg_name)
    # Hack to allow for very customized harness tests
    for testname in input_test_list[:]:
        if testname.startswith('custom:'):
            test_cfg_name_list.append(testname)
            mark_test_handled(testname)
    if len(test_cfg_name_list):
        fnum = pt.next_fnum()
        # Run Experiments
        experiment_harness.test_configurations(ibs, qaid_list, daid_list, test_cfg_name_list)

    valid_test_helpstr_list.append('    # --- Help ---')

    if intest('help'):
        print('valid tests are:')
        print('\n'.join(valid_test_helpstr_list))
        return locals_

    if len(input_test_list) > 0:
        print('valid tests are: \n')
        print('\n'.join(valid_test_list))
        raise Exception('Unknown tests: %r ' % input_test_list)
    return locals_


#-------------------
# CUSTOM DEV FUNCS
#-------------------


#------------------
# DEV MAIN
#------------------

def dev_snippets(main_locals):
    """ Common variables for convineince when interacting with IPython """
    print('[dev] dev_snippets')
    species = constants.Species.ZEB_GREVY
    quick = True
    fnum = 1
    # Get reference to IBEIS Controller
    ibs = main_locals['ibs']
    if 'back' in main_locals:
        # Get reference to GUI Backend
        back = main_locals['back']
        if back is not None:
            # Get reference to GUI Frontend
            front = getattr(back, 'front', None)
            ibswgt = front
            view = ibswgt.views['images']
            model = ibswgt.models['names_tree']
            selection_model = view.selectionModel()
    if ibs is not None:
        #ibs.dump_tables()
        aid_list = ibs.get_valid_aids()
        gid_list = ibs.get_valid_gids()
        #nid_list = ibs.get_valid_nids()
        #valid_nid_list   = ibs.get_annot_name_rowids(aid_list)
        #valid_aid_names  = ibs.get_annot_names(aid_list)
        #valid_aid_gtrues = ibs.get_annot_groundtruth(aid_list)
    return locals()


def get_sortbystr(str_list, key_list, strlbl=None, keylbl=None):
    sortx = key_list.argsort()
    ndigits = max(len(str(key_list.max())), 0 if keylbl is None else len(keylbl))
    keyfmt  = '%' + str(ndigits) + 'd'
    if keylbl is not None:
        header = keylbl + ' --- ' + strlbl
    else:
        header = None

    sorted_strs = ([(keyfmt % key + ' --- ' + str_) for str_, key in zip(str_list[sortx], key_list[sortx])])
    def boxjoin(list_, header=None):
        topline = '+----------'
        botline = 'L__________'
        boxlines = []
        boxlines.append(topline + '\n')
        if header is not None:
            boxlines.append(header + '\n')
            boxlines.append(topline)

        body = utool.indentjoin(list_, '\n | ')
        boxlines.append(body + '\n ')
        boxlines.append(botline + '\n')
        return ''.join(boxlines)
    return boxjoin(sorted_strs, header)


@devcmd('test_feats')
def test_feats(ibs, qaid_list, daid_list=None):
    """
    test_feats shows features using several different parameters

    Args:
        ibs (IBEISController):
        qaid_list (int): query annotation id

    CommandLine:
        python dev.py -t test_feats --db PZ_MTEST --all --qindex 0 --show -w

    Example:
        >>> import ibeis
        >>> ibs = ibeis.opendb('testdb1')
        >>> qaid_list = [1]
    """
    from ibeis import viz
    from ibeis.experiments import experiment_configs
    import utool as ut

    NUM_PASSES = 1 if not utool.get_argflag('--show') else 2
    varyparams_list = [experiment_configs.featparams]

    def test_featcfg_combo(ibs, aid, alldictcomb, count, nKpts_list, cfgstr_list):
        for dict_ in ut.progiter(alldictcomb, lbl='FeatCFG Combo: '):
            # Set ibs parameters to the current config
            for key_, val_ in six.iteritems(dict_):
                ibs.cfg.feat_cfg[key_] = val_
            cfgstr_ = ibs.cfg.feat_cfg.get_cfgstr()
            if count == 0:
                # On first run just record info
                kpts = ibs.get_annot_kpts(aid)
                nKpts_list.append(len(kpts))
                cfgstr_list.append(cfgstr_)
            if count == 1:
                kpts = ibs.get_annot_kpts(aid)
                # If second run happens display info
                cfgpackstr = utool.packstr(cfgstr_, textwidth=80,
                                              breakchars=',', newline_prefix='',
                                              break_words=False, wordsep=',')
                title_suffix = (' len(kpts) = %r \n' % len(kpts)) + cfgpackstr
                viz.show_chip(ibs, aid, fnum=pt.next_fnum(),
                              title_suffix=title_suffix, darken=.8,
                              ell_linewidth=2, ell_alpha=.6)

    alldictcomb = utool.flatten(map(utool.all_dict_combinations, varyparams_list))
    for count in range(NUM_PASSES):
        nKpts_list = []
        cfgstr_list = []
        for aid in qaid_list:
            test_featcfg_combo(ibs, aid, alldictcomb, count, nKpts_list, cfgstr_list)
            #for dict_ in alldictcomb:
        if count == 0:
            nKpts_list = np.array(nKpts_list)
            cfgstr_list = np.array(cfgstr_list)
            print(get_sortbystr(cfgstr_list, nKpts_list, 'cfg', 'nKpts'))


def devfunc(ibs, qaid_list):
    """ Function for developing something """
    print('[dev] devfunc')
    import ibeis  # NOQA
    from ibeis.model import Config  # NOQA
    #from ibeis.model.Config import *  # NOQA
    feat_cfg = Config.FeatureConfig()
    #feat_cfg.printme3()
    print('\ncfgstr..')
    print(feat_cfg.get_cfgstr())
    print(utool.dict_str(feat_cfg.get_hesaff_params()))
    #allres = results_all.get_allres(ibs, qaid_list)
    from ibeis import viz
    aid = 1
    ibs.cfg.feat_cfg.threshold = 16.0 / 3.0
    kpts = ibs.get_annot_kpts(aid)
    print('len(kpts) = %r' % len(kpts))
    from ibeis.experiments import experiment_configs
    #varyparams_list = [
    #    #{
    #    #    'threshold': [16.0 / 3.0, 32.0 / 3.0],  # 8.0  / 3.0
    #    #    'numberOfScales': [3, 2, 1],
    #    #    'maxIterations': [16, 32],
    #    #    'convergenceThreshold': [.05, .1],
    #    #    'initialSigma': [1.6, 1.2],
    #    #},
    #    {
    #        #'threshold': [16.0 / 3.0, 32.0 / 3.0],  # 8.0  / 3.0
    #        'numberOfScales': [1],
    #        #'maxIterations': [16, 32],
    #        #'convergenceThreshold': [.05, .1],
    #        #'initialSigma': [6.0, 3.0, 2.0, 1.6, 1.2, 1.1],
    #        'initialSigma': [3.2, 1.6, 0.8],
    #        'edgeEigenValueRatio': [10, 5, 3],
    #    },
    #]
    varyparams_list = [experiment_configs.featparams]

    # low threshold = more keypoints
    # low initialSigma = more keypoints

    nKpts_list = []
    cfgstr_list = []

    alldictcomb = utool.flatten([utool.util_dict.all_dict_combinations(varyparams) for varyparams in featparams_list])
    NUM_PASSES = 1 if not utool.get_argflag('--show') else 2
    for count in range(NUM_PASSES):
        for aid in qaid_list:
            #for dict_ in utool.progiter(alldictcomb, lbl='feature param comb: ', total=len(alldictcomb)):
            for dict_ in alldictcomb:
                for key_, val_ in six.iteritems(dict_):
                    ibs.cfg.feat_cfg[key_] = val_
                cfgstr_ = ibs.cfg.feat_cfg.get_cfgstr()
                cfgstr = utool.packstr(cfgstr_, textwidth=80,
                                        breakchars=',', newline_prefix='', break_words=False, wordsep=',')
                if count == 0:
                    kpts = ibs.get_annot_kpts(aid)
                    #print('___________')
                    #print('len(kpts) = %r' % len(kpts))
                    #print(cfgstr)
                    nKpts_list.append(len(kpts))
                    cfgstr_list.append(cfgstr_)
                if count == 1:
                    title_suffix = (' len(kpts) = %r \n' % len(kpts)) + cfgstr
                    viz.show_chip(ibs, aid, fnum=pt.next_fnum(),
                                   title_suffix=title_suffix, darken=.4,
                                   ell_linewidth=2, ell_alpha=.8)

        if count == 0:
            nKpts_list = np.array(nKpts_list)
            cfgstr_list = np.array(cfgstr_list)
            print(get_sortbystr(cfgstr_list, nKpts_list, 'cfg', 'nKpts'))
    pt.present()
    locals_ = locals()
    #locals_.update(annotationmatch_scores(ibs, qaid_list))
    return locals_


def run_dev(main_locals):
    """
    main developer command

    Args:
        main_locals (dict): locals returned by ibeis.main

    CommandLine:
        python dev.py --db PZ_Master0 --controlled --print-rankhist
    """
    print('[dev] --- RUN DEV ---')
    # Get reference to controller
    ibs  = main_locals['ibs']
    if ibs is not None:
        # Get aids marked as test cases
        qaid_list = main_helpers.get_test_qaids(ibs, default_qaids=[1])
        daid_list = main_helpers.get_test_daids(ibs, default_daids='all', qaid_list=qaid_list)
        print('[run_def] Test Annotations:')
        #print('[run_dev] * qaid_list = %s' % ut.packstr(qaid_list, 80, nlprefix='[run_dev]     '))
        verbose_info = True
        ibeis.other.dbinfo.print_qd_info(ibs, qaid_list, daid_list, verbose=verbose_info)
        # Warn on no test cases
        try:
            assert len(qaid_list) > 0, 'assert!'
            assert len(daid_list) > 0, 'daid_list!'
        except AssertionError as ex:
            utool.printex(ex, 'len(qaid_list) = 0', iswarning=True)
            utool.printex(ex, 'or len(daid_list) = 0', iswarning=True)
            #qaid_list = ibs.get_valid_aids()[0]

        if len(qaid_list) > 0 or True:
            # Run the dev experiments
            expt_locals = run_devcmds(ibs, qaid_list, daid_list)
            # Add experiment locals to local namespace
            execstr_locals = utool.execstr_dict(expt_locals, 'expt_locals')
            exec(execstr_locals)
        if ut.get_argflag('--devmode'):
            # Execute the dev-func and add to local namespace
            devfunc_locals = devfunc(ibs, qaid_list)
            exec(utool.execstr_dict(devfunc_locals, 'devfunc_locals'))

    return locals()


#-------------
# EXAMPLE TEXT
#-------------

EXAMPLE_TEXT = '''
### DOWNLOAD A TEST DATABASE (IF REQUIRED) ###
python dev.py --t mtest
python dev.py --t nauts
./resetdbs.sh  # FIXME
python ibeis/dbio/ingest_database.py  <- see module for usage

### LIST AVAIABLE DATABASES ###
python dev.py -t list_dbs

### CHOOSE A DATABASE ###
python dev.py --db PZ_Master0 --setdb
python dev.py --db GZ_ALL --setdb
python dev.py --db PZ_MTEST --setdb
python dev.py --db NAUT_test --setdb
python dev.py --db testdb1 --setdb
python dev.py --db seals2 --setdb

### DATABASE INFORMATION ###
python dev.py -t dbinfo

### EXPERIMENTS ###
python dev.py --allgt -t best
python dev.py --allgt -t vsone
python dev.py --allgt -t vsmany
python dev.py --allgt -t nsum

### COMPARE TWO CONFIGS ###
python dev.py --allgt -t nsum vsmany vsone
python dev.py --allgt -t nsum vsmany
python dev.py --allgt -t nsum vsmany vsone smk

### VIZ A SET OF MATCHES ###
python dev.py --db PZ_MTEST -t query --qaid 72 110 -w
#python dev.py --allgt -t vsone vsmany
#python dev.py --allgt -t vsone --vz --vh

### RUN A SMALL AMOUNT OF VSONE TESTS ###
python dev.py --allgt -t  vsone --qindex 0:1 --vz --vh --vf --noqcache
python dev.py --allgt --qindex 0:20 --

### DUMP ANALYSIS FIGURES TO DISK ###
python dev.py --allgt -t best --vf --vz --fig-dname query_analysis_easy
python dev.py --allgt -t best --vf --vh --fig-dname query_analysis_hard
python dev.py --allgt -t best --vf --va --fig-dname query_analysis_all

python dev.py --db PZ_MTEST --set-aids-as-hard 27 28 44 49 50 51 53 54 66 72 89 97 110
python dev.py --hard -t best vsone nsum
>>>
'''

#L______________


def devmain():
    """
    The Developer Script
        A command line interface to almost everything

        -w     # wait / show the gui / figures are visible
        --cmd  # ipython shell to play with variables
        -t     # run list of tests

        Examples:
    """

    helpstr = ut.codeblock(
        '''
        Dev is meant to be run as an interactive script.

        The dev.py script runs any test you regiter with @devcmd in any combination
        of configurations specified by a Config object.

        Dev caches information in order to get quicker results.  # FIXME: Provide quicker results  # FIXME: len(line)
        ''')

    INTRO_TITLE = 'The dev.py Script'
    INTRO_TEXT = ''.join((ut.bubbletext(INTRO_TITLE, font='cybermedium'), helpstr))

    INTRO_STR = ut.msgblock('dev.py Intro',  INTRO_TEXT)

    EXAMPLE_STR = ut.msgblock('dev.py Examples', ut.codeblock(EXAMPLE_TEXT))

    print(INTRO_STR)
    if ut.get_argflag(('--help', '--verbose')):
        print(EXAMPLE_STR)

    CMD   = ut.get_argflag('--cmd')
    NOGUI = not ut.get_argflag('--gui')

    if len(sys.argv) == 1:
        print('Run dev.py with arguments!')
        sys.exit(1)

    # Run Precommands
    run_devprecmds()

    #
    #
    # Run IBEIS Main, create controller, and possibly gui
    print('++dev')
    main_locals = ibeis.main(gui=ut.get_argflag('--gui'))
    #utool.set_process_title('IBEIS_dev')

    #
    #
    # Load snippet variables
    SNIPPITS = True and CMD
    if SNIPPITS:
        snippet_locals = dev_snippets(main_locals)
        snippet_execstr = utool.execstr_dict(snippet_locals, 'snippet_locals')
        exec(snippet_execstr)

    #
    #
    # Development code
    RUN_DEV = True  # RUN_DEV = '__IPYTHON__' in vars()
    if RUN_DEV:
        dev_locals = run_dev(main_locals)
        dev_execstr = utool.execstr_dict(dev_locals, 'dev_locals')
        exec(dev_execstr)

    command = ut.get_argval('--eval', type_=str, default=None)
    if command is not None:
        result = eval(command, globals(), locals())
        print('result = %r' % (result,))
        #ibs.search_annot_notes('360')

    #
    #
    # Main Loop (IPython interaction, or some exec loop)
    #if '--nopresent' not in sys.argv or '--noshow' in sys.argv:
    ut.show_if_requested()
    if ut.get_argflag(('--show', '--wshow')):
        pt.present()
    main_execstr = ibeis.main_loop(main_locals, ipy=(NOGUI or CMD))
    exec(main_execstr)

    #
    #
    # Memory profile
    if ut.get_argflag('--memprof'):
        utool.print_resource_usage()
        utool.memory_profile()

    print('exiting dev')


if __name__ == '__main__':
    multiprocessing.freeze_support()  # for win32
    devmain()


r"""
CurrentExperiments:
    # Full best settings run
    ./dev.py -t custom --db PZ_Master0 --allgt --species=zebra_plains
    # Full best settings run without spatial verification
    ./dev.py -t custom:sv_on=False --db PZ_Master0 --allgt --species=zebra_plains

    ./dev.py -t custom --db PZ_Master0 --allgt --species=zebra_plains --hs

    # Check to see if new spatial verification helps
    ./dev.py -t custom:full_homog_checks=False custom:full_homog_checks=True --db PZ_Master0 --allgt --species=zebra_plains
    # Yay it does


    # Look for how many false negatives are in the bottom batch
    ./dev.py -t custom --db PZ_MTEST --species=zebra_plains --print-rankhist
    ./dev.py -t custom --db PZ_MTEST --controlled --print-rankhist
    ./dev.py -t custom --db PZ_Master0 --controlled --print-rankhist

    ./dev.py -t \
            custom \
            custom:rotation_invariance=True,affine_invariance=False \
            custom:rotation_invariance=True,augment_queryside_hack=True \
            --db PZ_Master0 --controlled --print-rankhist  --print-bestcfg

    ./dev.py -t \
            custom:rotation_invariance=True,affine_invariance=False \
            custom:rotation_invariance=True,augment_queryside_hack=True \
            --db NNP_Master3 --controlled --print-rankhist  --print-bestcfg


ElephantEarExperiments
    --show --vh
    ./dev.py -t custom:affine_invariance=True --db Elephants_drop1_ears --allgt --print-rankhist
    ./dev.py -t custom:affine_invariance=False --db Elephants_drop1_ears --allgt --print-rankhist
    ./dev.py -t custom:affine_invariance=False,histeq=True --db Elephants_drop1_ears --allgt --print-rankhist
    ./dev.py -t custom:affine_invariance=False,adapteq=True --db Elephants_drop1_ears --allgt --print-rankhist

    ./dev.py -t custom:affine_invariance=False,fg_on=False --db Elephants_drop1_ears --allgt
    ./dev.py -t custom:affine_invariance=False,histeq=True,fg_on=False --db Elephants_drop1_ears --allgt
    ./dev.py -t custom:affine_invariance=False,adapteq=True,fg_on=False --db Elephants_drop1_ears --allgt

    ./dev.py -t elph --db Elephants_drop1_ears --allgt


Sift vs Siam Experiments
    ./dev.py -t custom:feat_type=hesaff+siam128,algorithm=linear custom:feat_type=hesaff+sift --db testdb1 --allgt
    ./dev.py -t custom:feat_type=hesaff+siam128,algorithm=linear custom:feat_type=hesaff+sift --db PZ_MTEST --allgt
    ./dev.py -t custom:feat_type=hesaff+siam128,lnbnn_on=False,fg_on=False,bar_l2_on=True custom:feat_type=hesaff+sift,fg_on=False --db PZ_MTEST --allgt

    ./dev.py -t custom:feat_type=hesaff+siam128 custom:feat_type=hesaff+sift --db PZ_MTEST --allgt --print-rankhist
    ./dev.py -t custom:feat_type=hesaff+siam128 --db PZ_MTEST --allgt --print-rankhist
    ./dev.py -t custom:feat_type=hesaff+sift --db PZ_MTEST --allgt --print-rankhist

    ./dev.py -t custom:feat_type=hesaff+siam128 custom:feat_type=hesaff+sift --db PZ_Master0 --allgt

    ./dev.py -t custom:feat_type=hesaff+siam128 --db testdb1 --allgt



Without SV:
agg rank histogram = {
    (0, 1): 2276,
    (1, 5): 126,
    (5, 50): 99,
    (50, 8624): 108,
    (8624, 8625): 28,
}
With SV:
agg rank histogram = {
    (0, 1): 2300,
    (1, 5): 106,
    (5, 50): 16,
    (50, 8624): 0,
    (8624, 8625): 215,
}

Guesses:
    0 2 2 2 4 4 4 4 0 0
    0 0 4 2 2 4 4 4 2 2
    2 4 4 4 1 1 1 2 2 2
    0 0 1 1 1 2 0 0 1
"""
