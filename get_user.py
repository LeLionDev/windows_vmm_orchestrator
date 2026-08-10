import sys
import subprocess
import json
import os
import getpass

def fetch_platform_data() -> str:
    try:
        username = os.getlogin()
    except OSError:
        username = getpass.getuser()

    if sys.platform.startswith("win32"):
        ps_command = (
            f"$Searcher = [adsisearcher]\"(sAMAccountName={username})\"; "
            "$Result = $Searcher.FindOne(); "
            "if ($Result) { "
            "    $Properties = @{}; "
            "    foreach ($Prop in $Result.Properties.PropertyNames) { "
            "        $Properties[$Prop] = $Result.Properties[$Prop] -join ', '; "
            "    }; "
            "    $Properties | ConvertTo-Json "
            "}"
        )
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


if __name__ == "__main__":
    user_profile_string = get_current_user_directory_info()
    print(user_profile_string)
