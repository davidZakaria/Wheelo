import os
from pathlib import Path

import pandas as pd
from apify_client import ApifyClient

SECRETS_PATH = Path(__file__).parent / ".streamlit" / "secrets.toml"


def get_apify_token() -> str:
    token = os.environ.get("APIFY_TOKEN")
    if not token and SECRETS_PATH.exists():
        for line in SECRETS_PATH.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("APIFY_TOKEN"):
                token = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
    if not token:
        try:
            import streamlit as st

            token = st.secrets["APIFY_TOKEN"]
        except Exception:
            token = None
    if not token:
        raise ValueError(
            "Apify API token not found. Copy .streamlit/secrets.toml.example to "
            ".streamlit/secrets.toml and add your APIFY_TOKEN, or set the "
            "APIFY_TOKEN environment variable."
        )
    return token


def get_apify_client() -> ApifyClient:
    return ApifyClient(get_apify_token())


def _status(message: str) -> None:
    try:
        import streamlit as st
        if st.runtime.exists():
            st.info(message)
            return
    except Exception:
        pass
    print(message)


def _run_actor_and_fetch(
    client: ApifyClient,
    actor_id: str,
    run_input: dict,
    timeout_secs: int = 7200,
) -> pd.DataFrame:
    """Start actor asynchronously and wait for large scrapes."""
    run = client.actor(actor_id).start(
        run_input=run_input,
        timeout_secs=timeout_secs,
        memory_mbytes=2048,
    )
    finished_run = client.run(run["id"]).wait_for_finish(wait_secs=timeout_secs + 300)
    status = finished_run.get("status")
    if status != "SUCCEEDED":
        raise RuntimeError(
            f"Apify actor {actor_id} finished with status: {status}. "
            f"Run ID: {run['id']}"
        )
    items = client.dataset(finished_run["defaultDatasetId"]).list_items().items
    return pd.DataFrame(items)


def fetch_facebook_comments(post_url: str, max_comments: int = 30000) -> pd.DataFrame:
    client = get_apify_client()
    run_input = {
        "startUrls": [{"url": post_url}],
        "resultsLimit": max_comments,
        "viewOption": "RANKED_UNFILTERED",
    }

    _status(
        "Triggering Apify cloud scraper for Facebook... "
        "This might take 30-90 minutes for 27k comments."
    )
    return _run_actor_and_fetch(
        client,
        "apify/facebook-comments-scraper",
        run_input,
        timeout_secs=7200,
    )


def fetch_instagram_comments(post_url: str, max_comments: int = 30000) -> pd.DataFrame:
    client = get_apify_client()
    run_input = {
        "directUrls": [post_url],
        "resultsLimit": max_comments,
    }

    _status("Triggering Apify cloud scraper for Instagram...")
    return _run_actor_and_fetch(
        client,
        "apify/instagram-comment-scraper",
        run_input,
        timeout_secs=1800,
    )
