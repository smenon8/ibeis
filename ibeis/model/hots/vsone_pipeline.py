"""
special pipeline for vsone specific functions

Current Issues:
    * getting feature distinctiveness is too slow, we can either try a different
      model, or precompute feature distinctiveness.

      - we can reduce the size of the vsone shortlist

TODOLIST:
    * Precompute distinctivness
    * keep feature matches from vsmany (allow fm_B)
    * Each keypoint gets
      - foregroundness
      - global distinctivness (databasewide) LNBNN
      - local distinctivness (imagewide) RATIO
      - regional match quality (descriptor based) COS
    * Circular hesaff keypoints
    * Asymetric weight scoring

    * FIX BUGS IN score_chipmatch_nsum FIRST THING TOMORROW.
     dict keys / vals are being messed up. very inoccuous


TestFuncs:
    >>> # VsMany Only
    python -m ibeis.model.hots.vsone_pipeline --test-show_post_vsmany_vser --show
    >>> # VsOne Only
    python -m ibeis.model.hots.vsone_pipeline --test-vsone_reranking --show --no-merge_vsmany
    >>> # VsOne + VsMany
    python -m ibeis.model.hots.vsone_pipeline --test-vsone_reranking --show

"""
from __future__ import absolute_import, division, print_function
import six
import numpy as np
import vtool as vt
#from ibeis.model.hots import neighbor_index
from ibeis.model.hots import voting_rules2 as vr2
from ibeis.model.hots import name_scoring
from ibeis.model.hots import hstypes
from ibeis.model.hots import scoring
#import pyflann
import functools
#from ibeis.model.hots import coverage_kpts
from vtool import matching
from ibeis.model.hots import _pipeline_helpers as plh  # NOQA
import utool as ut
from six.moves import zip, range  # NOQA
#profile = ut.profile
print, print_,  printDBG, rrr, profile = ut.inject(__name__, '[vsonepipe]', DEBUG=False)


from collections import namedtuple
PriorsTup = namedtuple('PriorsTup', ('fm_list', 'fs_list', 'H_list'))


def show_post_vsmany_vser():
    """ TESTFUNC just show the input data

    CommandLine:
        python -m ibeis.model.hots.vsone_pipeline --test-show_post_vsmany_vser --show --homog
        python -m ibeis.model.hots.vsone_pipeline --test-show_post_vsmany_vser --show --csum --homog

    Example:
        >>> from ibeis.model.hots.vsone_pipeline import *  # NOQA
        >>> show_post_vsmany_vser()
    """
    import plottool as pt
    ibs, qreq_, qaid2_prior_chipmatch, qaid_list, rrvsone_cfgdict = testdata_post_vsmany_sver()
    # HACK TO PRESCORE
    prescore_chipmatches_inplace(qreq_, qaid2_prior_chipmatch)
    show_all_top_chipmatches(qreq_.ibs, qaid2_prior_chipmatch, figtitle='vsmany post sver')
    pt.show_if_requested()


