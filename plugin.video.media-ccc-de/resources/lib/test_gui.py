from __future__ import print_function

from . import gui


def test_err(recwarn):
    gui.err("Some fatal error")
    assert len(recwarn) == 1
    w = recwarn.pop()
    assert issubclass(w.category, UserWarning)
    assert str(w.message) == "ERR: Some fatal error"


def test_info(recwarn):
    gui.info("Some information message")
    assert len(recwarn) == 1
    w = recwarn.pop()
    assert issubclass(w.category, UserWarning)
    assert str(w.message) == "INFO: Some information message"
