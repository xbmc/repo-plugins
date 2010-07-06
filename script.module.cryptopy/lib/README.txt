
CryptoPy
--------

This is a pure Python implementation of various cryptographic algorithms.
The goal of the package is to provide human readable code for the algorithms
that closely matches the style and content of the technicla specifications.
The is intended as a reference implementation and is likely much slower than
speed optimized versions.

INSTALLATION
------------

You can use distutils to install CryptoPy by just typing:

$  setup.py install

This should work on Unix and Microsoft Windows. Alternatively you can
install by hand:

SOurce distribution is created by:

$  setup.py sdist --formats=gztar --force-manifest

OPERATION
---------

The test rountines can be run from the command line.

From the installed directory (typically .../python/Lib/site-packages
->  ./ieee_802/ccm_examples.py
->  ./crypto/cipher/ccm_test.py

Just run the scripts:
>>python ccm_examples.py
>>python ccm_test.py

etc.

CHANGES
---------

See CHANGES.txt

FEED BACK
---------

send to nymble@users.sourceforge.net