#@profile
def vsone_reranking(qreq_, qaid2_prior_chipmatch, verbose=False):
    """
    Driver function for vsone reranking

    CommandLine:
        python -m ibeis.model.hots.vsone_pipeline --test-vsone_reranking --show

        python -m ibeis.model.hots.vsone_pipeline --test-vsone_reranking --show

        python -m ibeis.model.hots.vsone_pipeline --test-vsone_reranking
        utprof.py -m ibeis.model.hots.vsone_pipeline --test-vsone_reranking

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis.model.hots.vsone_pipeline import *  # NOQA
        >>> ibs, qreq_, qaid2_prior_chipmatch, qaid_list, rrvsone_cfgdict = testdata_post_vsmany_sver()
        >>> # qaid2_prior_chipmatch = ut.dict_subset(qaid2_prior_chipmatch, [6])
        >>> qaid2_chipmatch_VSONE = vsone_reranking(qreq_, qaid2_prior_chipmatch)
        >>> #qaid2_chipmatch = qaid2_chipmatch_VSONE
        >>> if ut.show_was_requested():
        ...     import plottool as pt
        ...     figtitle = ut.dict_str(rrvsone_cfgdict, newlines=False)
        ...     show_all_top_chipmatches(qreq_.ibs, qaid2_chipmatch_VSONE, figtitle=figtitle)
        ...     pt.show_if_requested()
    """
    ibs = qreq_.ibs
    config = qreq_.qparams
    vsmany_filtkey_list = qreq_.qparams.get_postsver_filtkey_list()
    # First find a shortlist to execute vsone reranking on
    shortlist_tup = make_rerank_pair_shortlist(qreq_, qaid2_prior_chipmatch)
    qaid_list, daids_list, prior_chipmatch_list = shortlist_tup
    priors_list = [
        extract_vsmany_priors(vsmany_filtkey_list, chipmatch,  daids)
        for chipmatch, daids in zip(prior_chipmatch_list, daids_list)
    ]
    # Then execute vsone reranking
    # runs several pairs of (qaid, daids) vsone matches
    # For each qaid, daids pair in the lists, execute a query
    progkw = dict(nTotal=len(qaid_list), lbl='VSONE RERANKING', freq=1)
    _prog = functools.partial(ut.ProgressIter, **progkw)
    reranktup_list = [
        single_vsone_rerank(ibs, qaid, daid_list, priors, config)
        for (qaid, daid_list, priors) in _prog(zip(qaid_list, daids_list, priors_list))
    ]
    #(daid_list, scores_list, fms_list, fsvs_list) = vsone_res_tup
    # Format the output into chipmatches
    chipmatch_VSONE_list = []
    for reranktup, priors in zip(reranktup_list, priors_list):
        daids, scores, fms, fsvs = reranktup
        fks = [np.ones(len(fm), dtype=hstypes.FK_DTYPE) for fm in fms]
        aid2_fm    = dict(zip(daids, fms))
        aid2_fsv   = dict(zip(daids, fsvs))
        aid2_fk    = dict(zip(daids, fks))
        aid2_score = dict(zip(daids, scores))
        aid2_H     = dict(zip(daids, priors.H_list))
        chipmatch_VSONE = hstypes.ChipMatch(aid2_fm, aid2_fsv, aid2_fk, aid2_score, aid2_H)
        #cm = hstypes.ChipMatch2(chipmatch_VSONE)
        #fm.foo()
        chipmatch_VSONE_list.append(chipmatch_VSONE)
    qaid2_chipmatch_VSONE = dict(zip(qaid_list, chipmatch_VSONE_list))
    return qaid2_chipmatch_VSONE


def prescore_chipmatches_inplace(qreq_, qaid2_prior_chipmatch):
    # HACK POPULATE AID2_SCORE FIELD IN CHIPMATCH TUPLE
    for qaid, chipmatch in six.iteritems(qaid2_prior_chipmatch):
        daid_list, prescore_list = vr2.score_chipmatch_nsum(qaid, chipmatch, qreq_)
        ut.dict_assign(chipmatch.aid2_score, daid_list, prescore_list)


def extract_vsmany_priors(vsmany_filtkey_list, chipmatch_VSMANY, daid_list):
    """ gets normalized vsmany priors """
    vsmany_fm_list  = ut.dict_take(chipmatch_VSMANY.aid2_fm, daid_list)
    vsmany_fsv_list = ut.dict_take(chipmatch_VSMANY.aid2_fsv, daid_list)
    vsmany_H_list   = ut.dict_take(chipmatch_VSMANY.aid2_H, daid_list)
    # Normalize prior features scores
    lnbnn_index = vsmany_filtkey_list.index('lnbnn')
    vsmany_fs_list = [normalize_vsmany_scores(lnbnn_index, vsmany_fsv) for vsmany_fsv in vsmany_fsv_list]
    # package and return
    priors_tup = PriorsTup(vsmany_fm_list, vsmany_fs_list, vsmany_H_list)
    return priors_tup


def normalize_vsmany_scores(lnbnn_index, vsmany_fsv):
    # TODO: parametarize
    fs_lnbnn_min = .0001
    fs_lnbnn_max = .05
    fs_lnbnn_power = 1.0
    vsmany_fs = vsmany_fsv.T[lnbnn_index].T.copy()
    vsmany_fs = vt.clipnorm(vsmany_fs, fs_lnbnn_min, fs_lnbnn_max, out=vsmany_fs)
    vsmany_fs = np.power(vsmany_fs, fs_lnbnn_power, out=vsmany_fs)
    return vsmany_fs


