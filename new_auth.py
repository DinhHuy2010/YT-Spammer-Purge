import io
import json
import pathlib
import sys
from textwrap import dedent
from typing import Any, Mapping, NoReturn, Optional, TypeGuard, Union, cast

from cryptography.fernet import InvalidToken
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build_from_document

from Scripts.constants import B, F, S
from Scripts.models import CurrentUser
from Scripts.utils import encryption
from Scripts.utils.errors import fail_client_secrets_loading, fail_to_authorize, no_client_secrets
from Scripts.utils.pyinstaller_stuff import asset_file_path

# from googleapiclient.discovery import build as discovery_build

TOKEN_FILE_PATH = pathlib.Path("token.pickle").resolve()
TOKEN_FILE_PATH_ENCRYPTED = TOKEN_FILE_PATH.with_suffix(TOKEN_FILE_PATH.suffix + ".encrypted")
CLIENT_SECRETS_FILE = pathlib.Path("client_secrets.json").resolve()

# Authorization constants
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
# API_SERVICE_NAME = "youtube"
# API_VERSION = "v3"
# If don't specify discovery URL for build, works in python but fails when running as EXE
# DISCOVERY_SERVICE_URL = "https://youtube.googleapis.com/$discovery/rest?version=v3"

YOUTUBE_DISCOVERY_DOCPATH = asset_file_path("youtube-discovery.json")

# globals
_youtube_service: Optional[Any] = None
_current_user: Optional[CurrentUser] = None
_ENCRYPTED_TOKEN = True

def _read_discovery_doc():
    with YOUTUBE_DISCOVERY_DOCPATH.open("r") as r:
        return json.load(r)

def resolve_client_secrets_location() -> Optional[pathlib.Path]:
    # Check if client_secrets.json file exists, if not give error
    # if <thing> --> if bool(<thing>) (is OR ==) True
    if CLIENT_SECRETS_FILE.is_file():
        return CLIENT_SECRETS_FILE

    dund = CLIENT_SECRETS_FILE.with_suffix(".json.json")
    # In case people don't have file extension viewing enabled
    # they may add a redundant json extension
    if dund.is_file():
        return dund
    return None

def load_client_secrets() -> InstalledAppFlow:
    client_secret_path = resolve_client_secrets_location()
    if client_secret_path is None:
        no_client_secrets()

    with client_secret_path.open("r") as jf:
        try:
            csconf = json.load(jf)
        except json.JSONDecodeError as jx:
            fail_client_secrets_loading(jx)
    return InstalledAppFlow.from_client_config(csconf, YOUTUBE_SCOPES)

def refresh_creds(creds: Credentials) -> tuple[Credentials, bool]:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        return creds, True
    return creds, False

def is_creds_vaild(creds: Optional[Credentials]) -> TypeGuard[Credentials]:
    return (creds is not None) and creds.valid

def load_from_token() -> Optional[Mapping]:
    if not TOKEN_FILE_PATH.is_file():
        return
    with TOKEN_FILE_PATH.open("r") as tp:
        return json.load(tp)

def load_from_encrypted_token() -> Optional[Mapping]:
    if not TOKEN_FILE_PATH_ENCRYPTED.is_file():
        return
    print(f"\n{F.LIGHTRED_EX}Enter your password{S.R} to decrypt the login credential file ({TOKEN_FILE_PATH_ENCRYPTED.name})")
    buf = io.BytesIO()
    with TOKEN_FILE_PATH_ENCRYPTED.open("rb") as tpe:
        while True:
            tpe.seek(0)
            pwd = encryption.get_password()
            try:
                encryption.decrypt_file(tpe, buf, pwd)
            except InvalidToken:
                print(f"\n{F.WHITE}{B.LIGHTRED_EX} INCORRECT PASSWORD {S.R} - Try again. If you can't remember the password, delete '{TOKEN_FILE_PATH_ENCRYPTED.name}' and re-run the program.")
                continue
            break

    return json.loads(buf.getvalue())

def load_credentials_from_token() -> Optional[Credentials]:
    data = load_from_encrypted_token()
    if data is None:
        data = load_from_token()
    if data is None:
        return None

    creds = Credentials.from_authorized_user_info(data)
    return creds

def first_load_credentials() -> Credentials:
    flow = load_client_secrets()
    msg = dedent("""
    Waiting for authorization. See message above.
    If you close the browser or the browser tab not opening,
    go to the url here: {url}
    """.strip())
    print(f"\nPlease {F.YELLOW}login using the browser window{S.R} that opened just now.\n")

    cred = flow.run_local_server(port=0, authorization_prompt_message=msg)
    print(f"{F.GREEN}[OK] Authorization Complete.{S.R}")

    return cast(Credentials, cred)

def _save_credentials_encrypted(creds: Credentials, is_refreshed: bool) -> None:
    if is_refreshed is False:
        print(f"\n{F.LIGHTGREEN_EX}Choose a password{S.R} to encrypt the login credential file.")
    else:
        print(f"\nLogin credential refreshed -- {F.LIGHTGREEN_EX}Re-Enter your password{S.R} to re-encrypt the updated credential file.")

    password = encryption.get_password(include_confirmation=True)
    unbuf = io.BytesIO(creds.to_json().encode("utf-8"))

    with TOKEN_FILE_PATH_ENCRYPTED.open("wb") as r:
        encryption.encrypt_file(unbuf, r, password)

def _save_credentials_unencrypted(creds: Credentials) -> None:
    with TOKEN_FILE_PATH.open("w") as r:
        r.write(creds.to_json())

def save_credentials(creds: Credentials, is_refreshed: bool) -> None:
    if _ENCRYPTED_TOKEN:
        _save_credentials_encrypted(creds, is_refreshed)
    else:
        _save_credentials_unencrypted(creds)

def remove_token_file():
    TOKEN_FILE_PATH.unlink(missing_ok=True)
    TOKEN_FILE_PATH_ENCRYPTED.unlink(missing_ok=True)

def _authorize_service():
    creds = load_credentials_from_token()
    refreshed = False
    if not is_creds_vaild(creds):
        if creds is not None:
            creds, refreshed = refresh_creds(creds)
        else:
            creds, refreshed = first_load_credentials(), False
        save_credentials(creds, refreshed)

    ytservice = build_from_document(
        service=_read_discovery_doc(),
        credentials=creds
    )
    return ytservice

def authorize_service() -> Union[Any, NoReturn]:
    global _youtube_service
    if _youtube_service is not None:
        return _youtube_service

    while True:
        try:
            _youtube_service = _authorize_service()
            break
        except Exception as exc:
            if not fail_to_authorize(exc):
                sys.exit()
            else:
                remove_token_file()

    return _youtube_service

def _test():
    service = authorize_service()
    query = service.channels().list(part="snippet", mine=True)
    result = query.execute()
    print(result)

if __name__ == "__main__":
    _test()
