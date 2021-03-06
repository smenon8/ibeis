# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
import utool
(print, print_,  rrr, profile, printDBG) = utool.inject(__name__, '[imageset]', DEBUG=False)
# Python
import six
from six.moves import zip, range
# Science
import networkx as netx
import numpy as np
# HotSpotter
from ibeis.model.hots import match_chips3 as mc3

import utool


def build_imageset_ids(ex2_gxs, gid2_clusterid):
    USE_STRING_ID = True
    gid2_imgsetid = [None] * len(gid2_clusterid)
    for ex, gids in enumerate(ex2_gxs):
        for gid in gids:
            nGx = len(gids)
            gid2_imgsetid[gid] = ('ex=%r_nGxs=%d' % (ex, nGx)
                             if USE_STRING_ID else
                             ex + (nGx / 10 ** np.ceil(np.log(nGx) / np.log(10))))


def get_chip_imagesets(ibs):
    gid2_ex, ex2_gxs = compute_occurrences(ibs)  # NOQA
    # Build imageset to chips from imageset to images
    ex2_cxs = [None for _ in range(len(ex2_gxs))]
    for ex, gids in enumerate(ex2_gxs):
        ex2_cxs[ex] = utool.flatten(ibs.gid2_cxs(gids))
    # optional
    # resort imagesets by number of chips
    ex2_nCxs = list(map(len, ex2_cxs))
    ex2_cxs = [y for (x, y) in sorted(zip(ex2_nCxs, ex2_cxs))]
    return ex2_cxs


def get_fmatch_iter(res):
    # USE res.get_fmatch_iter()
    fmfsfk_enum = enumerate(zip(res.aid2_fm, res.aid2_fs, res.aid2_fk))
    fmatch_iter = ((aid, fx_tup, score, rank)
                   for aid, (fm, fs, fk) in fmfsfk_enum
                   for (fx_tup, score, rank) in zip(fm, fs, fk))
    return fmatch_iter


def get_cxfx_enum(qreq):
    dx2_cxs = qreq._data_index.dx2_cx
    dx2_fxs = qreq._data_index.dx2_fx
    aidfx_enum = enumerate(zip(dx2_cxs, dx2_fxs))
    return aidfx_enum


def intra_query_cxs(ibs, aids):
    dcxs = qcxs = aids
    qreq = mc3.prep_query_request(qreq=ibs.qreq, qcxs=qcxs, dcxs=dcxs,
                                  query_cfg=ibs.prefs.query_cfg)
    qcx2_res = mc3.process_query_request(ibs, qreq)
    return qcx2_res


#def intra_occurrence_match(ibs, aids, **kwargs):
    # Make a graph between the chips
    #qcx2_res = intra_query_cxs(aids)
    #graph = make_chip_graph(qcx2_res)
    # TODO: Make a super cool algorithm which does this correctly
    #graph.cutEdges(**kwargs)
    # Get a temporary name id
    # TODO: ensure these name indexes do not conflict with other imagesets
    #aid2_nx, nid2_cxs = graph.getConnectedComponents()
    #return graph


def execute_all_intra_occurrence_match(ibs, **kwargs):
    # Group images / chips into imagesets
    ex2_cxs = get_chip_imagesets(ibs)
    # For each imageset
    ex2_names = {}
    for ex, aids in enumerate(ex2_cxs):
        pass
        # Perform Intra-ImageSet Matching
        #nid2_cxs = intra_occurrence_match(ibs, aids)
        #ex2_names[ex] = nid2_cxs
    return ex2_names


def inter_imageset_match(ibs, imgsetid2_names=None, **kwargs):
    # Perform Inter-ImageSet Matching
    #if imgsetid2_names is None:
        #imgsetid2_names = intra_occurrence_match(ibs, **kwargs)
    all_nxs = utool.flatten(imgsetid2_names.values())
    for nid2_cxs in imgsetid2_names:
        qnxs = nid2_cxs
        dnxs = all_nxs
        name_result = ibs.query(qnxs=qnxs, dnxs=dnxs)
    qcx2_res = name_result.chip_results()
    graph = netx.Graph()
    graph.add_nodes_from(list(range(len(qcx2_res))))
    graph.add_edges_from([res.aid2_fm for res in six.itervalues(qcx2_res)])
    graph.setWeights([(res.aid2_fs, res.aid2_fk) for res in six.itervalues(qcx2_res)])
    graph.cutEdges(**kwargs)
    aid2_nx, nid2_cxs = graph.getConnectedComponents()
    return aid2_nx


def print_imageset_stats(ex2_cxs):
    ex2_nCxs = list(map(len, ex2_cxs))
    ex_statstr = utool.common_stats(ex2_nCxs)
    print('num_imagesets = %r' % len(ex2_nCxs))
    print('imageset_stats = %r' % (ex_statstr,))
