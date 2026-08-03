
class ResponseParser:
    """Flattens the API's nested JSON into one row for the CSV."""

    CORE_KEYS = ["domain", "url", "response_url", "status_code", "scraped_at", "scrape_time", "emails_num", "phones_num", "social_num"]
    SOCIAL_KEYS = ["facebook", "instagram", "twitter", "linkedin", "youtube", "tiktok", "pinterest", "threads", "whatsapp", "telegram", "github", "reddit"]

    # Kept your exact _ACTIVE_PARSERS list as a class attribute
    _ACTIVE_PARSERS = []
    def __init__(self):
        self._ACTIVE_PARSERS = [self.parse_contact,  self.parse_profile,  self.parse_visuals,  self.parse_meta]

    def parse_contact(self, data: dict) -> dict:
        data = (data or {}).get("data", data) or {}
        contact = data.get("contact", {}) or {}
        social = contact.get("social", {}) or {}
        return {
            **{k: data.get(k) for k in self.CORE_KEYS},
            "emails": ", ".join(contact.get("emails") or []),
            "phones": ", ".join(contact.get("phones") or []),
            "original_phones": ", ".join(contact.get("original_phones") or []),
            **{k: social.get(k) for k in self.SOCIAL_KEYS},
            "social_all": ", ".join(contact.get("social_list") or []),
        }

    def parse_profile(self, data: dict) -> dict:
        profile  = data.get("profile", {}) or {}
        dates    = profile.get("dates", {}) or {}
        coords   = profile.get("coordinates", {}) or {}
        ratings  = profile.get("ratings", {}) or {}
        address  = next(iter(profile.get("addresses") or []), {}) or {}
        profile_keys = ["title", "site_name", "description", "language", "platform", "favicon", "h1", "h2", "h3"]
        address_keys = ["street", "city", "region", "postal_code", "country", "full"]
        return {
            **{k: profile.get(k) for k in profile_keys},
            "categories":          ", ".join(profile.get("categories") or []),
            "keywords":            ", ".join(profile.get("keywords") or []),
            "tags":                ", ".join(profile.get("tags") or []),
            **{f"address_{k}": address.get(k) for k in address_keys},
            "hours":               ", ".join(profile.get("hours") or []),
            "lat":                 coords.get("lat"),
            "lng":                 coords.get("lng"),
            "rating_value":        ratings.get("value"),
            "rating_count":        ratings.get("count"),
            "date_published":      dates.get("published"),
            "date_modified":       dates.get("modified"),
        }

    def parse_visuals(self, data: dict) -> dict:
        visuals = data.get("visuals", {}) or {}
        images_with_alt = visuals.get("images_with_alt") or []
        return {
            "logos":               ", ".join(visuals.get("logos") or []),
            "additional_logos":    ", ".join(visuals.get("additional_logos") or []),
            "og_image":            visuals.get("og_image"),
            "twitter_image":       visuals.get("twitter_image"),
            "images_with_alt_src": ", ".join(i.get("src", "") for i in images_with_alt if i.get("src")),
            "images_without_alt":  ", ".join(visuals.get("images_without_alt") or []),
        }

    def parse_meta(self, data: dict) -> dict:
        meta = data.get("meta", {}) or {}
        keys = ["has_privacy_policy", "has_terms", "has_blog", "has_careers", "has_pricing"]
        return {k: meta.get(k) for k in keys}

    def parse(self, json_data: dict, parse_mode: str = "raw") -> dict:
        data = json_data.get("data", json_data) if json_data else {}
        if parse_mode == "raw":
            return json_data
        if parse_mode == "contact":
            return self.parse_contact(data)
        if parse_mode == "full":
            return {k: v for parser in self._ACTIVE_PARSERS for k, v in parser(data).items()}

        raise ValueError(f"Invalid parse_mode: '{parse_mode}'. Choose from 'raw', 'contact', or 'full'.")

    def build_csv_fields(self) -> list[str]:
        return list(dict.fromkeys(
            key for parser in self._ACTIVE_PARSERS for key in parser({})
        ))