@profile
def make_rerank_pair_shortlist(qreq_, qaid2_prior_chipmatch):
    """
    Makes shortlists for vsone reranking

    CommandLine:
        python -m ibeis.model.hots.vsone_pipeline --test-make_rerank_pair_shortlist

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis.model.hots.vsone_pipeline import *  # NOQA
        >>> ibs, qreq_, qaid2_prior_chipmatch, qaid_list, rrvsone_cfgdict= testdata_post_vsmany_sver()
        >>> # execute test function
        >>> shortlist_tup = make_rerank_pair_shortlist(qreq_, qaid2_prior_chipmatch)
        >>> # verify results
        >>> qaid, top_aid_list = ut.get_list_column(shortlist_tup[0:2], 0)
        >>> top_nid_list = ibs.get_annot_name_rowids(top_aid_list)
        >>> qnid = ibs.get_annot_name_rowids(qaid)
        >>> print('top_aid_list = %r' % (top_aid_list,))
        >>> print('top_nid_list = %r' % (top_nid_list,))
        >>> print('qnid = %r' % (qnid,))
        >>> assert top_nid_list.index(qnid) == 0, 'qnid=%r should be first rank' % (qnid,)
        >>> max_num_rerank = qreq_.qparams.nNameShortlistVsone * qreq_.qparams.nAnnotPerName
        >>> min_num_rerank = qreq_.qparams.nNameShortlistVsone
        >>> ut.assert_inbounds(len(top_nid_list), min_num_rerank, max_num_rerank, 'incorrect number in shortlist')
    """
    ibs = qreq_.ibs
    score_method = qreq_.qparams.score_method
    assert score_method == 'nsum'
    # TODO: paramaterize
    # Params: the max number of top names to get and the max number of
    # annotations per name to verify against
    nNameShortlistVsone = qreq_.qparams.nNameShortlistVsone
    nAnnotPerName       = qreq_.qparams.nAnnotPerName
    print('vsone reranking. ')
    # HACK TO PRESCORE
    prescore_chipmatches_inplace(qreq_, qaid2_prior_chipmatch)
    qaid_list = list(six.iterkeys(qaid2_prior_chipmatch))
    chipmatch_list = ut.dict_take(qaid2_prior_chipmatch, qaid_list)
    # now build the shortlist
    daids_list = []
    prior_chipmatch_list = []
    for qaid, chipmatch in zip(qaid_list, chipmatch_list):
        daid_list = list(six.iterkeys(chipmatch.aid2_score))
        prescore_list = ut.dict_take(chipmatch.aid2_score, daid_list)
        nscore_tup = name_scoring.group_scores_by_name(ibs, daid_list, prescore_list)
        (sorted_nids, sorted_nscore, sorted_aids, sorted_scores) = nscore_tup
        # Clip number of names
        _top_aids_list  = ut.listclip(sorted_aids, nNameShortlistVsone)
        # Clip number of annots per name
        _top_clipped_aids_list = [ut.listclip(aids, nAnnotPerName) for aids in _top_aids_list]
        top_aids = ut.flatten(_top_clipped_aids_list)
        prior_chipmatch = hstypes.chipmatch_subset(chipmatch, top_aids)
        # append shortlist results for this query aid
        prior_chipmatch_list.append(prior_chipmatch)
        daids_list.append(top_aids)
    shortlist_tup = (qaid_list, daids_list, prior_chipmatch_list)
    return shortlist_tup


