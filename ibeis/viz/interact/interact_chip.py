# -*- coding: utf-8 -*-
"""
Interaction for a single annoation.
Also defines annotation context menu.

CommandLine:
    python -m ibeis.viz.interact.interact_chip --test-ishow_chip --show --aid 2
"""
from __future__ import absolute_import, division, print_function, unicode_literals
from ibeis import viz
import utool as ut
import vtool as vt
import plottool as pt  # NOQA
from functools import partial
import six
from ibeis import constants as const
from plottool import draw_func2 as df2
from plottool.viz_featrow import draw_feat_row
from ibeis.viz import viz_helpers as vh
from plottool import interact_helpers as ih

(print, rrr, profile) = ut.inject2(__name__, '[interact_chip]')


def interact_multichips(ibs, aid_list, config2_=None, **kwargs):
    r"""
    Args:
        ibs (IBEISController):  ibeis controller object
        aid_list (list):  list of annotation rowids

    Returns:
        MultiImageInteraction: iteract_obj

    CommandLine:
        python -m ibeis.viz.interact.interact_chip --exec-interact_multichips --show

    Example:
        >>> # SLOW_DOCTEST
        >>> from ibeis.viz.interact.interact_chip import *  # NOQA
        >>> import ibeis
        >>> ibs = ibeis.opendb(defaultdb='testdb1')
        >>> aid_list = ibs.get_valid_aids()
        >>> iteract_obj = interact_multichips(ibs, aid_list)
        >>> iteract_obj.start()
        >>> result = ('iteract_obj = %s' % (str(iteract_obj),))
        >>> print(result)
        >>> ut.show_if_requested()
    """
    # FIXME: needs to be flushed out a little
    import plottool as pt
    show_chip_list = [
        partial(viz.show_chip, ibs, aid, config2_=config2_)
        for aid in aid_list
    ]
    vizkw = dict(ell=0, pts=1)
    context_option_funcs = [
        partial(build_annot_context_options, ibs, aid, config2_=config2_)
        for aid in aid_list
    ]
    iteract_obj = pt.interact_multi_image.MultiImageInteraction(
        show_chip_list, context_option_funcs=context_option_funcs,
        vizkw=vizkw, **kwargs)
    return iteract_obj


def show_annot_context_menu(ibs, aid, qwin, qpoint, refresh_func=None,
                            with_interact_name=True, with_interact_chip=True,
                            with_interact_image=True, config2_=None):
    """
    Defines logic for poping up a context menu when viewing an annotation.
    Used in other interactions like name_interaction and interact_query_decision

    CommandLine:
        python -m ibeis.viz.interact.interact_chip --test-ishow_chip --show

    """
    import guitool
    callback_list = build_annot_context_options(
        ibs, aid, refresh_func=refresh_func,
        with_interact_name=with_interact_name,
        with_interact_chip=with_interact_chip,
        with_interact_image=with_interact_image, config2_=config2_)
    guitool.popup_menu(qwin, qpoint, callback_list)


