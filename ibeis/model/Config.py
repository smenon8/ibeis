from __future__ import absolute_import, division, print_function
import utool
import copy
(print, print_, printDBG, rrr, profile) = utool.inject(
    __name__, '[Config]', DEBUG=False)

ConfigBase = utool.Pref
#ConfigBase = utool.DynStruct
#ConfigBase = object


def make_feasible(query_cfg):
    """
    removes invalid parameter settings over all cfgs (move to QueryConfig)
    """
    filt_cfg = query_cfg.filt_cfg
    nn_cfg   = query_cfg.nn_cfg
    feat_cfg = query_cfg._feat_cfg

    # Ensure the list of on filters is valid given the weight and thresh
    if filt_cfg.ratio_thresh <= 1:
        filt_cfg.ratio_thresh = None
    if filt_cfg.bboxdist_thresh >= 1:
        filt_cfg.bboxdist_thresh = None
    if filt_cfg.bursty_thresh   <= 1:
        filt_cfg.bursty_thresh = None

    if feat_cfg.nogravity_hack is False:
        filt_cfg.gravity_weighting = False

    # normalizer rule depends on Knorm
    if nn_cfg.Knorm == 1:
        nn_cfg.normalizer_rule = 'last'


class NNConfig(ConfigBase):
    def __init__(nn_cfg, **kwargs):
        super(NNConfig, nn_cfg).__init__()
        nn_cfg.K = 4
        nn_cfg.Knorm = 1
        nn_cfg.normalizer_rule = ['last', 'name'][0]
        nn_cfg.checks  = 1024  # 512#128
        nn_cfg.update(**kwargs)

    def get_cfgstr_list(nn_cfg):
        nn_cfgstr  = ['_NN(',
                   'K', str(nn_cfg.K),
                   '+', str(nn_cfg.Knorm),
                   ',', nn_cfg.normalizer_rule,
                   ',cks', str(nn_cfg.checks),
                   ')']
        return nn_cfgstr

    def get_cfgstr(nn_cfg):
        return ''.join(nn_cfg.get_cfgstr_list())


