import ast
import re

import pandas as pd

COMMENT_ALIASES = ("text", "comment_text", "comment", "Comment", "Text")
USERNAME_ALIASES = (
    "username",
    "profileName",
    "ownerUsername",
    "user",
    "Username",
    "User",
    "name",
)

ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
SCORE_SEP = r"[-/:|،]"
SCORE_PAIR = rf"(\d+)\s*{SCORE_SEP}\s*(\d+)"

EGYPT_PATTERN = (
    r"(?:مصر|منتخبنا(?:\s+الوطن(?:ي|ى))?|الفراعنة|ام\s*الدنيا|منتخب\s+مصر|"
    r"المنتخب\s+المصري|المنتخب\s+الوطني|الوطن(?:ي|ى)|🇪🇬)"
)
ARG_PATTERN = (
    r"(?:الأرجنتين|الارجنتين|أرجنتين|ارجنتين|ارچنتين|الارچنتين|الارچنتيت|🇦🇷|argentina)"
)
FOR_EGYPT = rf"(?:لصالح\s+|لل\s*|ل\s*){EGYPT_PATTERN}"
FOR_ARG = rf"(?:لصالح\s+|لل\s*|ل\s*){ARG_PATTERN}"
PENALTY_PATTERN = r"(?:ضربات?\s*(?:ال)?جزاء|ركلات?\s*ترجيح)"
EGYPT_WIN_PATTERNS = (
    rf"فوز\s+{EGYPT_PATTERN}",
    rf"{SCORE_PAIR}\s*{FOR_EGYPT}",
    rf"{FOR_EGYPT}",
    rf"{EGYPT_PATTERN}\s+هت(?:فوز|كسب)",
    rf"ان\s*شاء?\s*الله\s+.*{EGYPT_PATTERN}",
    rf"{EGYPT_PATTERN}\s+ان\s*شاء?\s*الله",
    r"لمنتخب\s+مصر",
    r"منتخبنا(?:\s+الوطن(?:ي|ى))?",
    rf"ان\s*شاء?\s*الله\s+.*منتخب\s+مصر",
)


PROFILE_URL_ALIASES = ("profileUrl", "profile_url", "profileLink", "url")
SOURCE_ALIASES = ("source", "platform")


def _extract_facebook_profile_url(row: pd.Series) -> str:
    for key in ("profile_url", "profileUrl"):
        profile_url = row.get(key)
        if isinstance(profile_url, str) and profile_url.strip():
            return profile_url.strip()

    author = row.get("author")
    if isinstance(author, str) and author.strip():
        url_match = re.search(r"'url':\s*'([^']+)'", author)
        if url_match and url_match.group(1) not in ("None", ""):
            return url_match.group(1)
        try:
            author_data = ast.literal_eval(author)
            url = author_data.get("url")
            if isinstance(url, str) and url.strip():
                return url.strip()
        except (SyntaxError, ValueError):
            pass

    comment_url = row.get("commentUrl")
    if isinstance(comment_url, str) and comment_url.strip():
        return comment_url.strip()

    return ""


def _instagram_profile_url(username: str) -> str:
    if not isinstance(username, str) or not username.strip():
        return ""
    return f"https://www.instagram.com/{username.strip().lstrip('@')}/"


def _rename_column(df: pd.DataFrame, aliases: tuple[str, ...], target: str) -> pd.DataFrame:
    for alias in aliases:
        if alias in df.columns and alias != target:
            return df.rename(columns={alias: target})
    return df


def normalize_facebook_df(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    work = _rename_column(work, COMMENT_ALIASES, "comment")
    work = _rename_column(work, USERNAME_ALIASES, "username")
    result = _require_columns(work, "Facebook")
    result["profile_url"] = df.apply(_extract_facebook_profile_url, axis=1)
    result["source"] = "Facebook"
    return result[["username", "comment", "profile_url", "source"]]


def normalize_instagram_df(df: pd.DataFrame) -> pd.DataFrame:
    df = _rename_column(df, COMMENT_ALIASES, "comment")
    df = _rename_column(df, USERNAME_ALIASES, "username")
    df = _rename_column(df, PROFILE_URL_ALIASES, "profile_url")
    result = _require_columns(df, "Instagram")
    if "profile_url" in df.columns and df["profile_url"].notna().any():
        result["profile_url"] = df["profile_url"].fillna("").astype(str)
    else:
        result["profile_url"] = result["username"].apply(_instagram_profile_url)
    result["source"] = "Instagram"
    return result[["username", "comment", "profile_url", "source"]]


def normalize_uploaded_df(df: pd.DataFrame) -> pd.DataFrame:
    df = _rename_column(df, COMMENT_ALIASES, "comment")
    df = _rename_column(df, USERNAME_ALIASES, "username")
    df = _rename_column(df, PROFILE_URL_ALIASES, "profile_url")
    df = _rename_column(df, SOURCE_ALIASES, "source")
    result = _require_columns(df, "uploaded file")
    if "profile_url" not in df.columns:
        result["profile_url"] = ""
    else:
        result["profile_url"] = df["profile_url"].fillna("").astype(str)
    if "source" not in df.columns:
        result["source"] = "Upload"
    else:
        result["source"] = df["source"].fillna("Upload").astype(str)
    return result[["username", "comment", "profile_url", "source"]]


def _require_columns(df: pd.DataFrame, source: str) -> pd.DataFrame:
    missing = [col for col in ("username", "comment") if col not in df.columns]
    if missing:
        raise ValueError(
            f"{source} data is missing required columns: {', '.join(missing)}. "
            f"Found columns: {', '.join(df.columns)}"
        )
    return df[["username", "comment"]].copy()


def _normalize_text(text: str) -> str:
    return text.translate(ARABIC_DIGITS).lower()


def _scores_match(egypt_guess: int, arg_guess: int, egypt_score: str, arg_score: str) -> bool:
    return egypt_guess == int(egypt_score) and arg_guess == int(arg_score)


def _is_penalty_only_prediction(text: str, score_start: int) -> bool:
    """Ignore penalty-shootout scores that follow a draw prediction."""
    before = text[:score_start]
    return bool(re.search(PENALTY_PATTERN, before)) or (
        "تعادل" in before and re.search(PENALTY_PATTERN, text)
    )


def _has_egypt_win_intent(text: str) -> bool:
    """Reject comments rooting for / predicting an Egypt victory."""
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in EGYPT_WIN_PATTERNS)


