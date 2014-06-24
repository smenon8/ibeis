#!/usr/bin/env python2.7
# TODO: ADD COPYRIGHT TAG
from __future__ import absolute_import, division, print_function
from ibeis.dev import ibsfuncs
#from itertools import izip
# Python
import multiprocessing
#import numpy as np
from uuid import UUID
# Tools
import utool
from ibeis.control.IBEISControl import IBEISController
print, print_, printDBG, rrr, profile = utool.inject(__name__, '[TEST_UUID]')
from vtool import image
from ibeis.model.preproc import preproc_image

def TEST_ENCOUNTERS(ibs):
    print('[TEST_UUID]')
    img = image.imread('/home/hendrik/Pictures/ysbeer.jpg')
    uuid = preproc_image.get_image_uuid(img)
    uuid2 = UUID('cf55d6e3-908f-ac6c-9a5c-cd350f3e5682')
    print('uuid = %r' % uuid)
    print('uuid2 = %r' % uuid2)
    assert uuid == uuid2, 'uuid and uuid2 do not match'
    return locals()


if __name__ == '__main__':
    multiprocessing.freeze_support()  # For windows
    import ibeis
    main_locals = ibeis.main(defaultdb='testdb1', gui=False)
    ibs = main_locals['ibs']
    test_locals = utool.run_test(TEST_ENCOUNTERS, ibs)
    execstr = utool.execstr_dict(test_locals, 'test_locals')
    exec(execstr)
