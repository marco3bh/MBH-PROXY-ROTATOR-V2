
import time
from pathlib import Path
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
from threading import Lock

import requests

# ================= CONFIG =================

BASE_DIR = Path(__file__).resolve().parent
PROXY_FILE = BASE_DIR / "proxies.txt"
WORKING_FILE = BASE_DIR / "working_proxies.txt"

CHECK_URL = "https://api.ipify.org?format=json"
TIMEOUT = 8
MAX_WORKERS = 15

SUPPORTED = {"http", "https", "socks5", "socks5h"}


# ================= PROXY LOADER =================

def load_proxies():
    if not PROXY_FILE.exists():
        PROXY_FILE.write_text(
            "# One proxy per line\n"
            "# http://host:port\n"
            "# socks5h://host:port\n",
            encoding="utf-8"
        )
        print("[!] Created proxies.txt")
        return []

    proxies = []

    for line in PROXY_FILE.read_text(
        encoding="utf-8"
    ).splitlines():

        proxy = line.strip()

        if not proxy or proxy.startswith("#"):
            continue

        if "://" not in proxy:
            proxy = "http://" + proxy

        parsed = urlparse(proxy)

        try:
            valid_port = parsed.port is not None
            valid_host = bool(parsed.hostname)
        except ValueError:
            valid_port = False
            valid_host = False

        if (
            parsed.scheme not in SUPPORTED
            or not valid_host
            or not valid_port
        ):
            print(f"[-] Invalid proxy: {proxy}")
            continue

        proxies.append(proxy)

    return list(dict.fromkeys(proxies))


# ================= PROXY CHECKER =================

def test_proxy(proxy):
    started = time.perf_counter()

    try:
        response = requests.get(
            CHECK_URL,
            proxies={
                "http": proxy,
                "https": proxy
            },
            timeout=TIMEOUT,
            headers={
                "User-Agent": "MBH-Proxy-Rotator/2.0"
            }
        )

        response.raise_for_status()

        ip = response.json()["ip"]

        latency = round(
            (time.perf_counter() - started) * 1000
        )

        return {
            "proxy": proxy,
            "ip": ip,
            "latency": latency,
            "status": True
        }

    except (requests.RequestException, ValueError, KeyError):
        return {
            "proxy": proxy,
            "ip": None,
            "latency": None,
            "status": False
        }


# ================= PROXY ROTATOR =================