class FilterConfig(ConfigBase):
    # Rename to scoring mechanism
    def __init__(filt_cfg, **kwargs):
        super(FilterConfig, filt_cfg).__init__(name='filt_cfg')
        filt_cfg = filt_cfg
        filt_cfg.filt_on = True
        filt_cfg.Krecip = 0  # 0 := off
        filt_cfg.can_match_sameimg = False
        filt_cfg.can_match_samename = True
        filt_cfg.gravity_weighting = False
        filt_cfg._valid_filters = []
        def addfilt(sign, filt, thresh, weight, depends=None):
            'dynamically adds filters'
            printDBG('[addfilt] %r %r %r %r' % (sign, filt, thresh, weight))
            filt_cfg._valid_filters.append(filt)
            filt_cfg[filt + '_thresh'] = None if thresh is None else float(thresh)
            filt_cfg[filt + '_weight'] = None if weight is None else float(weight)
            filt_cfg['_' + filt + '_depends'] = depends
            filt_cfg['_' + filt + '_sign'] = sign
        #tuple(Sign, Filt, ValidSignThresh, ScoreMetaWeight)
        # thresh test is: sign * score <= sign * thresh
        # sign +1 --> Lower scores are better
        # sign -1 --> Higher scores are better
        addfilt(+1, 'bboxdist',  None,   0.0)
        addfilt(-1,   'recip',   0.0,   0.0, 'filt_cfg.Krecip > 0')
        addfilt(+1,  'bursty',  None,   0.0)
        addfilt(-1,   'ratio',  None,   0.0)
        addfilt(-1,   'lnbnn',  None,   1.0)
        addfilt(-1,   'lnrat',  None,   0.0)
        #addfilt(+1, 'scale' )
        filt_cfg.update(**kwargs)

    def get_stw(filt_cfg, filt):
        # stw = sign, thresh, weight
        if not isinstance(filt, (str, unicode)):
            raise AssertionError('Global cache seems corrupted')
        sign   = filt_cfg['_' + filt + '_sign']
        thresh = filt_cfg[filt + '_thresh']
        weight = filt_cfg[filt + '_weight']
        if weight == 1.0:
            weight = 1.0
        return sign, thresh, weight

    def get_active_filters(filt_cfg):
        active_filters = []
        for filt in filt_cfg._valid_filters:
            sign, thresh, weight = filt_cfg.get_stw(filt)
            depends = filt_cfg['_' + filt + '_depends']
            # Check to make sure dependencies are satisfied
            # RCOS TODO FIXME: Possible security flaw.
            # This eval needs to be removed.
            # Need to find a better way of encoding dependencies
            assert depends is None or depends.find('(') == -1, 'unsafe dependency'
            depends_ok = depends is None or eval(depends)
            conditions_ok = thresh is not None or weight != 0
            if conditions_ok and depends_ok:
                active_filters.append(filt)
        return active_filters

    def get_cfgstr_list(filt_cfg):
        if not filt_cfg.filt_on:
            return ['_FILT()']
        on_filters = filt_cfg.get_active_filters()
        filt_cfgstr = ['_FILT(']
        stw_list = []
        # Create a cfgstr for each filter
        for filt in on_filters:
            sign, thresh, weight = filt_cfg.get_stw(filt)
            stw_str = filt
            if thresh is None and weight == 0:
                continue
            if thresh is not None:
                sstr = '>' if sign == -1 else '<'  # actually <=, >=
                stw_str += sstr + str(thresh)
            if weight != 0:
                stw_str += '_' + str(weight)
            stw_list.append(stw_str)
        stw_str = ','.join(stw_list)
        if filt_cfg.Krecip != 0 and 'recip' in on_filters:
            filt_cfgstr += ['Kr' + str(filt_cfg.Krecip)]
            if len(stw_str) > 0:
                filt_cfgstr += [',']
        if len(stw_str) > 0:
            filt_cfgstr += [stw_str]
        if filt_cfg.can_match_sameimg:
            filt_cfgstr += 'same_img'
        if not filt_cfg.can_match_samename:
            filt_cfgstr += 'notsame_name'
        if filt_cfg.gravity_weighting:
            filt_cfgstr += [',gvweight']
        filt_cfgstr += [')']
        return filt_cfgstr

    def get_cfgstr(filt_cfg):
        return ''.join(filt_cfg.get_cfgstr_list())


class SpatialVerifyConfig(ConfigBase):
    def __init__(sv_cfg, **kwargs):
        super(SpatialVerifyConfig, sv_cfg).__init__(name='sv_cfg')
        tau = 6.28  # 318530
        sv_cfg.ori_thresh   = tau / 4.0
        sv_cfg.scale_thresh = 2
        sv_cfg.xy_thresh = .01
        sv_cfg.nShortlist = 50
        sv_cfg.prescore_method = 'csum'
        sv_cfg.use_chip_extent = False
        sv_cfg.min_nInliers = 4
        sv_cfg.sv_on = True
        sv_cfg.update(**kwargs)

    def get_cfgstr_list(sv_cfg):
        if not sv_cfg.sv_on or sv_cfg.xy_thresh is None:
            return ['_SV()']
        sv_cfgstr = ['_SV(']
        sv_cfgstr += [str(sv_cfg.nShortlist)]
        thresh_tup = (sv_cfg.xy_thresh, sv_cfg.scale_thresh, sv_cfg.ori_thresh)
        thresh_str = utool.remove_chars(str(thresh_tup), ' ()').replace(',', '_')
        sv_cfgstr += [',' + thresh_str]
        sv_cfgstr += [',cdl' * sv_cfg.use_chip_extent]  # chip diag len
        sv_cfgstr += [',' + sv_cfg.prescore_method]
        sv_cfgstr += [')']
        return sv_cfgstr

    def get_cfgstr(sv_cfg):
        return ''.join(sv_cfg.get_cfgstr_list())


