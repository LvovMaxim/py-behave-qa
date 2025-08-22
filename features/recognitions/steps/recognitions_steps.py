# features/steps/common_steps.py
import os
import json
import requests
from behave import given, when, then
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.stage.bonrepublic.com/api"
AUTH_URL = "https://auth.stage.bonrepublic.com/realms/tenants/protocol/openid-connect/token"


# ---------- AUTH ----------
@given('I authenticate as "{username}" with password "{password}"')
def step_authenticate(context, username, password):
    """Password flow + client_secret (confidential client)."""
    payload = {
        "client_id": os.getenv("CLIENT_ID"),
        "client_secret": os.getenv("CLIENT_SECRET"),
        "grant_type": "client_credentials",
        "username": username,
        "password": password,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    resp = requests.post(AUTH_URL, data=payload, headers=headers)
    resp.raise_for_status()
    token = resp.json()["access_token"]

    context.token = token
    context.headers = {"Authorization": f"Bearer {token}"}


# ---------- GENERIC REQUESTS ----------
@when('I send a GET request to "{endpoint}"')
def step_get_to_endpoint(context, endpoint):
    url = f"{BASE_URL}{endpoint}"
    context.response = requests.get(url, headers=context.headers)



@when('I send a GET request to recognition templates')
def step_get_recognition_templates(context):
    context.execute_steps(
        'When I send a GET request to "/recognition/template/?page=1&page_size=10"'
    )


# ---------- ASSERTIONS ----------
@then('the response status code should be {status_code:d}')
def step_assert_status(context, status_code):
    actual = context.response.status_code
    body_preview = context.response.text[:500]
    assert actual == status_code, (
        f"Expected {status_code}, got {actual}. "
        f"Response: {body_preview}"
    )


@then('the response should contain key "{key}"')
def step_assert_json_key(context, key):
    data = context.response.json()
    assert key in data, f"Key '{key}' not found in response. Got: {json.dumps(data)[:500]}"