class ProxyRotator:

    def __init__(self, proxies):
        self.all_proxies = list(proxies)
        self.proxies = deque(proxies)
        self.working = {}
        self.failed = set()

        self.lock = Lock()

        self.total_requests = 0
        self.successful = 0
        self.failures = 0

    def next_proxy(self):
        with self.lock:
            if not self.proxies:
                raise RuntimeError("No proxies available")

            proxy = self.proxies[0]
            self.proxies.rotate(-1)

            return proxy

    def scan(self):
        if not self.all_proxies:
            print("[-] No proxies loaded")
            return

        print(
            f"\n[*] Checking {len(self.all_proxies)} proxies..."
        )

        results = []

        with ThreadPoolExecutor(
            max_workers=MAX_WORKERS
        ) as executor:

            futures = {
                executor.submit(test_proxy, proxy): proxy
                for proxy in self.all_proxies
            }

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

                if result["status"]:
                    print(
                        f"[+] {result['proxy']} "
                        f"| {result['latency']}ms "
                        f"| IP: {result['ip']}"
                    )
                else:
                    print(f"[-] FAILED: {result['proxy']}")

        working = [
            result for result in results
            if result["status"]
        ]

        working.sort(key=lambda x: x["latency"])

        with self.lock:
            self.working = {
                item["proxy"]: item for item in working
            }

            self.failed = {
                item["proxy"] for item in results
                if not item["status"]
            }

            self.proxies = deque(
                item["proxy"] for item in working
            )

        self.export_working()

        print("\n========== SCAN RESULTS ==========")
        print(f"Total   : {len(results)}")
        print(f"Working : {len(working)}")
        print(f"Failed  : {len(results) - len(working)}")
        print("==================================")

    def check_ip(self):
        if not self.proxies:
            print("[-] No working proxies")
            print("[*] Run proxy scanner first")
            return

        attempts = len(self.proxies)

        for _ in range(attempts):
            proxy = self.next_proxy()

            print(f"\n[*] Testing: {proxy}")

            result = test_proxy(proxy)

            self.total_requests += 1

            if result["status"]:
                self.successful += 1

                self.working[proxy] = result

                print(f"[+] Public IP: {result['ip']}")
                print(f"[+] Latency: {result['latency']}ms")
                print(f"[+] Proxy: {proxy}")

                return result

            self.failures += 1

            print("[-] Proxy unavailable")

        print("[-] All available proxies failed")
        return None

    def auto_rotate(self, count, interval):
        if not self.proxies:
            print("[-] Run proxy scanner first")
            return

        for index in range(count):
            print(
                f"\n========== ROTATION "
                f"{index + 1}/{count} =========="
            )

            self.check_ip()

            if index < count - 1:
                time.sleep(interval)

    def export_working(self):
        proxies = sorted(
            self.working.values(),
            key=lambda x: x["latency"]
        )

        WORKING_FILE.write_text(
            "\n".join(item["proxy"] for item in proxies)
            + ("\n" if proxies else ""),
            encoding="utf-8"
        )

        print(
            f"[+] Exported {len(proxies)} proxies "
            f"to working_proxies.txt"
        )

    def statistics(self):
        total = self.total_requests

        success_rate = (
            self.successful / total * 100
            if total else 0
        )

        print("\n========== MBH STATISTICS ==========")
        print(f"Loaded proxies : {len(self.all_proxies)}")
        print(f"Working proxies: {len(self.working)}")
        print(f"Failed scan    : {len(self.failed)}")
        print(f"Requests       : {self.total_requests}")
        print(f"Successful     : {self.successful}")
        print(f"Failed         : {self.failures}")
        print(f"Success rate   : {success_rate:.1f}%")
        print("====================================")


# ================= BANNER =================

def banner():
    print(r"""
 __  __ ____  _   _
|  \/  | __ )| | | |
| |\/| |  _ \| |_| |
| |  | | |_) |  _  |
|_|  |_|____/|_| |_|

 ____  ____   _____  ____   __
|  _ \|  _ \ / _ \ \/ /\ \ / /
| |_) | |_) | | | \  /  \ V /
|  __/|  _ <| |_| /  \   | |
|_|   |_| \_\\___/_/\_\  |_|

       PROXY ROTATOR v2.0
       MBH NETWORK TOOLS
""")


# ================= MAIN =================

def main():
    banner()

    proxies = load_proxies()

    rotator = ProxyRotator(proxies)

    print(f"[+] Loaded {len(proxies)} proxies")

    while True:
        print("""
[1] SCAN ALL PROXIES
[2] CHECK CURRENT PROXY IP
[3] AUTO ROTATE PROXIES
[4] EXPORT WORKING PROXIES
[5] STATISTICS
[6] RELOAD PROXY LIST
[0] EXIT
""")

        choice = input("MBH > ").strip()

        try:
            if choice == "1":
                rotator.scan()

            elif choice == "2":
                rotator.check_ip()

            elif choice == "3":
                count = int(
                    input("Rotations (1-100): ")
                )

                interval = float(
                    input("Interval in seconds (min 3): ")
                )

                if not 1 <= count <= 100:
                    print("[-] Invalid rotation count")
                    continue

                if not 3 <= interval <= 3600:
                    print("[-] Interval must be 3-3600 seconds")
                    continue

                rotator.auto_rotate(count, interval)

            elif choice == "4":
                rotator.export_working()

            elif choice == "5":
                rotator.statistics()

            elif choice == "6":
                proxies = load_proxies()
                rotator = ProxyRotator(proxies)

                print(
                    f"[+] Reloaded {len(proxies)} proxies"
                )

            elif choice == "0":
                print("[+] Goodbye.")
                break

            else:
                print("[-] Invalid option")

        except (ValueError, RuntimeError) as error:
            print(f"[-] Error: {error}")

        except KeyboardInterrupt:
            print("\n[!] Operation interrupted")


if __name__ == "__main__":
    main()