class AggregateConfig(ConfigBase):
    def __init__(agg_cfg, **kwargs):
        super(AggregateConfig, agg_cfg).__init__(name='agg_cfg')
        agg_cfg.query_type   = 'vsmany'
        # chipsum, namesum, placketluce
        agg_cfg.isWeighted = False  # nsum, pl
        agg_cfg.score_method = 'csum'  # nsum, pl
        alt_methods = {
            'topk': 'topk',
            'borda': 'borda',
            'placketluce': 'pl',
            'chipsum': 'csum',
            'namesum': 'nsum',
            'coverage': 'coverage',
        }
        # For Placket-Luce
        agg_cfg.max_alts = 50
        #-----
        # User update
        agg_cfg.update(**kwargs)
        # ---
        key = agg_cfg.score_method.lower()
        # Use w as a toggle for weighted mode
        if key.find('w') == len(key) - 1:
            agg_cfg.isWeighted = True
            key = key[:-1]
            agg_cfg.score_method = key
        # Sanatize the scoring method
        if key in alt_methods:
            agg_cfg.score_method = alt_methods[key]

    def get_cfgstr_list(agg_cfg):
        agg_cfgstr = []
        agg_cfgstr += ['_AGG(']
        agg_cfgstr += [agg_cfg.query_type]
        agg_cfgstr += [',', agg_cfg.score_method]
        if agg_cfg.isWeighted:
            agg_cfgstr += ['w']
        if agg_cfg.score_method  == 'pl':
            agg_cfgstr += [',%d' % (agg_cfg.max_alts,)]
        agg_cfgstr += [')']
        return agg_cfgstr

    def get_cfgstr(agg_cfg):
        return ''.join(agg_cfg.get_cfgstr_list())


class QueryConfig(ConfigBase):
    def __init__(query_cfg, feat_cfg=None, **kwargs):
        super(QueryConfig, query_cfg).__init__(name='query_cfg')
        query_cfg.nn_cfg   = NNConfig(**kwargs)
        query_cfg.filt_cfg = FilterConfig(**kwargs)
        query_cfg.sv_cfg   = SpatialVerifyConfig(**kwargs)
        query_cfg.agg_cfg  = AggregateConfig(**kwargs)
        query_cfg.use_cache = False
        query_cfg.num_results = 6
        # Depends on feature config
        if feat_cfg is None:
            query_cfg._feat_cfg = FeatureConfig(**kwargs)
        else:
            query_cfg._feat_cfg = feat_cfg
        query_cfg.update_query_cfg(**kwargs)

    def update_query_cfg(query_cfg, **kwargs):
        # Each config paramater should be unique
        # So updating them all should not cause conflicts
        query_cfg._feat_cfg.update(**kwargs)
        query_cfg._feat_cfg._chip_cfg.update(**kwargs)
        query_cfg.nn_cfg.update(**kwargs)
        query_cfg.filt_cfg.update(**kwargs)
        query_cfg.sv_cfg.update(**kwargs)
        query_cfg.agg_cfg.update(**kwargs)
        query_cfg.update(**kwargs)
        # Ensure feasibility of the configuration
        make_feasible(query_cfg)

    def deepcopy(query_cfg, **kwargs):
        copy_ = copy.deepcopy(query_cfg)
        copy_.update_query_cfg(**kwargs)
        return copy_

    def get_cfgstr_list(query_cfg, **kwargs):
        if query_cfg._feat_cfg is None:
            raise Exception('Feat / chip config is required')

        # Ensure feasibility of the configuration
        make_feasible(query_cfg)

        # Build cfgstr
        cfgstr_list = []
        if kwargs.get('use_nn', True):
            cfgstr_list += query_cfg.nn_cfg.get_cfgstr_list(**kwargs)
        if kwargs.get('use_filt', True):
            cfgstr_list += query_cfg.filt_cfg.get_cfgstr_list(**kwargs)
        if kwargs.get('use_sv', True):
            cfgstr_list += query_cfg.sv_cfg.get_cfgstr_list(**kwargs)
        if kwargs.get('use_agg', True):
            cfgstr_list += query_cfg.agg_cfg.get_cfgstr_list(**kwargs)
        if kwargs.get('use_chip', True):
            cfgstr_list += query_cfg._feat_cfg.get_cfgstr_list()
        return cfgstr_list

    def get_cfgstr(query_cfg, **kwargs):
        cfgstr_list = query_cfg.get_cfgstr_list(**kwargs)
        cfgstr = ''.join(cfgstr_list)
        return cfgstr

    # Comparison operators for sorting and uniqueness
    def __lt__(self, other):
        return self.__hash__() < (other.__hash__())

    def __le__(self, other):
        return self.__hash__() <= (other.__hash__())

    def __eq__(self, other):
        return self.__hash__() == (other.__hash__())

    def __ne__(self, other):
        return self.__hash__() != (other.__hash__())

    def __gt__(self, other):
        return self.__hash__() > (other.__hash__())

    def __ge__(self, other):
        return self.__hash__() >= (other.__hash__())

    def __hash__(self):
        return hash(self.get_cfgstr())


