"""Load contestants from winners.csv and attach profile avatars from raw scrape data."""

from pathlib import Path

import pandas as pd

WINNERS_PATH = Path(__file__).parent / "winners.csv"
FB_RAW_PATH = Path(__file__).parent / "facebook_raw.csv"
IG_RAW_PATH = Path(__file__).parent / "instagram_raw.csv"
EXCLUDED_USERNAMES = {"adamelhelou", "سمير الليثى"}


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
                return pic.strip()
        return ""

    rows = fb[fb["profileName"] == username]
    if not rows.empty:
        pic = rows.iloc[0].get("profilePicture")
        if isinstance(pic, str) and pic.strip():
            return pic.strip()
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
