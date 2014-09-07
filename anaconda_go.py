
# Copyright (C) 2014 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

"""AnacondaGO is a Go linting/autocompleter/IDE for Sublime Text 3
"""

from .plugin_version import anaconda_required_version, ver

from .anaconda_lib.golang import detector
from .anaconda_lib.anaconda_plugin import anaconda_version

if anaconda_required_version > anaconda_version:
    raise RuntimeError(
        'AnacondaGO requires version {} or better of anaconda but {} '
        'is installed'.format(
            '.'.join(str(i) for i in anaconda_required_version), ver
        )
    )


def plugin_loaded():
    """Sublime Text 3 calls this function automatically after load the plugin
    """

    detector.init()