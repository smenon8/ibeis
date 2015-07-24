# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
import utool
from utool.util_six import get_funcname
#import functools

# A list of registered development test functions
DEVCMD_FUNCTIONS = []
DEVPRECMD_FUNCTIONS = []


def devcmd(*args):
    """ Decorator which registers a function as a developer command """
    noargs = len(args) == 1 and not isinstance(args[0], str)
    if noargs:
        # Function is only argument
        func = args[0]
        func_aliases = []
    else:
        func_aliases = list(args)
    def closure_devcmd(func):
        global DEVCMD_FUNCTIONS
        func_aliases.extend([get_funcname(func)])
        DEVCMD_FUNCTIONS.append((tuple(func_aliases), func))
        def func_wrapper(*args_, **kwargs_):
            #if utool.VERBOSE:
            #if utool.QUIET:
            print('[DEVCMD] ' + utool.func_str(func, args_, kwargs_))
            return func(*args_, **kwargs_)
        return func_wrapper
    if noargs:
        return closure_devcmd(func)
    return closure_devcmd


def devprecmd(*args):
    """ Decorator which registers a function as a developer precommand """
    noargs = len(args) == 1 and not isinstance(args[0], str)
    if noargs:
        # Function is only argument
        func = args[0]
        func_aliases = []
    else:
        func_aliases = list(args)
    def closure_devprecmd(func):
        global DEVPRECMD_FUNCTIONS
        func_aliases.extend([get_funcname(func)])
        DEVPRECMD_FUNCTIONS.append((tuple(func_aliases), func))
        def func_wrapper(*args_, **kwargs_):
            #if utool.VERBOSE:
            #if utool.QUIET:
            print('[DEVPRECMD] ' + utool.func_str(func, args_, kwargs_))
            return func(*args_, **kwargs_)
        return func_wrapper
    if noargs:
        return closure_devprecmd(func)
    return closure_devprecmd