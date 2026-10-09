import sys


def backend(file):
    return sys.modules[__name__]


def list_var(file):
    raise NotImplementedError


def list_img(file):
    raise NotImplementedError


def load_var(file, name):
    raise NotImplementedError


def load_img(file, name, roi=None):
    raise NotImplementedError


def meta_file(file):
    raise NotImplementedError


def meta_img(file, image):
    raise NotImplementedError
