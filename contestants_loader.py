"""Load contestants from winners.csv and attach profile avatars from raw scrape data."""

from pathlib import Path

import pandas as pd

WINNERS_PATH = Path(__file__).parent / "winners.csv"
FB_RAW_PATH = Path(__file__).parent / "facebook_raw.csv"
IG_RAW_PATH = Path(__file__).parent / "instagram_raw.csv"
EXCLUDED_USERNAMES = {"adamelhelou"}


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
        avatar = row.get("avatar_url", "")
        if not isinstance(avatar, str) or not avatar.strip():
            avatar = _lookup_avatar(username, source, fb, ig)

        contestants.append(
            {
                "username": username,
                "comment": str(row.get("comment", "")),
                "profile_url": str(row.get("profile_url", "")),
                "source": source,
                "avatar_url": avatar if isinstance(avatar, str) else "",
            }
        )
    return contestants


def save_enriched_winners() -> int:
    """Write avatar_url column back to winners.csv."""
    contestants = load_contestants()
    if not contestants:
        return 0

    df = pd.DataFrame(contestants)
    df.to_csv(WINNERS_PATH, index=False, encoding="utf-8-sig")
    return len(df)
