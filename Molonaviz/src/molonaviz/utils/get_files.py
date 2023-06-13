"""
This file holds different methods to import or get files from the molonaviz package more easily.
"""

from pkg_resources import resource_filename

def get_docs(filename):
    """
    Get the corresponding image from the docs/ folder.
    Ex: get_docs(ERD.png)
    """
    return resource_filename("molonaviz.docs", filename)

def get_imgs(filename):
    """
    Get the corresponding image from the imgs/ folder.
    Ex: get_imgs(MolonavizIcon.png)
    """
    return resource_filename("molonaviz.imgs", filename)

def get_ui_asset(filename):
    """
    Get the corresponding image from the frontend/ui folder.
    """
    return resource_filename("molonaviz.frontend.ui", filename)

def get_interactions_asset(filename):
    """
    Get the corresponding image from the frontend/ui folder.
    """
    return resource_filename("molonaviz.interactions", filename)