@profile
def single_vsone_rerank(ibs, qaid, daid_list, priors=None, config={}):
    r"""
    Runs a single vsone-pair (query, daid_list)

    CommandLine:
        python -m ibeis.model.hots.vsone_pipeline --test-single_vsone_rerank:0
        python -m ibeis.model.hots.vsone_pipeline --test-single_vsone_rerank:0 --show

    Example1:
        >>> # ENABLE_DOCTEST
        >>> from ibeis.model.hots.vsone_pipeline import *  # NOQA
        >>> ibs, qreq_, qaid, daid_list, priors = testdata_matching()
        >>> config = qreq_.qparams
        >>> reranktup = single_vsone_rerank(ibs, qaid, daid_list, priors, config)
        >>> daid_list, score_list, fm_list, fsv_list = reranktup
        >>> cm = hstypes.ChipMatch2.from_reranktup(reranktup, qaid, priors.H_list)
        >>> if ut.show_was_requested():
        ...     import plottool as pt
        ...     show_single_chipmatch(ibs, cm)
        ...     pt.show_if_requested()
        >>> print(score_list)
    """
    #print('==================')
    merge_prior       = config.get('merge_vsmany')
    use_constrained   = config.get('use_constrained')
    use_unconstrained = config.get('use_unconstrained')
    assert use_unconstrained is not None

    if use_unconstrained:
        unc_match_results = compute_query_unconstrained_matches(ibs, qaid, daid_list, config)
        vsone_fm_list, vsone_fs_list, vsone_fm_norm_list = unc_match_results

    prior_fm_list, prior_fs_list, prior_H_list = priors

    if use_constrained:
        scr_match_results = compute_query_constrained_matches(ibs, qaid, daid_list, prior_H_list, config)
        fm_SCR_list, fs_SCR_list, fm_norm_SCR_list = scr_match_results

    if merge_prior:
        # COMBINE VSONE WITH VSMANY MATCHES
        new_fm_list = []
        new_fs_list = []
        vecs1 = ibs.get_annot_vecs(qaid)
        _iter = zip(daid_list, vsone_fm_list, vsone_fs_list, prior_fm_list, prior_fs_list)
        for daid, fm_A, fs_A, fm_B, fs_B in _iter:
            vecs2 = ibs.get_annot_vecs(daid)
            fm_merged, fs_merged = merge_match_lists(
                vecs1, vecs2,  fm_A, fs_A, fm_B, fs_B)
            new_fm_list.append(fm_merged)
            new_fs_list.append(fs_merged)
        fm_list = new_fm_list
        fs_list = new_fs_list
    else:
        fm_list = vsone_fm_list
        fs_list = vsone_fs_list

    #if qaid == 6:
    #    print(list(map(len, fm_list)))
    #    print(list(map(len, fs_list)))
    #    #print(list(map(len, fsv_list)))
    #    print(daid_list)
    #    ut.embed()

    cov_score_list = scoring.compute_grid_coverage_score(ibs, qaid, daid_list, fm_list, fs_list, config=config)
    # TODO: paramatarize
    #cov_score_list = scoring.compute_kpts_coverage_score(ibs, qaid, daid_list, fm_list, fs_list, config=config)
    NAME_SCORING = True
    NAME_SCORING = False
    if NAME_SCORING:
        # Keep only the best annotation per name
        # FIXME: There may be a problem here
        nscore_tup = name_scoring.group_scores_by_name(ibs, daid_list, cov_score_list)
        score_list = ut.flatten([scores[0:1].tolist() + ([0] * (len(scores) - 1))
                                 for scores in nscore_tup.sorted_scores])
    else:
        score_list = cov_score_list
    # Convert our one score to a score vector here
    num_filts = 1  # currently only using one vector here.
    num_matches_iter = map(len, fm_list)
    fsv_list = [fs.reshape((num_matches, num_filts))
                for fs, num_matches in zip(fs_list, num_matches_iter)]
    reranktup = (daid_list, score_list, fm_list, fsv_list)
    return reranktup


def merge_match_lists(fm_A, fs_A,
                      fm_B, fs_B,
                      fsv_A_cols, fsv_B_cols):
    """ combines feature matches from two matching algorithms """
    # Flag rows found in both fmA and fmB
    flags_A, flags_B = vt.intersect2d_flags(fm_A, fm_B)
    # get the intersecting (both) and unique (only) matches
    fm_both_AB  = fm_A.compress( flags_A, axis=0)
    fm_only_A   = fm_A.compress(~flags_A, axis=0)
    fm_only_B   = fm_B.compress(~flags_B, axis=0)
    #
    fs_both_A = fs_A.compress( flags_A)
    fs_both_B = fs_B.compress( flags_B)
    fs_only_A = fs_A.compress(~flags_A)
    fs_only_B = fs_B.compress(~flags_B)

    offset1 = len(fm_both_AB)
    offset2 = offset1 + len(fm_only_A)
    offset3 = offset2 + len(fm_only_B)
    # Merge feature matches
    fm_merged = np.vstack([fm_both_AB, fm_only_A, fm_only_B])
    # Merge feature scores
    fsv_merged_cols = fsv_A_cols + fsv_B_cols
    fsv_merged = np.full((len(fm_merged), len(fsv_merged_cols)), np.nan)
    fsv_merged[0:offset1, 0]       = fs_both_A
    fsv_merged[0:offset1, 1]       = fs_both_B
    fsv_merged[offset1:offset2, 0] = fs_only_A
    fsv_merged[offset2:offset3, 1] = fs_only_B
    fs_merged = np.nan_to_num(fsv_merged).max(axis=1)
    return fm_merged, fs_merged

