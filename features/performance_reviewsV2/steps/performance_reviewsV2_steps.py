# features/performance_reviewsV2/steps/performance_reviewsV2_steps.py
import json
import requests
from behave import given, when, then
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup

# ---------- DEV2 endpoints ----------
AUTH_BASE = "https://auth.dev2.bonrepublic.com/realms/tenants"
BASE_URL_DEV2 = "https://api.dev2.bonrepublic.com"

# frontend client autorisation
FRONTEND_CLIENT_ID = "frontend"
REDIRECT_URI = "https://maxim-lvov.dev2.bonrepublic.com/"


def _get_login_form_action(html_text: str) -> str:
    """Достаём URL action из login form Keycloak."""
    soup = BeautifulSoup(html_text, "html.parser")
    form = soup.find("form")
    if not form or not form.get("action"):
        raise AssertionError("Cannot find login form action on Keycloak login page.")
    return form["action"]


@given('I authenticate on dev2 as "{username}" with password "{password}"')
def step_auth_as_user(context, username, password):
    """
    Логинимся в Keycloak как фронт (client_id=frontend, aud=account).
    Берём access_token и сохраняем в context.headers.
    """
    s = requests.Session()

    # 1) Получаем login form
    auth_url = (
        f"{AUTH_BASE}/protocol/openid-connect/auth"
        f"?scope=openid"
        f"&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        f"&client_id={FRONTEND_CLIENT_ID}"
    )
    r1 = s.get(auth_url, allow_redirects=True)
    r1.raise_for_status()
    login_action_url = _get_login_form_action(r1.text)

    # 2) POST login/password
    r2 = s.post(login_action_url, data={"username": username, "password": password}, allow_redirects=True)

    # 3) take code from redirect URL
    parsed = urlparse(r2.url)
    code_list = parse_qs(parsed.query).get("code")
    assert code_list, f"Authorization code not found in redirect url: {r2.url}"
    code = code_list[0]

    # 4) exchange code for token
    token_url = f"{AUTH_BASE}/protocol/openid-connect/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": FRONTEND_CLIENT_ID,
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r3 = s.post(token_url, data=data, headers=headers)
    r3.raise_for_status()

    access_token = r3.json()["access_token"]
    context.token = access_token
    context.headers = {"Authorization": f"Bearer {access_token}"}

    print("Got frontend token (aud=account):", access_token[:40], "...")


@when("I remember current auth as admin")
def step_remember_admin_auth(context):
    """Сохраняем текущие заголовки как админские, чтобы потом вернуть для удаления."""
    assert hasattr(context, "headers"), "Authenticate first."
    context.admin_headers = dict(context.headers)


# ========= CREATE / FETCH =========

@when('I create a review session on dev2 with payload:')
def step_create_review_session_dev2(context):
    assert hasattr(context, "headers"), "Not authenticated. Call the auth step first."

    body = json.loads(context.text)  # JSON from block """..."""
    url = f"{BASE_URL_DEV2}/performance-reviews/v1/review-sessions/"
    headers = {**context.headers, "Content-Type": "application/json"}

    resp = requests.post(url, json=body, headers=headers)
    context.response = resp
    resp.raise_for_status()

    data = resp.json()
    context.review_session_id = data.get("id")
    assert context.review_session_id, f"POST ok but no 'id' in response: {data}"


@when('I fetch the created review session on dev2')
def step_fetch_created_review_session_dev2(context):
    assert hasattr(context, "headers"), "Not authenticated. Call the auth step first."
    assert hasattr(context, "review_session_id"), "No review_session_id in context."

    url = f"{BASE_URL_DEV2}/performance-reviews/v1/review-sessions/{context.review_session_id}/"
    context.response = requests.get(url, headers=context.headers)


# ========= DELETE =========

@when('I delete the created review session on dev2')
def step_delete_review_session_dev2(context):
    """
    Удаляем созданную сессию.
    Если есть сохранённые админские заголовки — используем их.
    Иначе — текущие (на случай, если удалять может и текущий юзер).
    """
    assert hasattr(context, "review_session_id"), "No review_session_id in context."
    headers = getattr(context, "admin_headers", context.headers)
    assert headers, "No headers present to authorize DELETE."

    url = f"{BASE_URL_DEV2}/performance-reviews/v1/review-sessions/{context.review_session_id}/"
    resp = requests.delete(url, headers=headers)
    context.response = resp


# ========= ASSERTS =========

@then('the response status code should be {status_code:d}')
def step_assert_status(context, status_code):
    actual = context.response.status_code
    body_preview = context.response.text[:1000]
    assert actual == status_code, (
        f"Expected {status_code}, got {actual}. "
        f"URL: {getattr(context.response.request, 'url', '<no url>')} "
        f"\nResponse: {body_preview}"
    )


@then('one of participants has title exactly "{expected_title}"')
def step_assert_participant_title(context, expected_title):
    data = context.response.json()
    participants = data.get("participants", [])
    titles = [p.get("title") for p in participants if isinstance(p, dict)]
    assert expected_title in titles, (
        f"Expected title not found.\nExpected: {expected_title}\nGot titles: {titles}"
    )


@then("participants titles should not be visible to the current user")
def step_participants_titles_hidden(context):
    """
    Проверяем, что ни у одного участника нет непустого title.
    Это подтверждает анонимность для текущего пользователя.
    """
    data = context.response.json()
    participants = data.get("participants", [])
    offending = [
        p.get("title")
        for p in participants
        if isinstance(p, dict) and isinstance(p.get("title"), str) and p.get("title").strip() != ""
    ]
    assert not offending, f"Titles are visible, expected anonymity. Visible titles: {offending}"
