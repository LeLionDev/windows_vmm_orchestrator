import sys
import subprocess
import json
import os
import getpass
from typing import Optional


def resolve_username() -> str:
    try:
        return os.getlogin()
    except OSError:
        return getpass.getuser()


def _reorder_display_name(display_name: str) -> str:
    if "," not in display_name:
        return display_name
    last_name, remainder = display_name.rsplit(",")
    first_middle_split = remainder.strip().split()
    first_name = first_middle_split[0]
    return f"{first_name} {last_name}"


def _fetch_windows_full_name() -> Optional[str]:
    # Uses System.DirectoryServices.AccountManagement (ships with .NET) instead of
    # Get-ADUser, which requires the RSAT AD PowerShell module to be installed.
    ps_command = (
        "  Add-Type -AssemblyName 'System.DirectoryServices.AccountManagement'; "
        "  $ctx = New-Object System.DirectoryServices.AccountManagement.PrincipalContext([System.DirectoryServices.AccountManagement.ContextType]::Domain); "
        "  $u = [System.DirectoryServices.AccountManagement.UserPrincipal]::FindByIdentity($ctx, $env:USERNAME); "
        "  [PSCustomObject]@{ Name = $u.DisplayName }.Name "
    )

    process = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_command],
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )
    return _reorder_display_name(process.stdout.strip())


def _fetch_linux_full_name(username: str) -> Optional[str]:
    process = subprocess.run(
        ["getent", "passwd", username],
        capture_output=True,
        text=True,
        check=True,
        timeout=5,
    )
    # passwd format: username:password:UID:GID:GECOS:directory:shell
    fields = process.stdout.strip().split(":")
    gecos = fields[4] if len(fields) >= 5 else ""
    return gecos.split(",")[0] or None


def fetch_platform_data() -> dict:
    username = resolve_username()
    result = {"username": username, "full_name": None, "error": None}

    try:
        if sys.platform.startswith("win32"):
            result["full_name"] = _fetch_windows_full_name()
        elif sys.platform.startswith("linux"):
            result["full_name"] = _fetch_linux_full_name(username)
        else:
            result["error"] = f"Unsupported operating system: {sys.platform}"
    except Exception as e:
        result["error"] = f"Directory lookup failed: {e}"

    return result


def get_current_user_directory_info() -> str:
    return json.dumps(fetch_platform_data())


_identity_cache: Optional[dict] = None


def get_display_name() -> str:
    global _identity_cache
    if _identity_cache is None:
        _identity_cache = fetch_platform_data()

    return _identity_cache["full_name"] or _identity_cache["username"]


if __name__ == "__main__":
    print(f"DEBUG INFO: {get_current_user_directory_info()}")
    print(f"USER FULL NAME: {get_display_name()}")