class FeatureConfig(ConfigBase):
    def __init__(feat_cfg, chip_cfg=None, **kwargs):
        super(FeatureConfig, feat_cfg).__init__(name='feat_cfg')
        feat_cfg.feat_type = 'hesaff+sift'
        feat_cfg.whiten = False
        feat_cfg.scale_min = 0  # 0  # 30 # TODO: Put in pref types here
        feat_cfg.scale_max = 9001  # 9001 # 80
        feat_cfg.use_adaptive_scale = False  # 9001 # 80
        feat_cfg.nogravity_hack = False  # 9001 # 80
        if chip_cfg is None:
            feat_cfg._chip_cfg = ChipConfig(**kwargs)
        else:
            feat_cfg._chip_cfg = chip_cfg  # Features depend on chips
        feat_cfg.update(**kwargs)

    def get_dict_args(feat_cfg):
        dict_args = {
            'scale_min': feat_cfg.scale_min,
            'scale_max': feat_cfg.scale_max,
            'use_adaptive_scale': feat_cfg.use_adaptive_scale,
            'nogravity_hack': feat_cfg.nogravity_hack,
        }
        return dict_args

    def get_cfgstr_list(feat_cfg):
        if feat_cfg._chip_cfg is None:
            raise Exception('Chip config is required')
        if feat_cfg.scale_min < 0:
            feat_cfg.scale_min = None
        if feat_cfg.scale_max < 0:
            feat_cfg.scale_max = None
        feat_cfgstrs = ['_FEAT(']
        feat_cfgstrs += [feat_cfg.feat_type]
        feat_cfgstrs += [',white'] * feat_cfg.whiten
        feat_cfgstrs += [',%r_%r' % (feat_cfg.scale_min, feat_cfg.scale_max)]
        feat_cfgstrs += [',adaptive'] * feat_cfg.use_adaptive_scale
        feat_cfgstrs += [',nogravity'] * feat_cfg.nogravity_hack
        feat_cfgstrs += [')']
        feat_cfgstrs += feat_cfg._chip_cfg.get_cfgstr_list()
        return feat_cfgstrs

    def get_cfgstr(feat_cfg):
        return ''.join(feat_cfg.get_cfgstr_list())


class ChipConfig(ConfigBase):
    def __init__(cc_cfg, **kwargs):
        super(ChipConfig, cc_cfg).__init__(name='chip_cfg')
        cc_cfg.chip_sqrt_area = 450
        cc_cfg.grabcut         = False
        cc_cfg.histeq          = False
        cc_cfg.adapteq         = False
        cc_cfg.region_norm     = False
        cc_cfg.rank_eq         = False
        cc_cfg.local_eq        = False
        cc_cfg.maxcontrast     = False
        cc_cfg.chipfmt         = '.png'
        cc_cfg.update(**kwargs)

    def get_cfgstr_list(cc_cfg):
        chip_cfgstr = []
        #assert cc_cfg.chipfmt[0] == '.'
        chip_cfgstr += [cc_cfg.chipfmt[1:].lower()] * (cc_cfg.chipfmt != '.png')
        chip_cfgstr += ['histeq']  * cc_cfg.histeq
        chip_cfgstr += ['adapteq'] * cc_cfg.adapteq
        chip_cfgstr += ['grabcut'] * cc_cfg.grabcut
        chip_cfgstr += ['regnorm'] * cc_cfg.region_norm
        chip_cfgstr += ['rankeq']  * cc_cfg.rank_eq
        chip_cfgstr += ['localeq'] * cc_cfg.local_eq
        chip_cfgstr += ['maxcont'] * cc_cfg.maxcontrast
        isOrig = cc_cfg.chip_sqrt_area is None or cc_cfg.chip_sqrt_area  <= 0
        chip_cfgstr += ['szorig'] if isOrig else ['sz%r' % cc_cfg.chip_sqrt_area]
        return ['_CHIP(', (','.join(chip_cfgstr)), ')']

    def get_cfgstr(cc_cfg):
        return ''.join(cc_cfg.get_cfgstr_list())


