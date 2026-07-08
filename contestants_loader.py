"""Load contestants from winners.csv and attach profile avatars from raw scrape data."""

import ast
import re
from pathlib import Path

import pandas as pd

WINNERS_PATH = Path(__file__).parent / "winners.csv"
FB_RAW_PATH = Path(__file__).parent / "facebook_raw.csv"
IG_RAW_PATH = Path(__file__).parent / "instagram_raw.csv"
EXCLUDED_USERNAMES = {"adamelhelou", "سمير الليثى"}
AVATAR_SIZE = 320


def enhance_avatar_url(url: str, size: int = AVATAR_SIZE) -> str:
    """Request a larger CDN variant for Facebook thumbnails.

    Instagram CDN links only work at their original signed size (usually 150x150).
    Upscaling them returns 403, so those URLs are left unchanged.
    """
    if not isinstance(url, str) or not url.strip():
        return ""

    enhanced = url.strip()
    if "cdninstagram.com" in enhanced.lower():
        return re.sub(
            r"stp=dst-jpg_s\d+x\d+",
            "stp=dst-jpg_s150x150",
            enhanced,
            flags=re.IGNORECASE,
        )

    size_tag = f"s{size}x{size}"

    enhanced = re.sub(r"ctp=[sp]\d+x\d+", f"ctp={size_tag}", enhanced, flags=re.IGNORECASE)
    enhanced = re.sub(
        r"stp=dst-jpg_s\d+x\d+",
        f"stp=dst-jpg_{size_tag}",
        enhanced,
        flags=re.IGNORECASE,
    )
    return enhanced


def _pick_row(rows: pd.DataFrame, comment: str) -> pd.Series:
    if rows.empty:
        return pd.Series(dtype=object)
    if comment:
        text_col = "text" if "text" in rows.columns else "comment"
        if text_col in rows.columns:
            exact = rows[rows[text_col].astype(str).str.strip() == comment.strip()]
            if not exact.empty:
                return exact.iloc[0]
    return rows.iloc[0]


def _lookup_avatar(username: str, source: str, fb: pd.DataFrame, ig: pd.DataFrame) -> str:
    if source == "Instagram":
        rows = ig[ig["ownerUsername"] == username]
        if not rows.empty:
            pic = rows.iloc[0].get("ownerProfilePicUrl")
            if isinstance(pic, str) and pic.strip():
                return enhance_avatar_url(pic.strip())
        return ""

    rows = fb[fb["profileName"] == username]
    if not rows.empty:
        row = rows.iloc[0]
        author_pic = _avatar_from_author(row.get("author"))
        if author_pic:
            return enhance_avatar_url(author_pic)
        pic = row.get("profilePicture")
        if isinstance(pic, str) and pic.strip():
            return enhance_avatar_url(pic.strip())
    return ""


def _avatar_from_author(author) -> str:
    if not isinstance(author, str) or not author.strip():
        return ""
    match = re.search(
        r"profile_picture_depth_0_increased['\"]:\s*\{[^}]*'uri':\s*'([^']+)'",
        author,
    )
    if match:
        return match.group(1)
    try:
        author_data = ast.literal_eval(author)
        increased = author_data.get("profile_picture_depth_0_increased", {})
        uri = increased.get("uri")
        if isinstance(uri, str) and uri.strip():
            return uri.strip()
        standard = author_data.get("profile_picture_depth_0", {})
        uri = standard.get("uri")
        if isinstance(uri, str) and uri.strip():
            return uri.strip()
    except (SyntaxError, ValueError):
        pass
    return ""


def _lookup_comment_url(username: str, comment: str, source: str, fb: pd.DataFrame, ig: pd.DataFrame) -> str:
    if source == "Instagram":
        rows = ig[ig["ownerUsername"] == username]
        row = _pick_row(rows, comment)
        url = row.get("commentUrl") if not row.empty else ""
        return url.strip() if isinstance(url, str) else ""

    rows = fb[fb["profileName"] == username]
    row = _pick_row(rows, comment)
    url = row.get("commentUrl") if not row.empty else ""
    return url.strip() if isinstance(url, str) else ""


def _resolve_profile_url(profile_url: str, comment_url: str) -> str:
    if isinstance(profile_url, str) and profile_url.strip():
        if "comment_id=" not in profile_url:
            return profile_url.strip()
    if isinstance(comment_url, str) and comment_url.strip():
        return ""
    return profile_url.strip() if isinstance(profile_url, str) else ""


def load_contestants() -> list[dict]:
    if not WINNERS_PATH.exists():
        return []

    winners = pd.read_csv(WINNERS_PATH)
    winners = winners[~winners["username"].isin(EXCLUDED_USERNAMES)]

    fb = pd.read_csv(FB_RAW_PATH) if FB_RAW_PATH.exists() else pd.DataFrame()
    ig = pd.read_csv(IG_RAW_PATH) if IG_RAW_PATH.exists() else pd.DataFrame()

    contestants: list[dict] = []
    for _, row in winners.iterrows():
        source = str(row.get("source", "Facebook"))
        username = str(row["username"])
        comment = str(row.get("comment", ""))
        avatar = row.get("avatar_url", "")
        if not isinstance(avatar, str) or not avatar.strip():
            avatar = _lookup_avatar(username, source, fb, ig)
        else:
            avatar = enhance_avatar_url(avatar)

        comment_url = row.get("comment_url", "")
        if not isinstance(comment_url, str) or not comment_url.strip():
            comment_url = _lookup_comment_url(username, comment, source, fb, ig)
        if not comment_url and isinstance(row.get("profile_url"), str) and "comment_id=" in row["profile_url"]:
            comment_url = row["profile_url"].strip()

        profile_url = _resolve_profile_url(str(row.get("profile_url", "")), comment_url)
        if not profile_url:
            if source == "Instagram":
                profile_url = f"https://www.instagram.com/{username.strip().lstrip('@')}/"
            else:
                profile_url = _lookup_profile_url_from_raw(username, source, fb, ig)

        contestants.append(
            {
                "username": username,
                "comment": comment,
                "profile_url": profile_url,
                "comment_url": comment_url if isinstance(comment_url, str) else "",
                "source": source,
                "avatar_url": avatar if isinstance(avatar, str) else "",
            }
        )
    return contestants


def _lookup_profile_url_from_raw(username: str, source: str, fb: pd.DataFrame, ig: pd.DataFrame) -> str:
    if source == "Instagram":
        return f"https://www.instagram.com/{username.strip().lstrip('@')}/"
    rows = fb[fb["profileName"] == username]
    if rows.empty:
        return ""
    profile_url = rows.iloc[0].get("profileUrl")
    if isinstance(profile_url, str) and profile_url.strip():
        return profile_url.strip()
    return f"https://www.facebook.com/{username}"


def save_enriched_winners() -> int:
    """Write avatar_url and comment_url columns back to winners.csv."""
    contestants = load_contestants()
    if not contestants:
        return 0

    df = pd.DataFrame(contestants)
    df.to_csv(WINNERS_PATH, index=False, encoding="utf-8-sig")
    return len(df)