#def
#    # find cosine angle between matching vectors
#    vecs1_m = vecs1.take(fm_merged.T[0], axis=0)
#    vecs2_m = vecs2.take(fm_merged.T[1], axis=0)
#    # TODO: Param
#    cos_power = 3.0
#    fs_region = scoring.sift_selectivity_score(vecs1_m, vecs2_m, cos_power)
#    fsv_merged[:, 2] = fs_region

    # NEED TO MERGE THESE INTO A SINGLE SCORE
    # A USING LINEAR COMBINATION?
    #nan_weight = ~np.isnan(fsv_merged)
    # for now simply take the maximum of the 3 scores
    # TODO: can experiment with trying np.nanmin so each
    # keypoint gets the worst non-nan score
    fs_merged = np.nan_to_num(fsv_merged).max(axis=1)


def quick_vsone_flann(ibs, qvecs):
    flann_cachedir = ibs.get_flann_cachedir()
    flann_params = {
        'algorithm': 'kdtree',
        'trees': 8
    }
    use_cache = save = False and ut.is_developer()
    flann = vt.flann_cache(qvecs, flann_cachedir, flann_params=flann_params,
                           quiet=True, verbose=False, use_cache=use_cache, save=save)
    return flann


@profile
def compute_query_constrained_matches(ibs, qaid, daid_list, H_list, config):
    """

    CommandLine:
        python -m ibeis.model.hots.vsone_pipeline --test-compute_query_constrained_matches --show
        python -m ibeis.model.hots.vsone_pipeline --test-compute_query_constrained_matches --show --shownorm
        python -m ibeis.model.hots.vsone_pipeline --test-compute_query_constrained_matches --show --shownorm --homog

    Example1:
        >>> # ENABLE_DOCTEST
        >>> from ibeis.model.hots.vsone_pipeline import *  # NOQA
        >>> ibs, qreq_, qaid, daid_list, priors = testdata_matching()
        >>> config = qreq_.qparams
        >>> H_list = priors.H_list
        >>> fm_SCR_list, fs_SCR_list, fm_norm_SCR_list = compute_query_constrained_matches(ibs, qaid, daid_list, H_list, config)
        >>> print('depth_profile(fs_SCR_list) = ' + str(ut.depth_profile(fs_SCR_list)))
        >>> print('depth_profile(fm_SCR_list) = ' + str(ut.depth_profile(fm_SCR_list)))
        >>> print('daid_list = ' + str(daid_list))
        >>> if ut.show_was_requested():
        ...     import plottool as pt
        ...     idx = ut.listfind(ibs.get_annot_nids(daid_list), ibs.get_annot_nids(qaid))
        ...     args = (ibs, qaid, daid_list, fm_SCR_list, fs_SCR_list, fm_norm_SCR_list, H_list)
        ...     show_single_match(*args, index=idx)
        ...     pt.set_title('unconstrained')
        ...     pt.show_if_requested()
    """
    scr_ratio_thresh     = config.get('scr_ratio_thresh', .7)
    scr_K                = config.get('scr_K', 7)
    scr_match_xy_thresh  = config.get('scr_match_xy_thresh', .05)
    scr_norm_xy_min      = config.get('scr_norm_xy_min', 0.1)
    scr_norm_xy_max      = config.get('scr_norm_xy_max', 1.0)
    scr_norm_xy_bounds = (scr_norm_xy_min, scr_norm_xy_max)
    # query info
    vecs1 = ibs.get_annot_vecs(qaid)
    kpts1 = ibs.get_annot_kpts(qaid)
    # database info
    vecs2_list = ibs.get_annot_vecs(daid_list)
    kpts2_list = ibs.get_annot_kpts(daid_list)
    chip2_dlen_sqrd_list = ibs.get_annot_chip_dlen_sqrd(daid_list)  # chip diagonal length
    # build flann for query vectors
    flann = quick_vsone_flann(ibs, vecs1)
    # match database chips to query chip
    scr_kwargs = {
        'scr_K'            : scr_K,
        'match_xy_thresh'  : scr_match_xy_thresh,
        'norm_xy_bounds'   : scr_norm_xy_bounds,
        'scr_ratio_thresh' : scr_ratio_thresh,
    }
    print('scr_kwargs = ' + ut.dict_str(scr_kwargs))
    scr_kwargs.update({
        'fm_dtype'         : hstypes.FM_DTYPE,
        'fs_dtype'         : hstypes.FS_DTYPE,
    })
    # Homographys in H_list map image1 space into image2 space
    scrtup_list = [
        matching.spatially_constrained_ratio_match(
            flann, vecs2, kpts1, kpts2, H, chip2_dlen_sqrd, **scr_kwargs)
        for vecs2, kpts2, chip2_dlen_sqrd, H in
        zip(vecs2_list, kpts2_list, chip2_dlen_sqrd_list, H_list)]
    # return matches and scores
    fm_SCR_list = ut.get_list_column(scrtup_list, 0)
    fs_SCR_list = ut.get_list_column(scrtup_list, 1)
    fm_norm_SCR_list = ut.get_list_column(scrtup_list, 2)
    match_results = fm_SCR_list, fs_SCR_list, fm_norm_SCR_list
    return match_results