class DisplayConfig(ConfigBase):
    def __init__(display_cfg, **kwargs):
        super(DisplayConfig, display_cfg).__init__(name='display_cfg')
        display_cfg.N = 6
        display_cfg.name_scoring = False
        display_cfg.showanalysis = False
        display_cfg.annotations  = True
        display_cfg.vert = True  # None
        display_cfg.show_results_in_image = False  # None


class EncounterConfig(ConfigBase):
    valid_cluster_algos = ['meanshift', 'agglomerative']
    def __init__(enc_cfg, **kwargs):
        super(EncounterConfig, enc_cfg).__init__(name='enc_cfg')
        enc_cfg.min_imgs_per_encounter = 1
        #enc_cfg.cluster_algo = 'meanshift'  # [agglomerative]
        enc_cfg.cluster_algo = 'agglomerative'
        enc_cfg.quantile = .01  # depends meanshift
        enc_cfg.seconds_thresh = 60    # depends agglomerative
        enc_cfg.use_gps = False

    def get_cfgstr_list(enc_cfg):
        enc_cfgstrs = []
        if enc_cfg.cluster_algo == 'meanshift':
            enc_cfgstrs.append('ms')
            enc_cfgstrs.append('quant_%r' % enc_cfg.quantile)
        elif enc_cfg.cluster_algo == 'agglomerative':
            enc_cfgstrs.append('agg')
            enc_cfgstrs.append('sec_%r' % enc_cfg.seconds_thresh)
        if enc_cfg.use_gps:
            enc_cfgstrs.append('gps')
        
        enc_cfgstrs.append(str(enc_cfg.min_imgs_per_encounter))
        return ['_ENC(', ','.join(enc_cfgstrs), ')']

    def get_cfgstr(enc_cfg):
        return ''.join(enc_cfg.get_cfgstr_list())


class PreprocConfig(ConfigBase):
    def __init__(preproc_cfg, **kwargs):
        super(PreprocConfig, preproc_cfg).__init__(name='preproc_cfg')
        preproc_cfg.max_image_width  = 1000
        preproc_cfg.max_image_height = 1000

    def get_cfgstr_list(preproc_cfg):
        cfgstrs = []
        return ['_PREPROC(', ','.join(cfgstrs), ')']

    def get_cfgstr(preproc_cfg):
        return ''.join(preproc_cfg.get_cfgstr_list())


class DetectionConfig(ConfigBase):
    def __init__(guicfg, **kwargs):
        super(DetectionConfig, guicfg).__init__(name='detectcfg')
        guicfg.species     = 'zebra_grevys'
        guicfg.detector    = 'rf'


class OtherConfig(ConfigBase):
    def __init__(othercfg, **kwargs):
        super(OtherConfig, othercfg).__init__(name='othercfg')
        othercfg.thumb_size     = 64


# Convinience
def __dict_default_func(dict_):
    # Sets keys only if they dont exist
    def set_key(key, val):
        if key not in dict_:
            dict_[key] = val
    return set_key


def default_query_cfg(**kwargs):
    kwargs['query_type'] = 'vsmany'
    query_cfg = QueryConfig(**kwargs)
    return query_cfg


def default_vsone_cfg(ibs, **kwargs):
    kwargs['query_type'] = 'vsone'
    utool.dict_update_newkeys(kwargs, {
        'lnbnn_weight': 0.0,
        'checks': 256,
        'K': 1,
        'Knorm': 1,
        'ratio_weight': 1.0,
        'ratio_thresh': 1.5,
    })
    query_cfg = QueryConfig(**kwargs)
    return query_cfg
