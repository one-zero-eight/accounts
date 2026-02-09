from src.modules.providers.innopolis.schemas import UserInfoFromSSO
from src.modules.providers.telegram.schemas import TelegramWidgetData
from src.modules.users.search import rank_users
from src.storages.mongo.models import User


def _user(
    name: str | None = None,
    email: str | None = None,
    tg_username: str | None = None,
) -> User:
    sso = UserInfoFromSSO(email=email or "x@innopolis.ru", name=name) if (name or email) else None
    tg = TelegramWidgetData(hash="h", id=1, auth_date=0, first_name="f", username=tg_username) if tg_username else None
    return User.model_construct(innopolis_sso=sso, telegram=tg)


USERS = [
    _user(name="Alice Ivanova", email="a.ivanova@innopolis.ru", tg_username="alice_iv"),
    _user(name="Bob Petrov", email="b.petrov@innopolis.ru", tg_username="bob_p"),
    _user(name="Charlie Sidorov", email="c.sidorov@innopolis.ru", tg_username="charlie_s"),
    _user(name="Diana Kuznetsova", email="d.kuznetsova@innopolis.ru", tg_username="diana_k"),
    _user(name="Eve Smirnova", email="e.smirnova@innopolis.ru", tg_username="eve_sm"),
]


def test_empty_users():
    assert rank_users([], "alice") == []


def test_no_match():
    assert rank_users(USERS, "zzzzzzzzz", min_score=90) == []


def test_exact_name():
    results = rank_users(USERS, "Alice Ivanova", min_score=20)
    assert results[0].user is USERS[0]


def test_partial_name():
    results = rank_users(USERS, "Bob", min_score=20)
    assert results[0].user is USERS[1]


def test_name_case_insensitive():
    results = rank_users(USERS, "CHARLIE SIDOROV", min_score=20)
    assert results[0].user is USERS[2]


def test_exact_email():
    results = rank_users(USERS, "a.ivanova@innopolis.ru")
    assert results[0].user is USERS[0]


def test_email_prefix():
    results = rank_users(USERS, "b.petrov@", min_score=30)
    assert results[0].user is USERS[1]


def test_dot_pattern_weights_email():
    results = rank_users(USERS, "a.ivanova", min_score=30)
    assert results[0].user is USERS[0]
    assert results[0].email_score > results[0].name_score


def test_telegram_exact():
    results = rank_users(USERS, "@alice_iv")
    assert results[0].user is USERS[0]
    assert results[0].tg_score == 100.0


def test_telegram_partial():
    results = rank_users(USERS, "@bob_p")
    assert results[0].user is USERS[1]


def test_telegram_weight():
    results = rank_users(USERS, "@diana_k")
    r = results[0]
    assert r.user is USERS[3]
    assert r.score >= 0.8 * r.tg_score


def test_limit():
    results = rank_users(USERS, "innopolis", limit=2, min_score=0)
    assert len(results) <= 2


def test_min_score_filters():
    assert rank_users(USERS, "xyz_nomatch_123", min_score=99) == []


def test_scores_descending():
    results = rank_users(USERS, "Petrov", min_score=0)
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_no_telegram_field():
    u = _user(name="Only Name", email="only@innopolis.ru")
    results = rank_users([u], "Only Name", min_score=20)
    assert len(results) >= 1
    assert results[0].tg_score == 0.0


def test_no_sso_field():
    u = User.model_construct(
        telegram=TelegramWidgetData(hash="h", id=1, auth_date=0, first_name="f", username="solo_tg")
    )
    results = rank_users([u], "@solo_tg")
    assert len(results) >= 1
    assert results[0].name_score == 0.0
    assert results[0].email_score == 0.0
