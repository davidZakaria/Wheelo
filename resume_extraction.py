"""Resume or monitor an existing Apify run and export winners."""

import sys

import pandas as pd

from apify_fetch import get_apify_client
from filtering import (
    build_contestants,
    normalize_facebook_df,
    normalize_instagram_df,
)

EGYPT_SCORE = "2"
ARG_SCORE = "3"


def fetch_dataset_from_run(run_id: str) -> pd.DataFrame:
    client = get_apify_client()
    run = client.run(run_id).wait_for_finish(wait_secs=7200)
    status = run.get("status")
    print(f"Run {run_id} finished with status: {status}")
    if status != "SUCCEEDED":
        raise RuntimeError(f"Run failed with status: {status}")
    items = client.dataset(run["defaultDatasetId"]).list_items().items
    return pd.DataFrame(items)


def main() -> None:
    normalized_dfs: list[pd.DataFrame] = []

    if len(sys.argv) > 1:
        run_id = sys.argv[1]
        print(f"Waiting for existing Facebook run: {run_id}")
        fb_df = fetch_dataset_from_run(run_id)
    else:
        from apify_fetch import fetch_facebook_comments, fetch_instagram_comments

        FB_URL = "https://www.facebook.com/share/p/1JEXadnG8f/"
        IG_URL = "https://www.instagram.com/p/DafbvzHoEd1/"

        print("Fetching Instagram comments (800)...")
        ig_df = fetch_instagram_comments(IG_URL, max_comments=800)
        ig_df.to_csv("instagram_raw.csv", index=False)
        print(f"Instagram: {len(ig_df)} comments.")
        normalized_dfs.append(normalize_instagram_df(ig_df))

        print("Fetching Facebook comments (27000)...")
        fb_df = fetch_facebook_comments(FB_URL, max_comments=27000)

    fb_df.to_csv("facebook_raw.csv", index=False)
    print(f"Facebook: {len(fb_df)} comments.")
    normalized_dfs.append(normalize_facebook_df(fb_df))

    if len(normalized_dfs) == 1:
        from apify_fetch import fetch_instagram_comments

        IG_URL = "https://www.instagram.com/p/DafbvzHoEd1/"
        print("Fetching Instagram comments (800)...")
        ig_df = fetch_instagram_comments(IG_URL, max_comments=800)
        ig_df.to_csv("instagram_raw.csv", index=False)
        normalized_dfs.insert(0, normalize_instagram_df(ig_df))

    winners_df, winner_count = build_contestants(
        normalized_dfs, EGYPT_SCORE, ARG_SCORE
    )
    winners_df.to_csv("winners.csv", index=False)

    print(f"\nFinal score: Egypt {EGYPT_SCORE} - Argentina {ARG_SCORE}")
    print(f"Unique correct guesses: {winner_count}")
    print("Saved: facebook_raw.csv, instagram_raw.csv, winners.csv")


if __name__ == "__main__":
    main()