def build_annot_context_options(ibs, aid, refresh_func=None,
                                 with_interact_name=True,
                                 with_interact_chip=True,
                                 with_interact_image=True, config2_=None):
    r"""
    Args:
        ibs (IBEISController):  ibeis controller object
        aid (int):  annotation id
        refresh_func (None): (default = None)
        with_interact_name (bool): (default = True)
        with_interact_chip (bool): (default = True)
        with_interact_image (bool): (default = True)
        config2_ (dict): (default = None)

    Returns:
        list: callback_list

    CommandLine:
        python -m ibeis.viz.interact.interact_chip --exec-build_annot_context_options

    Example:
        >>> # DISABLE_DOCTEST
        >>> from ibeis.viz.interact.interact_chip import *  # NOQA
        >>> import ibeis
        >>> ibs = ibeis.opendb(defaultdb='testdb1')
        >>> aid = ibs.get_valid_aids()[0]
        >>> refresh_func = None
        >>> with_interact_name = True
        >>> with_interact_chip = True
        >>> with_interact_image = True
        >>> config2_ = None
        >>> callback_list = build_annot_context_options(ibs, aid, refresh_func,
        >>>                                             with_interact_name,
        >>>                                             with_interact_chip,
        >>>                                             with_interact_image,
        >>>                                             config2_)
        >>> result = ('callback_list = %s' % (ut.list_str(callback_list, nl=4),))
        >>> print(result)
    """
    import guitool
    is_exemplar = ibs.get_annot_exemplar_flags(aid)

    def refresh_wrp(func):
        def _wrp():
            ret = func()
            if refresh_func is None:
                print('no refresh func')
            else:
                print('calling refresh_func=%r' % (refresh_func,))
                refresh_func()
            return ret
        return _wrp

    def newplot_wrp(func):
        def _wrp():
            import plottool as pt
            ret = func()
            pt.draw()
            return ret
        return _wrp

    @refresh_wrp
    def toggle_exemplar_func():
        new_flag = not is_exemplar
        print('set_annot_exemplar(%r, %r)' % (aid, new_flag))
        ibs.set_annot_exemplar_flags(aid, new_flag)
    def set_yaw_func(yawtext):
        #@refresh_wrp()
        def _wrap_yaw():
            ibs.set_annot_yaw_texts([aid], [yawtext])
            print('set_annot_yaw(%r, %r)' % (aid, yawtext))
        return _wrap_yaw
    def set_quality_func(qualtext):
        #@refresh_wrp()
        def _wrp_qual():
            ibs.set_annot_quality_texts([aid], [qualtext])
            print('set_annot_quality(%r, %r)' % (aid, qualtext))
        return _wrp_qual
    # Define popup menu
    callback_list = []

    nid = ibs.get_annot_name_rowids(aid)

    if with_interact_chip:
        callback_list += [
            ('Interact chip',
             partial(
                 ishow_chip, ibs, aid, fnum=None, config2_=config2_))
        ]

    if with_interact_name and not ibs.is_nid_unknown(nid):
        from ibeis.viz.interact import interact_name
        callback_list.append(
            ('Interact name', partial(interact_name.ishow_name, ibs,
                                                nid, fnum=None))
        )
        from ibeis.viz import viz_graph
        callback_list.append(
            ('Interact name graph',
             partial(viz_graph.make_name_graph_interaction,
                               ibs, nids=None, aids=[aid])),
        )

    if with_interact_image:
        gid = ibs.get_annot_gids(aid)
        from ibeis.viz.interact import interact_annotations2
        callback_list.append(
            ('Interact image',
             partial(
                 interact_annotations2.ishow_image2, ibs, gid, fnum=None))
        )

    if True:
        from ibeis import viz
        callback_list.append(
            ('Show foreground mask',
             newplot_wrp(lambda: viz.show_probability_chip(
                 ibs, aid, config2_=config2_))),
        )
        callback_list.append(
            ('Show foreground mask (blended)',
             newplot_wrp(lambda: viz.show_probability_chip(
                 ibs, aid, config2_=config2_, blend=True))),
        )

    if True:
        # Edit mask
        callback_list.append(
            ('Edit mask',
             partial(ibs.depc_annot.get_property, 'annotmask', aid, recompute=True))
        )

    current_qualtext = ibs.get_annot_quality_texts([aid])[0]
    current_yawtext = ibs.get_annot_yaw_texts([aid])[0]
    # Nested viewpoints
    callback_list += [
        #('Set Viewpoint: ' + key, set_yaw_func(key))
        ('Set &Viewpoint: ',  [
            ('&' + str(count) + ' ' +
             ('*' if current_yawtext == key else '') + key,
             set_yaw_func(key))
            for count, key in
            enumerate(six.iterkeys(const.VIEWTEXT_TO_YAW_RADIANS), start=1)
        ]),
    ]
    # Nested qualities
    callback_list += [
        #('Set Quality: ' + key, set_quality_func(key))
        ('Set &Quality: ',  [
            ('&' + str(count) + ' ' + ('*' if current_qualtext == key else '') +
             '&' + key,
             set_quality_func(key))
            for count, key in
            enumerate(six.iterkeys(const.QUALITY_TEXT_TO_INT), start=1)
        ]),
    ]

    with_tags = True
    if with_tags:
        from ibeis import tag_funcs
        case_list = tag_funcs.get_available_annot_tags()
        tags = ibs.get_annot_case_tags([aid])[0]
        tags = [_.lower() for _ in tags]

        case_hotlink_list = guitool.make_word_hotlinks(case_list,
                                                       after_colon=True)

        def _wrap_set_annot_prop(prop, toggle_val):
            if ut.VERBOSE:
                print('[SETTING] Clicked set prop=%r to val=%r' %
                      (prop, toggle_val,))
            ibs.set_annot_prop(prop, [aid], [toggle_val])
            if ut.VERBOSE:
                print('[SETTING] done')

        annot_tag_options = []
        for case, case_hotlink in zip(case_list, case_hotlink_list):
            toggle_val = case.lower() not in tags
            fmtstr = 'Mark %s case' if toggle_val else 'Untag %s'
            annot_tag_options += [
                #(fmtstr % (case_hotlink,), lambda:
                #ibs.set_annotmatch_prop(case, _get_annotmatch_rowid(),
                #                        [toggle_val])),
                #(fmtstr % (case_hotlink,), partial(ibs.set_annotmatch_prop,
                #case, [annotmatch_rowid], [toggle_val])),
                (fmtstr % (case_hotlink,), partial(_wrap_set_annot_prop, case,
                                                   toggle_val)),
            ]

        callback_list += [
            ('Set Annot Ta&gs', annot_tag_options),
        ]

    callback_list += [
        ('Remove name', lambda: ibs.set_annot_name_rowids([aid], [-aid]))
    ]

    callback_list += [
        ('Unset as e&xemplar' if is_exemplar else 'Set as e&xemplar',
         toggle_exemplar_func),
    ]

    annot_info = ibs.get_annot_info(
        aid, default=True, gname=False, name=False, notes=False,
        exemplar=False)

    def print_annot_info():
        print('[interact_chip] Annotation Info = ' + ut.obj_str(annot_info, nl=4))
        print('config2_ = %r' % (config2_,))
        if config2_ is not None:
            print('config2_.__dict__ = %s' % (ut.repr3(config2_.__dict__),))

    callback_list += [
        ('dev print annot info', print_annot_info),
        ('dev refresh', pt.update),
    ]

    if ut.is_developer():
        def dev_debug():
            print('aid = %r' % (aid,))
            print('config2_ = %r' % (config2_,))
        def dev_embed(ibs=ibs, aid=aid, config2_=config2_):
            #import plottool as pt
            #pt.plt.ioff()
            # TODO need to disable matplotlib callbacks?
            # Causes can't re-enter readline error
            ut.embed()
            #pt.plt.ion()
            pass
        callback_list += [
            ('dev chip context embed', dev_embed),
            ('dev chip context debug', dev_debug),
        ]
    return callback_list


