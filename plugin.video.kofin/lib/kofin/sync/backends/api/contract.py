"""Pure public-interface floor and feature probes; behavioural qualification
is separate.

The baseline is what every Kodi the build installs on offers (Piers 22.0
onwards): a Kodi short of it keeps native sync off and the report says why.
A *feature* is what a newer Kodi may offer beyond it, named so the rest of
the add-on can ask for it by name (``capabilities.features``): each is a set
of probes of the same kinds the baseline uses -- a JSON-RPC method and its
parameters, the values of a field enum, a Python method on an info tag or a
stream detail class, a system add-on's version -- and is on only while every
probe passes. Two features stand for behaviour Kodi cannot be asked about
and are probed by proxy, named in ``requirements.json``: ``asset_clean``
(kontell/xbmc #1, #2 and #10, by the ``xbmc.python`` version the change set
raises) and ``tempo`` (the tempo set, by the ``correction`` flag #38 adds to
``Player.SetTempo``).
"""

from typing import Any


def version(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in value.split("."))


def _check_addons(
    capture: dict[str, Any], addons: dict[str, str], errors: list[str]
) -> None:
    for addon, minimum in addons.items():
        try:
            adequate = version(
                capture.get("system_addons", {}).get(addon, "0")
            ) >= version(minimum)
        except ValueError:
            adequate = False
        if not adequate:
            errors.append(addon + " >= " + minimum + " is required")


def _check_methods(
    capture: dict[str, Any], methods: dict[str, dict[str, Any]], errors: list[str]
) -> None:
    for method, parameters in methods.items():
        definition = capture.get("methods", {}).get(method)
        if definition is None:
            errors.append("missing method " + method)
            continue
        actual = {param["name"]: param for param in definition.get("params", [])}
        for name, required in parameters.items():
            if name not in actual:
                errors.append("missing parameter " + method + "." + name)
            elif required and not set(required).issubset(actual[name].get("enums", [])):
                errors.append("missing enum values " + method + "." + name)


def _check_python(
    capture: dict[str, Any], python: dict[str, list[str]], errors: list[str]
) -> None:
    for field, methods in python.items():
        for method in methods:
            if capture.get(field, {}).get(method) is not True:
                errors.append("missing Python capability " + field + "." + method)


def _check_fields(
    capture: dict[str, Any], fields: dict[str, list[str]], errors: list[str]
) -> None:
    """A value a field enum must list: a property a readback may ask for
    only while Kodi names it, since an unknown one fails the whole call."""
    for type_name, values in fields.items():
        items = capture.get("types", {}).get(type_name, {}).get("items", {})
        enums = items.get("enums") or items.get("enum") or []
        for value in values:
            if value not in enums:
                errors.append("missing field " + type_name + "." + value)


def check(
    capture: dict[str, Any], contract: dict[str, Any], allow_dirty: bool = False
) -> dict[str, Any]:
    capture = capture.get("result", capture)
    errors: list[str] = []
    application = capture.get("application", {}).get("version", {})
    if application.get("major", 0) < contract["minimum_kodi_major"]:
        errors.append("Kodi %d or later is required" % contract["minimum_kodi_major"])
    _check_addons(capture, contract["system_addons"], errors)
    # Build provenance is diagnostic only. A test build carries a dirty
    # revision; actual public capabilities decide whether sync can run.
    dirty = "dirty" in application.get("revision", "").lower()
    _check_methods(capture, contract["methods"], errors)
    _check_python(capture, contract["python"], errors)
    features: dict[str, bool] = {}
    missing: dict[str, list[str]] = {}
    for name, probes in contract.get("features", {}).items():
        reasons: list[str] = []
        _check_addons(capture, probes.get("system_addons", {}), reasons)
        _check_methods(capture, probes.get("methods", {}), reasons)
        _check_python(capture, probes.get("python", {}), reasons)
        _check_fields(capture, probes.get("fields", {}), reasons)
        features[name] = not reasons
        if reasons:
            missing[name] = reasons
    return {
        "interfaces_passed": not errors,
        "errors": errors,
        "features": features,
        "missing": missing,
        "build_is_dirty": dirty,
        "behavioral_qualification_required": True,
        "behavioral_gates": contract["behavioral_gates"],
    }