@profile
def compute_query_unconstrained_matches(ibs, qaid, daid_list, config):
    """

    CommandLine:
        python -m ibeis.model.hots.vsone_pipeline --test-compute_query_unconstrained_matches --show
        python -m ibeis.model.hots.vsone_pipeline --test-compute_query_unconstrained_matches --show --shownorm
        python -m ibeis.model.hots.vsone_pipeline --test-compute_query_unconstrained_matches --show --shownorm --homog

    Example1:
        >>> # ENABLE_DOCTEST
        >>> from ibeis.model.hots.vsone_pipeline import *  # NOQA
        >>> ibs, qreq_, qaid, daid_list, priors = testdata_matching()
        >>> config = qreq_.qparams
        >>> match_results = compute_query_unconstrained_matches(ibs, qaid, daid_list, config)
        >>> H_list = priors.H_list
        >>> fm_RAT_list, fs_RAT_list, fm_norm_RAT_list = match_results
        >>> print('depth_profile(fs_RAT_list) = ' + str(ut.depth_profile(fs_RAT_list)))
        >>> print('depth_profile(fm_norm_RAT_list) = ' + str(ut.depth_profile(fm_norm_RAT_list)))
        >>> print('daid_list = ' + str(daid_list))
        >>> if ut.show_was_requested():
        ...     import plottool as pt
        ...     idx = ut.listfind(ibs.get_annot_nids(daid_list), ibs.get_annot_nids(qaid))
        ...     args = (ibs, qaid, daid_list, fm_RAT_list, fs_RAT_list, fm_norm_RAT_list, H_list)
        ...     show_single_match(*args, index=idx)
        ...     pt.set_title('unconstrained')
        ...     pt.show_if_requested()
    """
    unc_ratio_thresh = config.get('unc_ratio_thresh', .625)
    # query info
    qvecs = ibs.get_annot_vecs(qaid)
    # database info
    dvecs_list = ibs.get_annot_vecs(daid_list)
    # build flann for query vectors
    flann = quick_vsone_flann(ibs, qvecs)
    # match database chips to query chip
    rat_kwargs = {
        'unc_ratio_thresh' : unc_ratio_thresh,
        'fm_dtype'     : hstypes.FM_DTYPE,
        'fs_dtype'     : hstypes.FS_DTYPE,
    }
    print('rat_kwargs = ' + ut.dict_str(rat_kwargs))
    scrtup_list = [
        matching.unconstrained_ratio_match(
            flann, dvecs, **rat_kwargs)
        for dvecs in dvecs_list]
    # return matches and scores
    fm_RAT_list = ut.get_list_column(scrtup_list, 0)
    fs_RAT_list = ut.get_list_column(scrtup_list, 1)
    fm_norm_RAT_list = ut.get_list_column(scrtup_list, 2)
    match_results = fm_RAT_list, fs_RAT_list, fm_norm_RAT_list
    return match_results


# -----------------------------
# TESTDATA
# -----------------------------


