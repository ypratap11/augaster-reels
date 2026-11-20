#!/usr/bin/env python3
"""One-time: get a YouTube upload refresh token for publish_youtube.py.

1. Google Cloud console -> your project -> enable "YouTube Data API v3".
2. OAuth consent screen: External, add yourself as a test user, then "Publish app"
   (In production) so the refresh token does not expire after 7 days.
3. Credentials -> Create OAuth client ID -> Desktop app. Copy the ID and secret.
4. Run:  python youtube_auth.py <client_id> <client_secret>
   Sign in with the Google account that owns the YouTube channel and allow upload.
5. Save the printed values as GitHub secrets YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN.
   Never commit them.
"""
import http.server, json, secrets, sys, urllib.parse, urllib.request, webbrowser

SCOPE = "https://www.googleapis.com/auth/youtube.upload"
PORT = 8765


def main(cid, secret):
    redirect = f"http://127.0.0.1:{PORT}/"
    state = secrets.token_urlsafe(16)
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": cid, "redirect_uri": redirect, "response_type": "code", "scope": SCOPE,
        "access_type": "offline", "prompt": "consent", "state": state})
    got = {}

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            got.update({k: v[0] for k, v in q.items()})
            self.send_response(200); self.end_headers()
            self.wfile.write(b"Done. You can close this tab and return to the terminal.")

        def log_message(self, *a):
            pass

    print("Opening your browser to sign in…\nIf it doesn't open, visit:\n" + url)
    webbrowser.open(url)
    with http.server.HTTPServer(("127.0.0.1", PORT), H) as srv:
        while "code" not in got and "error" not in got:
            srv.handle_request()
    if got.get("state") != state or "code" not in got:
        raise SystemExit(f"sign-in failed: {got.get('error', 'state mismatch')}")
    data = urllib.parse.urlencode({"code": got["code"], "client_id": cid, "client_secret": secret,
                                   "redirect_uri": redirect, "grant_type": "authorization_code"}).encode()
    tok = json.load(urllib.request.urlopen("https://oauth2.googleapis.com/token", data))
    if "refresh_token" not in tok:
        raise SystemExit("no refresh token returned; remove the app's access at myaccount.google.com/permissions and retry")
    print("\nAdd these as GitHub secrets (Settings -> Secrets and variables -> Actions):")
    print(f"  YT_CLIENT_ID      = {cid}")
    print(f"  YT_CLIENT_SECRET  = (the secret you passed in)")
    print(f"  YT_REFRESH_TOKEN  = {tok['refresh_token']}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])
