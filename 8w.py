import subprocess
import sys

for pkg in ("requests", "pyyaml"):
    try:
        __import__(pkg)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

import time
import random
import string
import yaml
from requests import post, RequestException

with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

_8w_idx = config["tokens"]
_webhook_url = config["webhook_url"]
_username_length = config.get("username_length", 4)
_iq_8w_idx = 0

def format_time(seconds: float) -> str:
    seconds = int(seconds)
    hrs, rem = divmod(seconds, 3600)
    mins, secs = divmod(rem, 60)
    parts = []
    if hrs:
        parts.append(f"{hrs} hour{'s' if hrs != 1 else ''}")
    if mins:
        parts.append(f"{mins} minute{'s' if mins != 1 else ''}")
    if secs or not parts:
        parts.append(f"{secs} second{'s' if secs != 1 else ''}")
    return ", ".join(parts)

def generate_username(length=_username_length):
    chars = string.ascii_lowercase+string.digits+"_."
    return "".join(random.choice(chars)for _ in range(length))

def generate_usernames():
    try:
        count = int(input("Enter the number of usernames to generate: "))
    except ValueError:
        print("Please enter a valid integer.")
        return
    with open("8w_user.txt", "w", encoding="utf-8") as f:
        for _ in range(count):
            f.write(generate_username() + "\n")
    print(f"{count} usernames written to 8w_user.txt")

def check_usernames():
    global _iq_8w_idx
    try:
        with open("8w_user.txt", "r", encoding="utf-8") as infile:
            usernames = infile.read().splitlines()
    except FileNotFoundError:
        print("Username file not found. Please generate usernames first.")
        return

    print(f"\nTotal usernames to check: {len(usernames)}\n")
    for name in usernames:
        while True:
            t_8w = _8w_idx[_iq_8w_idx]
            try:
                response = post(
                    "https://discord.com/api/v9/users/@me/pomelo-attempt",
                    json={"username": name},
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": t_8w
                    }
                )
            except RequestException as e:
                print(f"[!]: Network error while checking '{name}': {e}")
                print("Retrying in 5 seconds...")
                time.sleep(5)
                continue

            if response.status_code == 429:
                retry = response.json().get("retry_after", 0)
                prev = _iq_8w_idx
                _iq_8w_idx = (_iq_8w_idx + 1) % len(_8w_idx)
                if _iq_8w_idx == prev:
                    print(f"All tokens rate limited. Waiting {format_time(retry)}...")
                    time.sleep(retry)
                else:
                    print(f"Switching to token #{_iq_8w_idx+1}. Retrying...")
                continue
            break

        if response.status_code == 200:
            if response.json().get("taken"):
                print(f"[-]: Username '{name}' is already taken.")
            else:
                print(f"[+]: Username '{name}' is available.")
                post(_webhook_url, json={"embeds":[{"description": name, "footer": {"text": "8.w - beta"}}]})
                with open("ava_8w.txt", "a", encoding="utf-8") as validfile:
                    validfile.write(f"{name}\n")
        elif response.status_code == 401:
            print(f"Auth error {response.status_code}. Refresh token #{_iq_8w_idx+1}.")
            input("Press ENTER after refreshing token to continue...")
        else:
            print(f"[!]: Unexpected HTTP {response.status_code} encountered for '{name}'.")

    print("\nAll username checks complete.")
    input("Press ENTER to return to the menu...")

def main():
    while True:
        print("\nPlease choose an option:")
        print("1) Generate usernames")
        print("2) Check usernames")
        choice = input("Enter 1 or 2: ").strip()
        if choice == '1':
            generate_usernames()
        elif choice == '2':
            check_usernames()
        else:
            print("Invalid choice. Please enter 1 or 2.")

if __name__ == "__main__":
    main()
