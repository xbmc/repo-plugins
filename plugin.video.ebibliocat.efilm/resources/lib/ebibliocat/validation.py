"""Small explicit schema checks for data returned by an external service."""

from datetime import datetime, timezone

from resources.lib.ebibliocat.errors import EfilmError


def positive_id(value):
    if isinstance(value, bool):
        raise ValueError("invalid ID")
    number = int(value)
    if number <= 0 or str(number) != str(value):
        raise ValueError("invalid ID")
    return number


def valid_id(value):
    try:
        positive_id(value)
        return True
    except (ValueError, TypeError, OverflowError):
        return False


def object_response(value):
    if not isinstance(value, dict):
        raise EfilmError("invalid_response")
    return value


def page_response(value):
    value = object_response(value)
    if not isinstance(value.get("results"), list):
        raise EfilmError("invalid_response")
    links = value.get("links", {})
    if not isinstance(links, dict):
        raise EfilmError("invalid_response")
    following = links.get("next", value.get("next"))
    if following is not None and not isinstance(following, str):
        raise EfilmError("invalid_response")
    return value["results"], bool(following)


def valid_page(value):
    try:
        page_response(value)
        return True
    except EfilmError:
        return False


def products_response(value):
    if not isinstance(value, list):
        return False
    return all(
        isinstance(p, dict)
        and valid_id(p.get("id"))
        and isinstance(p.get("name"), str)
        and p["name"].strip()
        and isinstance(p.get("slug"), str)
        and p["slug"]
        and isinstance(p.get("type"), str)
        and isinstance(p.get("genres", []), list)
        for p in value
    )


def valid_product(value):
    return products_response([value])


def active_loan(loan):
    if not isinstance(loan, dict) or not valid_id(loan.get("id")):
        return False
    if loan.get("enabled") is not None and not isinstance(loan["enabled"], bool):
        raise EfilmError("invalid_response")
    if loan.get("enabled") is False:
        return False
    expiry = loan.get("expire")
    if expiry:
        try:
            expires = datetime.fromisoformat(str(expiry).replace("Z", "+00:00"))
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            return expires > datetime.now(timezone.utc)
        except (ValueError, TypeError):
            raise EfilmError("invalid_response") from None
    return True
