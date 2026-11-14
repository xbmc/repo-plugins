"""Unicode UI strings backed by Kodi localization resources."""

MESSAGES = {
    "all_movies": (30001, "All movies (A–Z)"),
    "genres": (30002, "Movies by genre"),
    "lists": (30003, "Lists"),
    "series": (30004, "Series"),
    "search": (30005, "Search movies"),
    "alphabet": (30006, "Browse A–Z"),
    "refresh": (30007, "Refresh catalog"),
    "clear_cache": (30008, "Clear catalog cache"),
    "login": (30009, "Sign in to eFilm"),
    "logout": (30010, "Sign out of eFilm"),
    # IDs 30011–30013 are retired. Keep all remaining IDs stable across updates.
    "username": (30014, "eFilm library username"),
    "password": (30015, "eFilm password"),
    "signed_in": (30016, "Signed in to eFilm."),
    "signed_out": (30017, "Signed out of eFilm."),
    "choose_tracks": (30018, "Choose audio and subtitles"),
    "borrow_title": (30019, "Borrow from eFilm"),
    "borrow_confirm": (30020, "Borrow {title}? This may use one of your available eFilm loans."),
    "resume_title": (30021, "Resume eFilm loan"),
    "resume_confirm": (30022, "Resume your existing loan for {title}?"),
    "cancel": (30023, "Cancel"),
    "borrow": (30024, "Borrow"),
    "resume": (30025, "Resume"),
    "next": (30026, "Next page"),
    "previous": (30027, "Previous page"),
    "season": (30028, "Season {number}"),
    "page": (30029, "Page {current} of {total} · {count} titles"),
    "loading": (30030, "Loading catalog…"),
    "loading_pages": (30031, "Loading page {current} of {total}"),
    "stale_cache": (30032, "eFilm is unavailable. Showing the saved catalog."),
    "cache_cleared": (30033, "Catalog cache cleared."),
    "catalog_refreshed": (30034, "Catalog refreshed."),
    "no_results": (30035, "No matching titles."),
    "popular": (30036, "Popular movies"),
    "noperdis": (30037, "Don’t miss"),
    "other_letters": (30038, "Numbers and symbols"),
    "unknown_route": (30039, "This link is no longer supported. Open the add-on home menu."),
    "session_expired": (30040, "Sign in to eFilm again."),
    "signin_failed": (30041, "Sign-in failed. Check your library username and password."),
    "network_error": (30042, "Could not connect to eFilm. Try again later."),
    "service_error": (30043, "eFilm could not complete the request. Try again later."),
    "access_denied": (30044, "eFilm denied access. Check your account, region, and loan limits."),
    "unavailable": (30045, "This title or loan is no longer available."),
    "loan_conflict": (30046, "Check your existing loans before borrowing again."),
    "rate_limited": (30047, "eFilm is receiving too many requests. Try again later."),
    "invalid_response": (30048, "eFilm returned an unexpected response. Please report the add-on version."),
    "storage_error": (30049, "Could not save or remove local data. Check storage space and permissions."),
    "busy": (30050, "Another add-on operation is still running. Try again shortly."),
    "cancelled": (30051, "Cancelled."),
    "borrow_uncertain": (
        30052,
        "The loan request could not be confirmed. Check your loans on eFilm before trying again.",
    ),
    "loan_rejected": (
        30053,
        "eFilm rejected the loan. Check your remaining credits, account eligibility, and content availability.",
    ),
    "no_tracks": (30054, "No compatible audio/subtitle tracks are available for this title."),
    "unsupported_stream": (
        30055,
        "This provider did not supply a supported stream. The loan may already have started.",
    ),
    "unsupported_drm": (30056, "This DRM format is not supported on this device."),
    "inputstream_missing": (
        30057,
        "Enable InputStream Adaptive under My add-ons → VideoPlayer InputStream, then try again.",
    ),
    "helper_missing": (30058, "Install InputStream Helper from the Kodi repository, then try again."),
    "drm_missing": (30059, "DRM playback prerequisites are unavailable or setup was cancelled."),
    "loan_expired": (30060, "The old loan is no longer active. Confirm a new loan to continue."),
    "loan_limit": (30061, "No eFilm loans remaining. Check your eFilm account for the renewal date."),
}


class EBiblioStrings:
    def __init__(self, addon):
        self.addon = addon

    def get(self, key, **values):
        code, fallback = MESSAGES.get(key, (0, MESSAGES["service_error"][1]))
        text = self.addon.getLocalizedString(code) if code else ""
        if not isinstance(text, str) or not text:
            text = fallback
        return text.format(**values) if values else text
