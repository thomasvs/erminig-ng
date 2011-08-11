# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

# fake out hildon

import sys

try:
    import hildon
except ImportError:
    sys.modules['hildon'] = sys.modules['sys']
