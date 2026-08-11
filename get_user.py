import sys
import subprocess
import json
import os
import getpass

def resolve_username() -> str:
    try:
        return os.getlogin()
    except OSError:
        return getpass.getuser()


def fetch_platform_data() -> str:
    username = resolve_username()

    if sys.platform.startswith("win32"):
        ps_command = "Get-ADUser -Identity $env:USERNAME | ConvertTo-Json"
        try:
            process = subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            return process.stdout.strip()
        except subprocess.CalledProcessError as e:
            return f"Windows directory lookup failed: {e.stderr.strip()}"

    elif sys.platform.startswith("linux"):
        try:
            process = subprocess.run(
                ["getent", "passwd", username],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            return process.stdout.strip()
        except subprocess.CalledProcessError:
            return f"Linux directory lookup failed. User '{username}' might only exist locally."

    else:
        return f"Unsupported operating system: {sys.platform}"


def get_current_user_directory_info() -> str:
    directory_string = fetch_platform_data()
    return directory_string


_display_name_cache = None


def get_display_name() -> str:
    global _display_name_cache
    if _display_name_cache is not None:
        return _display_name_cache

    username = resolve_username()

    try:
        parsed = json.loads(fetch_platform_data())
    except (json.JSONDecodeError, TypeError):
        _display_name_cache = username
        return _display_name_cache

    _display_name_cache = parsed.get("Name") or username
    return _display_name_cache


if __name__ == "__main__":
    user_profile_string = get_current_user_directory_info()
    print(user_profile_string)
