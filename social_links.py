"""Normalize Facebook/Instagram URLs for mobile app deep-linking."""

from urllib.parse import quote, unquote, urlparse, urlunparse


def _clean_url(url: str) -> str:
    if not isinstance(url, str):
        return ""
    cleaned = url.strip()
    if not cleaned:
        return ""
    parsed = urlparse(cleaned)
    if not parsed.scheme:
        cleaned = f"https://{cleaned.lstrip('/')}"
        parsed = urlparse(cleaned)
    path = quote(unquote(parsed.path), safe="/%")
    return urlunparse((parsed.scheme, parsed.netloc, path, parsed.params, parsed.query, parsed.fragment))


def facebook_mobile_url(url: str) -> str:
    cleaned = _clean_url(url)
    if not cleaned:
        return ""
    return (
        cleaned.replace("://www.facebook.com", "://m.facebook.com")
        .replace("://facebook.com", "://m.facebook.com")
        .replace("://web.facebook.com", "://m.facebook.com")
    )


def instagram_mobile_url(url: str) -> str:
    cleaned = _clean_url(url)
    if not cleaned:
        return ""
    return cleaned.replace("://www.instagram.com", "://instagram.com")


def prepare_social_url(url: str, source: str, username: str = "") -> str:
    """Return a mobile-friendly web URL used as the deep-link target."""
    cleaned = _clean_url(url)
    if not cleaned:
        if source == "Instagram" and username:
            return f"https://instagram.com/{username.lstrip('@')}/"
        return ""

    if source == "Instagram" or "instagram.com" in cleaned:
        return instagram_mobile_url(cleaned)
    if source == "Facebook" or "facebook.com" in cleaned:
        return facebook_mobile_url(cleaned)
    return cleaned

SOCIAL_OPEN_JS = """
function wheeloOpenSocialLink(event, url, source) {
  if (!url) return;
  event.preventDefault();
  const mobile = /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent || "");
  const fbUrl = url.replace(/:\\/\\/(www\\.)?facebook\\.com/i, "://m.facebook.com");
  const igUrl = url.replace(/:\\/\\/(www\\.)?instagram\\.com/i, "://instagram.com");

  if (!mobile) {
    window.open(url, "_blank", "noopener");
    return;
  }

  const isFacebook = source === "Facebook" || /facebook\\.com/i.test(url);
  const isInstagram = source === "Instagram" || /instagram\\.com/i.test(url);
  let appLink = "";
  let fallbackUrl = url;

  if (isFacebook) {
    const encoded = encodeURIComponent(fbUrl);
    fallbackUrl = fbUrl;
    appLink = /Android/i.test(navigator.userAgent)
      ? `intent://${fbUrl.replace(/^https?:\\/\\//, "")}#Intent;package=com.facebook.katana;scheme=https;S.browser_fallback_url=${encoded};end`
      : `fb://facewebmodal/f?href=${encoded}`;
  } else if (isInstagram) {
    const igPath = igUrl.replace(/^https?:\\/\\/(www\\.)?instagram\\.com\\//i, "");
    fallbackUrl = igUrl;
    appLink = `instagram://${igPath}`;
  } else {
    window.open(url, "_blank", "noopener");
    return;
  }

  const timer = setTimeout(() => window.open(fallbackUrl, "_blank", "noopener"), 1400);
  const clear = () => clearTimeout(timer);
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) clear();
  }, { once: true });
  window.location.href = appLink;
}
"""
