"""CLI script to scrape comments and extract correct score guesses."""

import pandas as pd

from apify_fetch import fetch_facebook_comments, fetch_instagram_comments
from filtering import (
    build_contestants,
    normalize_facebook_df,
    normalize_instagram_df,
)

FB_URL = "https://www.facebook.com/share/p/1JEXadnG8f/"
IG_URL = "https://www.instagram.com/p/DafbvzHoEd1/"
EGYPT_SCORE = "2"
ARG_SCORE = "3"
FB_LIMIT = 27000
IG_LIMIT = 800


def main() -> None:
    normalized_dfs: list[pd.DataFrame] = []

    print(f"Fetching up to {FB_LIMIT} Facebook comments...")
    fb_df = fetch_facebook_comments(FB_URL, max_comments=FB_LIMIT)
    print(f"Facebook: {len(fb_df)} comments retrieved.")
    fb_df.to_csv("facebook_raw.csv", index=False)
    normalized_dfs.append(normalize_facebook_df(fb_df))

    print(f"Fetching up to {IG_LIMIT} Instagram comments...")
    ig_df = fetch_instagram_comments(IG_URL, max_comments=IG_LIMIT)
    print(f"Instagram: {len(ig_df)} comments retrieved.")
    ig_df.to_csv("instagram_raw.csv", index=False)
    normalized_dfs.append(normalize_instagram_df(ig_df))

    winners_df, winner_count = build_contestants(
        normalized_dfs, EGYPT_SCORE, ARG_SCORE
    )
    winners_df.to_csv("winners.csv", index=False)

    print(f"\nFinal score: Egypt {EGYPT_SCORE} - Argentina {ARG_SCORE}")
    print(f"Total comments scraped: {len(fb_df) + len(ig_df)}")
    print(f"Unique correct guesses: {winner_count}")
    print("Saved: facebook_raw.csv, instagram_raw.csv, winners.csv")


if __name__ == "__main__":
    main()
