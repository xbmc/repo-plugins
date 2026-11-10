"""eBiblioCat's service API. Loan creation is never automatically retried."""

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlencode

import xbmcvfs

from resources.lib.ebibliocat import http as HTTP
from resources.lib.ebibliocat.cache import Cache
from resources.lib.ebibliocat.errors import Cancelled, EfilmError
from resources.lib.ebibliocat.storage import file_lock, read_json, write_json
from resources.lib.ebibliocat.validation import (
    active_loan,
    object_response,
    page_response,
    positive_id,
    products_response,
    valid_id,
    valid_product,
    valid_page,
)

API_BASE = "https://backend-prod.efilm.online/api/v1/"
WEB_BASE = "https://ebibliocat.efilm.info/"
EBIBLIOCAT_CLIENT_ID = 5
DEFAULT_LOCALIZATION = {"codeCountry": "ES", "city": "", "test": 2}
MAX_PAGES = 1000


class EfilmSession:
    def __init__(self, addon, language="ca"):
        self.profile = xbmcvfs.translatePath(addon.getAddonInfo("profile"))
        self.session_path = str(Path(self.profile) / "session.json")
        self.access_token = None
        self._refresh_marker = None
        self.localization = dict(DEFAULT_LOCALIZATION)
        self.language = language if language in ("ca", "es", "en") else "ca"
        self.cache = Cache(self.profile, self.language)

    def set_localization_from_headers(self, headers):
        if isinstance(headers, dict):
            self.localization = {
                "codeCountry": headers.get("cloudfront-viewer-country") or "ES",
                "city": headers.get("cloudfront-viewer-city") or headers.get("x-open-next-city") or "",
                "test": 2,
            }

    def _load_session(self):
        value = read_json(self.session_path, {})
        if not isinstance(value, dict):
            return {}
        refresh = value.get("refresh")
        if not isinstance(refresh, str) or not refresh:
            return {}
        loans = value.get("loans")
        loans = (
            {
                str(key): positive_id(value)
                for key, value in loans.items()
                if valid_id(key) and valid_id(value)
            }
            if isinstance(loans, dict)
            else {}
        )
        return {"refresh": refresh, "loans": loans}

    def _load_refresh_token(self):
        return self._load_session().get("refresh")

    def has_session(self):
        return bool(self._load_refresh_token())

    def _save_session(self, refresh_token=None, loans=None):
        with file_lock(self.profile, "session"):
            current = self._load_session()
            refresh = refresh_token if refresh_token is not None else current.get("refresh")
            if not isinstance(refresh, str) or not refresh:
                raise EfilmError("session_expired")
            write_json(
                self.session_path,
                {
                    "refresh": refresh,
                    "loans": current.get("loans", {}) if loans is None else loans,
                },
            )

    def clear(self):
        with file_lock(self.profile, "auth"), file_lock(self.profile, "session"):
            self.access_token = None
            self._refresh_marker = None
            try:
                os.unlink(self.session_path)
            except FileNotFoundError:
                pass
            except OSError as error:
                raise EfilmError("storage_error") from error

    def login(self, username, password):
        with file_lock(self.profile, "auth"):
            response = object_response(
                self._request(
                    "POST",
                    "auth/",
                    {
                        "id_client": EBIBLIOCAT_CLIENT_ID,
                        "username": username,
                        "password": password,
                    },
                )
            )
            access, refresh = response.get("access"), response.get("refresh")
            if not isinstance(access, str) or not access or not isinstance(refresh, str) or not refresh:
                raise EfilmError("invalid_response")
            self._save_session(refresh, {})
            self.access_token, self._refresh_marker = access, refresh

    def _request(self, method, path, payload=None, access_token=None):
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": WEB_BASE.rstrip("/"),
            "Accept-Language": self.language,
            "localization": json.dumps(self.localization, separators=(",", ":")),
        }
        if access_token:
            headers["Authorization"] = "JWT " + access_token
        return HTTP.request(API_BASE + path, method, payload, headers)

    def _refresh_access_token(self):
        # Caller holds the cross-process auth lock through request and persistence.
        refresh = self._load_refresh_token()
        if not refresh:
            raise EfilmError("session_expired")
        try:
            response = object_response(self._request("POST", "auth/refresh/", {"refresh": refresh}))
        except EfilmError as error:
            if error.status in (400, 401):
                # Do not call clear(): it would reacquire the auth lock.
                with file_lock(self.profile, "session"):
                    try:
                        os.unlink(self.session_path)
                    except FileNotFoundError:
                        pass
                raise EfilmError("session_expired", status=error.status) from None
            raise
        access = response.get("access")
        rotated = response.get("refresh", refresh)
        if not isinstance(access, str) or not access or not isinstance(rotated, str) or not rotated:
            raise EfilmError("invalid_response")
        self._save_session(rotated)
        self.access_token, self._refresh_marker = access, rotated

    def _authorized_request(self, method, path, payload=None):
        with file_lock(self.profile, "auth"):
            refresh = self._load_refresh_token()
            if not refresh:
                raise EfilmError("session_expired")
            if not self.access_token or refresh != self._refresh_marker:
                self._refresh_access_token()
            try:
                return self._request(method, path, payload, self.access_token)
            except EfilmError as error:
                if error.status != 401:
                    raise
                # An explicit unauthorized response has no successful loan side effect.
                self._refresh_access_token()
                return self._request(method, path, payload, self.access_token)

    def _pages(self, path, params=None, authorized=False):
        params = dict(params or {}, page_size=100)
        seen_pages = set()
        for page in range(1, MAX_PAGES + 1):
            query = urlencode(dict(params, page=page))
            fetch = self._authorized_request if authorized else self._request
            result = fetch("GET", path + "?" + query)
            if isinstance(result, list):
                yield from result
                return
            rows, following = page_response(result)
            signature = json.dumps(rows, sort_keys=True)
            if following and (not rows or signature in seen_pages):
                raise EfilmError("invalid_response")
            seen_pages.add(signature)
            yield from rows
            if not following:
                return
        raise EfilmError("invalid_response")

    def visible_lists(self):
        def load():
            return [
                x
                for x in self._pages(
                    "products/visible-lists/",
                    {
                        "visible": "true",
                        "elements_page_size": 1,
                        "order_by": "name,id",
                    },
                )
                if isinstance(x, dict)
            ]

        return self.cache.get(
            "lists", load, lambda v: isinstance(v, list) and all(isinstance(x, dict) for x in v)
        )

    def list_elements(self, list_id, page=1):
        result = self._request(
            "GET",
            "products/lists/{}/elements-by-id/?{}".format(
                positive_id(list_id), urlencode({"page_size": 24, "page": positive_id(page)})
            ),
        )
        page_response(result)
        return result

    def series(self, page=1):
        page = positive_id(page)

        def load():
            value = self._request("GET", "videos/series/?visible=true&page_size=24&page=" + str(page))
            page_response(value)
            return value

        return self.cache.get("series-" + str(page), load, valid_page)

    def series_detail(self, series_id):
        series_id = positive_id(series_id)

        def valid(value):
            return (
                isinstance(value, dict)
                and valid_id(value.get("id"))
                and int(value["id"]) == series_id
                and isinstance(value.get("seasons"), list)
            )

        return self.cache.get(
            "show-" + str(series_id),
            lambda: self._request("GET", "products/collections/{}/".format(series_id)),
            valid,
        )

    def genres(self):
        return self.cache.get(
            "genres",
            lambda: self._request("GET", "products/genres/audiovisual-available/"),
            lambda v: isinstance(v, list)
            and all(
                isinstance(g, dict) and valid_id(g.get("id")) and isinstance(g.get("name"), str) for g in v
            ),
        )

    def movies(self, refresh=False, progress=None, cancelled=None):
        def check_cancelled():
            if cancelled and cancelled():
                raise Cancelled()

        def fetch(page):
            check_cancelled()
            result = self._request(
                "GET",
                "products/products/relevant/?"
                + urlencode(
                    {
                        "skip_chapters": "true",
                        "page_size": 200,
                        "page": page,
                        "fields": "id,name,slug,cover,genres,type,duration,year,description",
                    }
                ),
            )
            page_response(result)
            return result

        def load():
            first = fetch(1)
            try:
                total = positive_id(first["total_pages"])
            except (KeyError, TypeError, ValueError):
                if first.get("count") == 0 and first.get("results") == []:
                    total = 1
                else:
                    raise EfilmError("invalid_response") from None
            if total > MAX_PAGES:
                raise EfilmError("invalid_response")
            products = list(first["results"])
            completed = 1
            if progress:
                progress(completed, total)
            # Submit one bounded batch at a time; cancellation never leaves hundreds queued.
            with ThreadPoolExecutor(max_workers=4) as executor:
                for start in range(2, total + 1, 4):
                    check_cancelled()
                    pending = [executor.submit(fetch, p) for p in range(start, min(start + 4, total + 1))]
                    for future in as_completed(pending):
                        check_cancelled()
                        products.extend(future.result()["results"])
                        completed += 1
                        if progress:
                            progress(completed, total)
            # Fail rather than save a silently truncated/repeated-page catalog.
            count = first.get("count")
            if count is not None and (
                isinstance(count, bool) or not isinstance(count, int) or count < 0 or count != len(products)
            ):
                raise EfilmError("invalid_response")
            valid = [p for p in products if valid_product(p)]
            usable = {str(p["id"]): p for p in valid}
            if len(usable) != len(valid) or (products and not usable):
                raise EfilmError("invalid_response")
            return list(usable.values())

        return self.cache.get(
            "movies", load, products_response, ttl=21600, force=refresh, cancelled=cancelled
        )

    def loan_guard(self, product_id):
        return file_lock(self.profile, "loan-" + str(positive_id(product_id)), timeout=120)

    def save_loan(self, product_id, loan_id):
        with file_lock(self.profile, "session"):
            current = self._load_session()
            if not current:
                raise EfilmError("session_expired")
            loans = current["loans"]
            key = str(positive_id(product_id))
            if loan_id is None:
                loans.pop(key, None)
            else:
                loans[key] = positive_id(loan_id)
            write_json(self.session_path, current)

    def find_active_loan(self, product_id):
        product_id = positive_id(product_id)
        match = None
        for loan in self._pages("loans/loans/actives/", authorized=True):
            if (
                not isinstance(loan, dict)
                or not valid_id(loan.get("id"))
                or not valid_id(loan.get("product"))
            ):
                raise EfilmError("invalid_response")
            if active_loan(loan) and int(loan["product"]) == product_id:
                match = positive_id(loan["id"])
                break
        self.save_loan(product_id, match)
        return match

    def make_loan(self, product_id):
        product_id = positive_id(product_id)
        try:
            result = object_response(
                self._authorized_request(
                    "POST",
                    "loans/loans/",
                    {
                        "product": product_id,
                        "localization": self.localization,
                    },
                )
            )
            loan = object_response(result.get("loan", result))
            if not valid_id(loan.get("id")):
                raise EfilmError("invalid_response", uncertain=True)
        except EfilmError as error:
            if error.uncertain or error.status == 409 or error.message == "invalid_response":
                # Reconcile once with a read. Never repeat the POST after an uncertain outcome.
                try:
                    recovered = self.find_active_loan(product_id)
                except EfilmError:
                    recovered = None
                if recovered:
                    return {"id": recovered}
                raise EfilmError("borrow_uncertain", uncertain=True) from None
            raise
        # A disk failure here must not lead to another POST on the next invocation.
        self.save_loan(product_id, loan["id"])
        return loan

    def get_playback(self, loan_id, language_id, subtitle_id):
        return self._authorized_request(
            "POST",
            "loans/displays/",
            {
                "loan": positive_id(loan_id),
                "language": positive_id(language_id),
                "subtitle": positive_id(subtitle_id),
                "localization": self.localization,
            },
        )