#def custom_chip_click(event):
#    ax = event.inaxes
#    if ih.clicked_outside_axis(event):
#        pass
#    else:
#        viztype = vh.get_ibsdat(ax, 'viztype')
#        print('[ic] viztype=%r' % viztype)
#        if viztype == 'chip':
#            if event.button == 3:   # right-click
#                import guitool
#                from ibeis.viz.interact import interact_chip
#                height = fig.canvas.geometry().height()
#                qpoint = guitool.newQPoint(event.x, height - event.y)
#                refresh_func = partial(_chip_view, **kwargs)
#                interact_chip.show_annot_context_menu(
#                    ibs, aid, fig.canvas, qpoint, refresh_func=refresh_func,
#                    with_interact_chip=False, config2_=config2_)


# CHIP INTERACTION 2
def ishow_chip(ibs, aid, fnum=2, fx=None, dodraw=True, config2_=None,
               ischild=False, **kwargs):
    r"""

    # TODO:
        split into two interactions
        interact chip and interact chip features

    Args:
        ibs (IBEISController):  ibeis controller object
        aid (int):  annotation id
        fnum (int):  figure number
        fx (None):

    CommandLine:
        python -m ibeis.viz.interact.interact_chip --test-ishow_chip --show
        python -m ibeis.viz.interact.interact_chip --test-ishow_chip --show --aid 2

    Example:
        >>> # DISABLE_DOCTEST
        >>> from ibeis.viz.interact.interact_chip import *  # NOQA
        >>> import ibeis
        >>> # build test data
        >>> ibs = ibeis.opendb('testdb1')
        >>> aid = ut.get_argval('--aid', type_=int, default=1)
        >>> fnum = 2
        >>> fx = None
        >>> # execute function
        >>> dodraw = ut.show_was_requested()
        >>> result = ishow_chip(ibs, aid, fnum, fx, dodraw)
        >>> # verify results
        >>> pt.show_if_requested()
        >>> print(result)
    """
    fnum = pt.ensure_fnum(fnum)
    vh.ibsfuncs.assert_valid_aids(ibs, (aid,))
    # TODO: Reconcile this with interact keypoints.
    # Preferably this will call that but it will set some fancy callbacks
    if not ischild:
        fig = ih.begin_interaction('chip', fnum)
    else:
        fig = pt.gcf()
        #fig = pt.figure(fnum=fnum, pnum=pnum)

    # Get chip info (make sure get_chips is called first)
    #mode_ptr = [1]
    mode_ptr = [0]

    def _select_fxth_kpt(fx):
        # Get the fx-th keypiont
        chip = ibs.get_annot_chips(aid, config2_=config2_)
        kp = ibs.get_annot_kpts(aid, config2_=config2_)[fx]
        sift = ibs.get_annot_vecs(aid, config2_=config2_)[fx]
        # Draw chip + keypoints + highlighted plots
        _chip_view(pnum=(2, 1, 1), sel_fx=fx)
        #ishow_chip(ibs, aid, fnum=None, fx=fx, config2_=config2_, **kwargs)
        # Draw the selected feature plots
        nRows, nCols, px = (2, 3, 3)
        draw_feat_row(chip, fx, kp, sift, fnum, nRows, nCols, px, None)

    def _chip_view(mode=0, pnum=(1, 1, 1), **kwargs):
        print('... _chip_view mode=%r' % mode_ptr[0])
        kwargs['ell'] = mode_ptr[0] == 1
        kwargs['pts'] = mode_ptr[0]  == 2

        if not ischild:
            df2.figure(fnum=fnum, pnum=pnum, docla=True, doclf=True)
        # Toggle no keypoints view
        viz.show_chip(ibs, aid, fnum=fnum, pnum=pnum, config2_=config2_,
                      **kwargs)
        df2.set_figtitle('Chip View')

    def _on_chip_click(event):
        print('[inter] clicked chip')
        ax, x, y = event.inaxes, event.xdata, event.ydata
        if ih.clicked_outside_axis(event):
            if not ischild:
                print('... out of axis')
                mode_ptr[0] = (mode_ptr[0] + 1) % 3
                _chip_view(**kwargs)
        else:
            if event.button == 3:   # right-click
                import guitool
                #from ibeis.viz.interact import interact_chip
                height = fig.canvas.geometry().height()
                qpoint = guitool.newQPoint(event.x, height - event.y)
                refresh_func = partial(_chip_view, **kwargs)

                callback_list = build_annot_context_options(
                    ibs, aid, refresh_func=refresh_func,
                    with_interact_chip=False,
                    config2_=config2_)
                qwin = fig.canvas
                guitool.popup_menu(qwin, qpoint, callback_list)
                #interact_chip.show_annot_context_menu(
                #    ibs, aid, fig.canvas, qpoint, refresh_func=refresh_func,
                #    with_interact_chip=False, config2_=config2_)
            else:
                viztype = vh.get_ibsdat(ax, 'viztype')
                print('[ic] viztype=%r' % viztype)
                if viztype == 'chip' and event.key == 'shift':
                    _chip_view(**kwargs)
                    ih.disconnect_callback(fig, 'button_press_event')
                elif viztype == 'chip':
                    kpts = ibs.get_annot_kpts(aid, config2_=config2_)
                    if len(kpts) > 0:
                        fx = vt.nearest_point(
                            x, y, kpts, conflict_mode='next')[0]
                        print('... clicked fx=%r' % fx)
                        _select_fxth_kpt(fx)
                    else:
                        print('... len(kpts) == 0')
                elif viztype in ['warped', 'unwarped']:
                    fx = vh.get_ibsdat(ax, 'fx')
                    if fx is not None and viztype == 'warped':
                        viz.show_keypoint_gradient_orientations(
                            ibs, aid, fx, fnum=df2.next_fnum())
                else:
                    print('...Unknown viztype: %r' % viztype)

        viz.draw()

    # Draw without keypoints the first time
    if fx is not None:
        _select_fxth_kpt(fx)
    else:
        _chip_view(**kwargs)
    if dodraw:
        viz.draw()

    if not ischild:
        ih.connect_callback(fig, 'button_press_event', _on_chip_click)


if __name__ == '__main__':
    """
    CommandLine:
        python -m ibeis.viz.interact.interact_chip
        python -m ibeis.viz.interact.interact_chip --allexamples
    """
    import multiprocessing
    multiprocessing.freeze_support()  # for win32
    import utool as ut  # NOQA
    ut.doctest_funcs()
