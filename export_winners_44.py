"""Export the previous 44-winner list (context-aware filter, before Argentina-only rule)."""

import pandas as pd

from filtering import (
    ARG_PATTERN,
    EGYPT_PATTERN,
    FOR_ARG,
    FOR_EGYPT,
    PENALTY_PATTERN,
    SCORE_PAIR,
    _normalize_text,
    _scores_match,
    normalize_facebook_df,
    normalize_instagram_df,
)


def _is_penalty_only_prediction(text: str, score_start: int) -> bool:
    before = text[:score_start]
    return bool(__import__("re").search(PENALTY_PATTERN, before)) or (
        "تعادل" in before and __import__("re").search(PENALTY_PATTERN, text)
    )


def _assign_argentina_scores(s1: int, s2: int) -> tuple[int, int]:
    if s1 > s2:
        return s2, s1
    return s1, s2


def _try_patterns_relaxed(text: str, egypt_score: str, arg_score: str) -> bool:
    import re

    checks = [
        (rf"فوز\s+{EGYPT_PATTERN}(?:\s+على\s+{ARG_PATTERN})?\s+{SCORE_PAIR}", "egypt_first"),
        (rf"فوز\s+{ARG_PATTERN}\s+{SCORE_PAIR}", "arg_assoc"),
        (rf"{SCORE_PAIR}\s*{FOR_EGYPT}", "egypt_first"),
        (rf"{SCORE_PAIR}\s*{FOR_ARG}", "arg_assoc"),
        (rf"{SCORE_PAIR}\s*{ARG_PATTERN}", "arg_assoc"),
        (rf"{EGYPT_PATTERN}\s+{SCORE_PAIR}", "egypt_first"),
        (rf"{EGYPT_PATTERN}\s+(\d+)\s+{ARG_PATTERN}\s+(\d+)", "egypt_arg_explicit"),
        (rf"{ARG_PATTERN}\s+{SCORE_PAIR}\s+{EGYPT_PATTERN}", "arg_first"),
        (rf"{ARG_PATTERN}\s+(\d+)\s+{EGYPT_PATTERN}\s+(\d+)", "arg_egypt_explicit"),
        (rf"{EGYPT_PATTERN}\s+هت(?:فوز|كسب)\s+{SCORE_PAIR}", "egypt_first"),
    ]

    for pattern, mode in checks:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            if _is_penalty_only_prediction(text, match.start()):
                continue

            if mode == "egypt_first":
                egypt_guess, arg_guess = int(match.group(1)), int(match.group(2))
            elif mode in ("arg_assoc", "arg_first"):
                egypt_guess, arg_guess = _assign_argentina_scores(
                    int(match.group(1)), int(match.group(2))
                )
            elif mode == "egypt_arg_explicit":
                egypt_guess, arg_guess = int(match.group(1)), int(match.group(2))
            else:
                arg_guess, egypt_guess = int(match.group(1)), int(match.group(2))

            if _scores_match(egypt_guess, arg_guess, egypt_score, arg_score):
                return True
    return False


def _try_contextual_relaxed(text: str, egypt_score: str, arg_score: str) -> bool:
    import re

    for match in re.finditer(SCORE_PAIR, text):
        if _is_penalty_only_prediction(text, match.start()):
            continue

        s1, s2 = int(match.group(1)), int(match.group(2))
        window = text[max(0, match.start() - 40) : match.end() + 40]
        egypt_near = re.search(EGYPT_PATTERN, window, flags=re.IGNORECASE)
        arg_near = re.search(ARG_PATTERN, window, flags=re.IGNORECASE)

        if egypt_near and not arg_near:
            if _scores_match(s1, s2, egypt_score, arg_score):
                return True
        elif arg_near and not egypt_near:
            egypt_guess, arg_guess = _assign_argentina_scores(s1, s2)
            if _scores_match(egypt_guess, arg_guess, egypt_score, arg_score):
                return True
        elif egypt_near and arg_near:
            if egypt_near.start() < arg_near.start():
                if _scores_match(s1, s2, egypt_score, arg_score):
                    return True
            else:
                egypt_guess, arg_guess = _assign_argentina_scores(s1, s2)
                if _scores_match(egypt_guess, arg_guess, egypt_score, arg_score):
                    return True
    return False


def is_correct_guess_relaxed(text, egypt_score: str, arg_score: str) -> bool:
    if not isinstance(text, str) or not text.strip():
        return False
    normalized = _normalize_text(text)
    return _try_patterns_relaxed(normalized, egypt_score, arg_score) or _try_contextual_relaxed(
        normalized, egypt_score, arg_score
    )


def main() -> None:
    fb = pd.read_csv("facebook_raw.csv")
    ig = pd.read_csv("instagram_raw.csv")
    combined = pd.concat(
        [normalize_facebook_df(fb), normalize_instagram_df(ig)], ignore_index=True
    )
    combined["is_winner"] = combined["comment"].apply(
        lambda text: is_correct_guess_relaxed(text, "2", "3")
    )
    winners = combined[combined["is_winner"]].copy()
    winners["profile_url"] = winners["profile_url"].fillna("")
    winners = winners.sort_values(
        by=["username", "profile_url"], ascending=[True, False]
    ).drop_duplicates(subset=["username"], keep="first")
    winners = winners[["username", "comment", "profile_url", "source"]]
    winners.to_csv("winners_44.csv", index=False, encoding="utf-8-sig")
    print(f"Saved winners_44.csv with {len(winners)} entries")


if __name__ == "__main__":
    main()