def testdata_post_vsmany_sver():
    """
        >>> from ibeis.model.hots.vsone_pipeline import *  # NOQA
    """
    dbname = ut.get_argval('--db', str, 'PZ_MTEST')
    cfgdict = dict(dupvote_weight=1.0,
                   prescore_method='nsum',
                   score_method='nsum',
                   sver_weighting=True)
    rrvsone_cfgdict = {
        'merge_vsmany': True,
        'use_unconstrained': True,
        'use_constrained': True,
    }

    rrvsone_cfgdict = ut.util_arg.argparse_dict(rrvsone_cfgdict)
    cfgdict.update(rrvsone_cfgdict)

    qaid = ut.get_argval('--qaid', int, 1)
    daid_list = ut.get_argval('--daid_list', list, None)
    #ut.embed()
    if daid_list is None:
        daid_list = 'all'
    qaid_list = [qaid]
    # VSMANY TO GET HOMOG
    ibs, qreq_ = plh.get_pipeline_testdata(dbname, cfgdict=cfgdict, qaid_list=qaid_list, daid_list=daid_list)
    if len(ibs.get_annot_groundtruth(qaid)) == 0:
        print('WARNING: qaid=%r has no groundtruth' % (qaid,))
    locals_ = plh.testrun_pipeline_upto(qreq_, 'chipmatch_to_resdict')
    qaid2_chipmatch = locals_['qaid2_chipmatch_SVER']
    return ibs, qreq_, qaid2_chipmatch, qaid_list, rrvsone_cfgdict


def testdata_matching():
    """
        >>> from ibeis.model.hots.vsone_pipeline import *  # NOQA
    """
    ibs, qreq_, qaid2_chipmatch, qaid_list, rrvsone_cfgdict = testdata_post_vsmany_sver()
    qaid_list, daids_list, prior_chipmatch_list = make_rerank_pair_shortlist(qreq_, qaid2_chipmatch)
    vsmany_filtkey_list = qreq_.qparams.get_postsver_filtkey_list()
    priors_list = [
        extract_vsmany_priors(vsmany_filtkey_list, chipmatch,  daids)
        for chipmatch, daids in zip(prior_chipmatch_list, daids_list)
    ]
    qaid = qaid_list[0]
    daid_list = daids_list[0]
    priors = priors_list[0]
    return ibs, qreq_, qaid, daid_list, priors


# -----------------------------
# GRIDSEARCH
# -----------------------------


def gridsearch_constrained_matches():
    r"""

    CommandLine:
        python -m ibeis.model.hots.vsone_pipeline --test-gridsearch_constrained_matches --show
        python -m ibeis.model.hots.vsone_pipeline --test-gridsearch_constrained_matches --show --testindex 2

    Example:
        >>> # DISABLE_DOCTEST
        >>> import plottool as pt
        >>> from ibeis.model.hots.vsone_pipeline import *  # NOQA
        >>> gridsearch_constrained_matches()
        >>> pt.show_if_requested()
    """
    import plottool as pt
    fnum = 1

    varied_dict = {
        'scr_ratio_thresh': [.625, .3, .9, 0.0, 1.0],
        'scr_K': [7, 2],
        'scr_xy_thresh': [.05, 1.0, .1],
        'scr_norm_xy_min': [0, .1, .2],
        'scr_norm_xy_max': [1, .3],
    }
    slice_dict = {
        'scr_ratio_thresh': slice(0, 1),
        'scr_K': slice(0, 2),
        'scr_xy_thresh': slice(0, 2),
        'scr_norm_xy_min': slice(0, 2),
        'scr_norm_xy_max': slice(0, 2),
    }

    def constrain_func(cfg):
        if cfg['scr_norm_xy_min'] >= cfg['scr_norm_xy_max']:
            return False

    # Make configuration for every parameter setting
    cfgdict_list, cfglbl_list = ut.make_constrained_cfg_and_lbl_list(
        varied_dict, constrain_func, slice_dict=slice_dict, defaultslice=slice(0, 10))
    #fname = None  # 'easy1.png'
    ibs, qreq_, qaid, daid_list, priors = testdata_matching()
    H_list = priors.H_list
    #config = qreq_.qparams
    cfgresult_list = [
        compute_query_constrained_matches(ibs, qaid, daid_list, H_list, cfgdict)
        for cfgdict in ut.ProgressIter(cfgdict_list, lbl='constrained ratio match')
    ]
    # which result to look at
    index = ut.get_argval('--testindex', int, 0)
    score_list = [scrtup[1][index].sum() for scrtup in cfgresult_list]
    #score_list = [scrtup[1][0].sum() / len(scrtup[1][0]) for scrtup in cfgresult_list]
    showfunc = functools.partial(show_single_match, ibs, qaid, daid_list, H_list=H_list, index=index)
    ut.interact_gridsearch_result_images(
        showfunc, cfgdict_list, cfglbl_list,
        cfgresult_list, score_list=score_list, fnum=fnum,
        figtitle='constrained ratio match', unpack=True,
        max_plots=25, scorelbl='sumscore')

    #if use_separate_norm:
    #    ut.interact_gridsearch_result_images(
    #        functools.partial(show_single_match, use_separate_norm=True), cfgdict_list, cfglbl_list,
    #        cfgresult_list, fnum=fnum + 1, figtitle='constrained ratio match', unpack=True,
    #        max_plots=25, scorelbl='sumscore')
    pt.iup()