def _assign_argentina_scores(s1: int, s2: int) -> tuple[int, int]:
    """Interpret score pair in Argentina-associated comments."""
    if s1 > s2:
        return s2, s1  # 3/2 للارجنتين → Egypt 2, Argentina 3
    return s1, s2  # 2/3 للارجنتين → Egypt 2, Argentina 3


def _try_patterns(text: str, egypt_score: str, arg_score: str) -> bool:
    """Only accept predictions tied to Argentina with the correct final score."""
    if _has_egypt_win_intent(text):
        return False

    checks = [
        # فوز الارجنتين 3/2  |  فوز الارجنتين 2/3
        (rf"فوز\s+{ARG_PATTERN}\s+{SCORE_PAIR}", "arg_win"),
        # 3/2 للأرجنتين  |  2/3 للارجنتين
        (rf"{SCORE_PAIR}\s*{FOR_ARG}", "arg_assoc"),
        # 3/2 الارجنتين  |  3/2 الأرجنتين
        (rf"{SCORE_PAIR}\s*{ARG_PATTERN}", "arg_assoc"),
        # الارجنتين 3/2 مصر  |  الارجنتين 3  مصر 2
        (rf"{ARG_PATTERN}\s+{SCORE_PAIR}\s+{EGYPT_PATTERN}", "arg_first"),
        (rf"{ARG_PATTERN}\s+(\d+)\s+{EGYPT_PATTERN}\s+(\d+)", "arg_egypt_explicit"),
    ]

    for pattern, mode in checks:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            if _is_penalty_only_prediction(text, match.start()):
                continue

            if mode == "arg_win":
                egypt_guess, arg_guess = _assign_argentina_scores(
                    int(match.group(1)), int(match.group(2))
                )
            elif mode == "arg_assoc":
                egypt_guess, arg_guess = _assign_argentina_scores(
                    int(match.group(1)), int(match.group(2))
                )
            elif mode == "arg_first":
                arg_guess, egypt_guess = int(match.group(1)), int(match.group(2))
            else:  # arg_egypt_explicit
                arg_guess, egypt_guess = int(match.group(1)), int(match.group(2))

            if _scores_match(egypt_guess, arg_guess, egypt_score, arg_score):
                return True

    return False


def _try_contextual_scores(text: str, egypt_score: str, arg_score: str) -> bool:
    """Use nearby Argentina keywords to interpret bare score pairs."""
    if _has_egypt_win_intent(text):
        return False

    for match in re.finditer(SCORE_PAIR, text):
        if _is_penalty_only_prediction(text, match.start()):
            continue

        s1, s2 = int(match.group(1)), int(match.group(2))
        window = text[max(0, match.start() - 40) : match.end() + 40]

        arg_near = re.search(ARG_PATTERN, window, flags=re.IGNORECASE)
        egypt_near = re.search(EGYPT_PATTERN, window, flags=re.IGNORECASE)

        if not arg_near or egypt_near:
            continue

        egypt_guess, arg_guess = _assign_argentina_scores(s1, s2)
        if _scores_match(egypt_guess, arg_guess, egypt_score, arg_score):
            return True

    return False


def is_correct_guess(text, egypt_score: str, arg_score: str) -> bool:
    if not isinstance(text, str) or not text.strip():
        return False

    normalized = _normalize_text(text)
    return _try_patterns(normalized, egypt_score, arg_score) or _try_contextual_scores(
        normalized, egypt_score, arg_score
    )


def build_contestants(
    dfs: list[pd.DataFrame], egypt_score: str, arg_score: str
) -> tuple[pd.DataFrame, int]:
    if not dfs:
        return pd.DataFrame(
            columns=["username", "comment", "profile_url", "source"]
        ), 0

    combined = pd.concat(dfs, ignore_index=True)
    combined["is_winner"] = combined["comment"].apply(
        lambda text: is_correct_guess(text, egypt_score, arg_score)
    )
    winners = combined[combined["is_winner"]].copy()
    winners["profile_url"] = winners["profile_url"].fillna("")
    winners = winners.sort_values(
        by=["username", "profile_url"], ascending=[True, False]
    ).drop_duplicates(subset=["username"], keep="first")
    return winners[["username", "comment", "profile_url", "source"]], len(winners)
