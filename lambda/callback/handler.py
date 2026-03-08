import json
import os
import time
import base64
import urllib.request
import urllib.parse

import boto3

DOMAIN_NAME = os.environ["DOMAIN_NAME"]
DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]
SECRET_ARN = os.environ["SECRET_ARN"]

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE)
secrets_client = boto3.client("secretsmanager")

_cached_credentials = None


def get_spotify_credentials() -> tuple[str, str]:
    global _cached_credentials
    if _cached_credentials is None:
        resp = secrets_client.get_secret_value(SecretId=SECRET_ARN)
        secret = json.loads(resp["SecretString"])
        _cached_credentials = (secret["client_id"], secret["client_secret"])
    return _cached_credentials

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
}


def lambda_handler(event, context):
    http = event["requestContext"]["http"]
    method = http["method"]
    path = http["path"]

    if method == "OPTIONS":
        return response(204, "", content_type="text/plain")

    if method == "GET" and path == "/callback":
        return handle_callback(event)

    if method == "GET" and path == "/config":
        return handle_config()

    if method == "GET" and path.startswith("/token/"):
        session_id = path.split("/token/", 1)[1]
        return handle_token(session_id)

    if method == "POST" and path == "/refresh":
        return handle_refresh(event)

    return response(404, json.dumps({"error": "not_found"}), content_type="application/json")


def handle_callback(event):
    params = event.get("queryStringParameters") or {}
    code = params.get("code")
    state = params.get("state")
    error = params.get("error")

    if error:
        return response(400, error_page(error))

    if not code or not state:
        return response(400, error_page("Missing code or state parameter."))

    try:
        token_data = exchange_code(code)
    except Exception as e:
        return response(502, error_page(f"Token exchange failed: {e}"))

    if "error" in token_data:
        return response(400, error_page(token_data.get("error_description", token_data["error"])))

    ttl = int(time.time()) + 300

    table.put_item(Item={
        "session_id": state,
        "access_token": token_data["access_token"],
        "refresh_token": token_data.get("refresh_token", ""),
        "token_type": token_data.get("token_type", "Bearer"),
        "expires_in": token_data.get("expires_in", 3600),
        "scope": token_data.get("scope", ""),
        "ttl": ttl,
    })

    return response(200, success_page())


def handle_token(session_id):
    result = table.get_item(Key={"session_id": session_id})
    item = result.get("Item")

    if not item:
        return response(404, json.dumps({
            "error": "not_found",
            "message": "Token not found or expired",
        }), content_type="application/json")

    table.delete_item(Key={"session_id": session_id})

    token_data = {
        "access_token": item["access_token"],
        "refresh_token": item.get("refresh_token", ""),
        "token_type": item.get("token_type", "Bearer"),
        "expires_in": int(item.get("expires_in", 3600)),
        "scope": item.get("scope", ""),
    }

    return response(200, json.dumps(token_data), content_type="application/json")


def handle_config():
    client_id, _ = get_spotify_credentials()
    return response(200, json.dumps({
        "client_id": client_id,
        "redirect_uri": f"https://{DOMAIN_NAME}/callback",
        "scope": "user-read-playback-state user-modify-playback-state user-read-currently-playing user-library-read user-library-modify playlist-read-private playlist-read-collaborative user-read-recently-played user-top-read",
    }), content_type="application/json")


def handle_refresh(event):
    body = event.get("body", "")
    try:
        data = json.loads(body)
    except (json.JSONDecodeError, TypeError):
        return response(400, json.dumps({"error": "invalid_body"}), content_type="application/json")

    refresh_token = data.get("refresh_token")
    if not refresh_token:
        return response(400, json.dumps({"error": "missing_refresh_token"}), content_type="application/json")

    client_id, client_secret = get_spotify_credentials()
    credentials = base64.b64encode(
        f"{client_id}:{client_secret}".encode()
    ).decode()

    post_data = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }).encode()

    req = urllib.request.Request(
        "https://accounts.spotify.com/api/token",
        data=post_data,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            token_data = json.loads(resp.read().decode())
    except Exception as e:
        return response(502, json.dumps({"error": str(e)}), content_type="application/json")

    return response(200, json.dumps(token_data), content_type="application/json")


def exchange_code(code):
    redirect_uri = f"https://{DOMAIN_NAME}/callback"
    client_id, client_secret = get_spotify_credentials()
    credentials = base64.b64encode(
        f"{client_id}:{client_secret}".encode()
    ).decode()

    data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }).encode()

    req = urllib.request.Request(
        "https://accounts.spotify.com/api/token",
        data=data,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )

    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def response(status_code, body, content_type="text/html"):
    return {
        "statusCode": status_code,
        "headers": {**CORS_HEADERS, "Content-Type": content_type},
        "body": body,
    }


def success_page():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>terminal-ify - Authenticated</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: #121212;
    color: #ffffff;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    text-align: center;
  }
  .container {
    max-width: 480px;
    padding: 48px 32px;
  }
  .icon {
    width: 72px;
    height: 72px;
    background: #1DB954;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 32px;
    font-size: 36px;
    line-height: 1;
  }
  h1 {
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 16px;
    color: #1DB954;
  }
  p {
    font-size: 16px;
    line-height: 1.6;
    color: #b3b3b3;
  }
  .hint {
    margin-top: 32px;
    padding: 16px 24px;
    background: #1a1a1a;
    border-radius: 8px;
    border: 1px solid #282828;
    font-size: 14px;
    color: #a0a0a0;
  }
  .hint code {
    color: #1DB954;
    font-family: 'SF Mono', 'Fira Code', 'Fira Mono', monospace;
  }
</style>
</head>
<body>
<div class="container">
  <div class="icon">&#10003;</div>
  <h1>Authentication Successful</h1>
  <p>You can close this window and return to your terminal.</p>
  <div class="hint">Your <code>terminal-ify</code> session is now connected to Spotify.</div>
</div>
</body>
</html>"""


def error_page(error_detail):
    safe_detail = (
        str(error_detail)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>terminal-ify - Error</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: #121212;
    color: #ffffff;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    text-align: center;
  }}
  .container {{
    max-width: 480px;
    padding: 48px 32px;
  }}
  .icon {{
    width: 72px;
    height: 72px;
    background: #e74c3c;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 32px;
    font-size: 36px;
    line-height: 1;
  }}
  h1 {{
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 16px;
    color: #e74c3c;
  }}
  p {{
    font-size: 16px;
    line-height: 1.6;
    color: #b3b3b3;
  }}
  .detail {{
    margin-top: 24px;
    padding: 16px 24px;
    background: #1a1a1a;
    border-radius: 8px;
    border: 1px solid #282828;
    font-size: 14px;
    color: #a0a0a0;
    font-family: 'SF Mono', 'Fira Code', 'Fira Mono', monospace;
    word-break: break-word;
  }}
</style>
</head>
<body>
<div class="container">
  <div class="icon">&#10007;</div>
  <h1>Authentication Failed</h1>
  <p>Something went wrong during the Spotify authorization flow.</p>
  <div class="detail">{safe_detail}</div>
</div>
</body>
</html>"""
