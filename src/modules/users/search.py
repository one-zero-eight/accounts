import re
from dataclasses import dataclass

from rapidfuzz import fuzz, process, utils

from src.storages.mongo.models import User


def norm(s: str | None) -> str:
    return (s or "").strip().lower()


def norm_tg(s: str | None) -> str:
    s = norm(s)
    return s[1:] if s.startswith("@") else s


@dataclass
class MatchResult:
    user: User
    score: float
    name_score: float
    email_score: float
    tg_score: float


def rank_users(users: list[User], q: str, limit: int = 10, min_score: float = 60.0) -> list[MatchResult]:
    if not users:
        return []

    q0 = norm(q)
    q_tg = q0[1:] if q0.startswith("@") else q0

    # Pre-extract fields into parallel lists
    names = [norm(u.innopolis_sso.name if u.innopolis_sso else None) for u in users]
    emails = [norm(u.innopolis_sso.email if u.innopolis_sso else None) for u in users]
    tgs = [norm_tg(u.telegram.username if u.telegram else None) for u in users]

    # Batch fuzzy scores via process.extract (returns list of (choice, score, index))
    name_results = {
        idx: sc
        for _, sc, idx in process.extract(
            q0, names, scorer=fuzz.WRatio, processor=utils.default_process, limit=len(users)
        )
    }
    email_results = {
        idx: sc
        for _, sc, idx in process.extract(
            q0, emails, scorer=fuzz.QRatio, processor=utils.default_process, limit=len(users)
        )
    }
    tg_results = {
        idx: sc
        for _, sc, idx in process.extract(
            q_tg, tgs, scorer=fuzz.QRatio, processor=utils.default_process, limit=len(users)
        )
    }

    # Weights (act as score ceilings since we use max() below)
    if q0.startswith("@"):
        w_name, w_email, w_tg = 0.3, 0.3, 1.0
    elif "@" in q0:
        w_name, w_email, w_tg = 0.3, 1.0, 0.3
    elif re.match(r"^[a-zA-Z0-9]+[.][a-zA-Z0-9]+$", q0):
        w_name, w_email, w_tg = 0.5, 1.0, 0.5
    else:
        w_name, w_email, w_tg = 1.0, 0.7, 0.7

    results: list[MatchResult] = []
    for i, user in enumerate(users):
        name_s = name_results.get(i, 0.0) if names[i] else 0.0

        # Email: exact/prefix override
        e = emails[i]
        if not e:
            email_s = 0.0
        elif q0 == e:
            email_s = 100.0
        elif e.startswith(q0) and len(q0) >= 3:
            email_s = 95.0
        else:
            email_s = email_results.get(i, 0.0)

        # Telegram: exact/prefix override
        t = tgs[i]
        if not t:
            tg_s = 0.0
        elif q_tg == t:
            tg_s = 100.0
        elif t.startswith(q_tg) and len(q_tg) >= 3:
            tg_s = 95.0
        else:
            tg_s = tg_results.get(i, 0.0)

        total = max(w_name * name_s, w_email * email_s, w_tg * tg_s)

        if total >= min_score:
            results.append(MatchResult(user=user, score=total, name_score=name_s, email_score=email_s, tg_score=tg_s))

    results.sort(key=lambda r: r.score, reverse=True)
    return results[:limit]