# -----------------------------
# VISUALIZATIONS
# -----------------------------


def show_single_match(ibs, qaid, daid_list, fm_list, fs_list, fm_norm_list=None, H_list=None, index=None, **kwargs):
    use_sameaxis_norm = ut.get_argflag('--shownorm')
    fs = fs_list[index]
    fm = fm_list[index]
    if use_sameaxis_norm:
        fm_norm = fm_norm_list[index]
    else:
        fm_norm = None
    kwargs['darken'] = .7
    #if use_separate_norm is not None:
    #    if use_separate_norm:
    #        fm_norm = None
    #        fm = fm_norm_list[index]
    #        kwargs['cmap'] = 'cool'
    #    else:
    #        fm = fm_list[index]
    #        fm_norm = None
    #    kwargs['ell'] = False
    daid = daid_list[index]
    H1 = H_list[index]
    #H1 = None  # uncomment to see warping
    show_constrained_chipmatch(ibs, qaid, daid, fm, fs=fs, H1=H1, fm_norm=fm_norm, **kwargs)


def show_constrained_chipmatch(ibs, qaid, daid, fm, fs=None, fm_norm=None,
                               H1=None, fnum=None, pnum=None, **kwargs):
    if not ut.get_argflag('--homog'):
        H1 = None
    # viz function for compute_query_constrained_matches
    from ibeis.viz import viz_matches
    #import plottool as pt
    viz_matches.show_matches2(ibs, qaid, daid, fm=fm, fs=fs, fm_norm=fm_norm,
                              H1=H1, fnum=fnum, pnum=pnum, show_name=False, **kwargs)
    #pt.set_title('score = %.3f' % (score,))


def show_single_chipmatch(ibs, chipmatch, qaid=None, fnum=None):
    import plottool as pt
    if fnum is None:
        fnum = pt.next_fnum()
    if qaid is None:
        qaid = chipmatch.qaid
    CLIP_TOP = 6
    daid_list     = list(six.iterkeys(chipmatch.aid2_fm))
    score_list    = ut.dict_take(chipmatch.aid2_score, daid_list)
    top_daid_list = ut.listclip(ut.sortedby(daid_list, score_list, reverse=True), CLIP_TOP)
    nRows, nCols  = pt.get_square_row_cols(len(top_daid_list), fix=True)
    next_pnum     = pt.make_pnum_nextgen(nRows, nCols)
    for daid in top_daid_list:
        fm    = chipmatch.aid2_fm[daid]
        fsv   = chipmatch.aid2_fsv[daid]
        fs    = fsv.prod(axis=1)
        H1 = chipmatch.aid2_H[daid]
        pnum = next_pnum()
        #with ut.EmbedOnException():
        show_constrained_chipmatch(ibs, qaid, daid, fm=fm, fs=fs, H1=H1, fnum=fnum, pnum=pnum)
        score = chipmatch.aid2_score[daid]
        pt.set_title('score = %.3f' % (score,))


def show_all_top_chipmatches(ibs, qaid2_chipmatch, fnum_offset=0, figtitle=''):
    """ helper """
    import plottool as pt
    for fnum_, (qaid, chipmatch) in enumerate(six.iteritems(qaid2_chipmatch)):
        #cm = hstypes.ChipMatch2(chipmatch)
        #cm.foo()
        fnum = fnum_ + fnum_offset
        show_single_chipmatch(ibs, chipmatch, qaid, fnum)
        #pt.figure(fnum=fnum, doclf=True, docla=True)
        pt.set_figtitle('qaid=%r %s' % (qaid, figtitle))


if __name__ == '__main__':
    """
    CommandLine:
        python -m ibeis.model.hots.vsone_pipeline
        python -m ibeis.model.hots.vsone_pipeline --allexamples
        python -m ibeis.model.hots.vsone_pipeline --allexamples --noface --nosrc
    """
    import multiprocessing
    multiprocessing.freeze_support()  # for win32
    import utool as ut  # NOQA
    ut.doctest_funcs()
