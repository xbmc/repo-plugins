import hashlib


def hashit(s):
    """Using our own wrapper against hash function
        @note: Md5 seem to be the fastest in hashlib
        We don't really need cryptographic algo but well dunnon what to use :)
    """
    m = hashlib.md5()
    m.update(s)
    return m.hexdigest()
