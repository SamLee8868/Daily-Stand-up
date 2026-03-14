"""
sharepoint.py — SharePoint read/write helpers via Microsoft Graph API.

Handles uploading deliverables to and downloading files from
a SharePoint document library using MSAL client credentials flow.
"""

import os
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse, quote

import msal
import requests
from dotenv import load_dotenv

load_dotenv()

TENANT_ID = os.getenv("AZURE_TENANT_ID", "")
CLIENT_ID = os.getenv("AZURE_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET", "")
SITE_URL = os.getenv("SHAREPOINT_SITE_URL", "")
DOCUMENT_LIBRARY = os.getenv("SHAREPOINT_DOCUMENT_LIBRARY", "ShowRunner")

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
UPLOAD_CHUNK_SIZE = 4 * 1024 * 1024  # 4MB threshold for simple vs chunked upload


def _check_config():
    """Verify required environment variables are set."""
    missing = []
    if not TENANT_ID:
        missing.append("AZURE_TENANT_ID")
    if not CLIENT_ID:
        missing.append("AZURE_CLIENT_ID")
    if not CLIENT_SECRET:
        missing.append("AZURE_CLIENT_SECRET")
    if not SITE_URL:
        missing.append("SHAREPOINT_SITE_URL")
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}. "
            f"See .env.example and docs/setup-guide.md."
        )


def get_access_token() -> str:
    """Acquire an access token using MSAL client credentials flow."""
    _check_config()
    authority = f"https://login.microsoftonline.com/{TENANT_ID}"
    app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=authority,
        client_credential=CLIENT_SECRET,
    )
    result = app.acquire_token_for_client(
        scopes=["https://graph.microsoft.com/.default"]
    )
    if "access_token" in result:
        return result["access_token"]
    raise RuntimeError(
        f"Failed to acquire token: {result.get('error_description', result.get('error', 'Unknown'))}"
    )


def _get_site_id(access_token: str) -> str:
    """Resolve the SharePoint site ID from the configured SITE_URL."""
    parsed = urlparse(SITE_URL)
    hostname = parsed.hostname
    site_path = parsed.path.rstrip("/")

    url = f"{GRAPH_BASE}/sites/{hostname}:{site_path}"
    resp = requests.get(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def _get_drive_id(access_token: str, site_id: str) -> str:
    """Get the drive ID for the configured document library."""
    url = f"{GRAPH_BASE}/sites/{site_id}/drives"
    resp = requests.get(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )
    resp.raise_for_status()

    for drive in resp.json().get("value", []):
        if drive.get("name", "").lower() == DOCUMENT_LIBRARY.lower():
            return drive["id"]

    drives_available = [d.get("name") for d in resp.json().get("value", [])]
    raise RuntimeError(
        f"Document library '{DOCUMENT_LIBRARY}' not found. "
        f"Available: {drives_available}"
    )


def upload_file(
    local_path: str,
    remote_folder: str,
    access_token: Optional[str] = None,
) -> str:
    """Upload a file to SharePoint document library.

    Args:
        local_path: Path to local file.
        remote_folder: Target folder (e.g., "/GSS/Sprint-12/").
        access_token: Provided or acquired automatically.

    Returns:
        The SharePoint web URL of the uploaded file.
    """
    token = access_token or get_access_token()
    site_id = _get_site_id(token)
    drive_id = _get_drive_id(token, site_id)

    local = Path(local_path)
    filename = local.name
    remote_path = f"{remote_folder.strip('/')}/{filename}"

    file_size = local.stat().st_size

    if file_size < UPLOAD_CHUNK_SIZE:
        url = f"{GRAPH_BASE}/drives/{drive_id}/items/root:/{quote(remote_path)}:/content"
        with open(local_path, "rb") as f:
            resp = requests.put(
                url,
                data=f,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/octet-stream",
                },
                timeout=60,
            )
        resp.raise_for_status()
        web_url = resp.json().get("webUrl", "")
        print(f"Uploaded {filename} to SharePoint: {web_url}")
        return web_url
    else:
        print(f"File {filename} is {file_size} bytes — chunked upload needed but not yet implemented.")
        raise NotImplementedError("Chunked upload for files > 4MB not yet implemented.")


def download_file(
    remote_path: str,
    local_path: str,
    access_token: Optional[str] = None,
) -> None:
    """Download a file from SharePoint document library."""
    token = access_token or get_access_token()
    site_id = _get_site_id(token)
    drive_id = _get_drive_id(token, site_id)

    url = f"{GRAPH_BASE}/drives/{drive_id}/items/root:/{quote(remote_path)}:/content"
    resp = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=60,
    )
    resp.raise_for_status()

    Path(local_path).parent.mkdir(parents=True, exist_ok=True)
    with open(local_path, "wb") as f:
        f.write(resp.content)

    print(f"Downloaded to {local_path}")


def list_files(
    remote_folder: str,
    access_token: Optional[str] = None,
) -> List[dict]:
    """List files in a SharePoint document library folder.

    Returns list of dicts with keys: name, size, lastModifiedDateTime, webUrl.
    """
    token = access_token or get_access_token()
    site_id = _get_site_id(token)
    drive_id = _get_drive_id(token, site_id)

    url = f"{GRAPH_BASE}/drives/{drive_id}/items/root:/{quote(remote_folder.strip('/'))}:/children"
    resp = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    resp.raise_for_status()

    return [
        {
            "name": item["name"],
            "size": item.get("size", 0),
            "lastModifiedDateTime": item.get("lastModifiedDateTime", ""),
            "webUrl": item.get("webUrl", ""),
        }
        for item in resp.json().get("value", [])
        if "file" in item
    ]
