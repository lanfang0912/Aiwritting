"""Save draft text to Google Docs via Service Account."""
import json
import os

from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
]


def _get_credentials():
    raw = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    if not raw:
        raise RuntimeError("缺少環境變數 GOOGLE_SERVICE_ACCOUNT_JSON")
    info = json.loads(raw)
    return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)


def save_to_gdocs(title: str, content: str) -> str:
    """
    Create a new Google Doc with the given title and content.
    Returns the URL of the created document.
    """
    creds = _get_credentials()
    folder_id = os.getenv("GDRIVE_FOLDER_ID", "")

    docs = build("docs", "v1", credentials=creds)
    drive = build("drive", "v3", credentials=creds)

    # Create empty doc
    doc = docs.documents().create(body={"title": title}).execute()
    doc_id = doc["documentId"]

    # Insert content
    docs.documents().batchUpdate(
        documentId=doc_id,
        body={
            "requests": [
                {"insertText": {"location": {"index": 1}, "text": content}}
            ]
        },
    ).execute()

    # Move to folder if specified
    if folder_id:
        file = drive.files().get(fileId=doc_id, fields="parents").execute()
        previous_parents = ",".join(file.get("parents", []))
        drive.files().update(
            fileId=doc_id,
            addParents=folder_id,
            removeParents=previous_parents,
            fields="id, parents",
        ).execute()

    return f"https://docs.google.com/document/d/{doc_id}/edit"
