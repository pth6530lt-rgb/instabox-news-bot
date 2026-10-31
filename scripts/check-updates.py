#!/usr/bin/env python3
"""Kiem tra ban moi cua image dang chay, KHONG tu update, KHONG restart container.

Cach hoat dong:
- Lay danh sach container dang chay bang `docker ps`.
- Voi moi image, lay digest tren registry bang `docker manifest inspect`
  (chi doc metadata, khong tai image ve, khong ton dung luong).
- So sanh voi RepoDigest cua image local (docker image inspect).
- In ket qua: OK = dang chay ban moi nhat, UPDATE = co ban moi tren registry,
  UNKNOWN = khong lay duoc digest (mang loi, image private, registry khac).

Chi chay kiem tra. Muon update that, ban phai tu quyet dinh, tao snapshot
truoc, roi moi chay `docker compose pull` + `docker compose up -d` cho tung app.
Khong co token, mat khau hay API key nao trong file nay.
"""
import json
import subprocess
import sys


def run(cmd):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except (FileNotFoundError, OSError):
        return "", 127
    return out.stdout.strip(), out.returncode


def main():
    out, code = run(["docker", "ps", "--format", "{{.Names}} {{.Image}}"])
    if code != 0 or not out:
        print("Khong lay duoc danh sach container dang chay. May co docker khong?")
        return 1
    print(f"{'Container':<20} {'Image':<45} {'Ket qua'}")
    print("-" * 90)
    for line in out.splitlines():
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        name, image = parts
        local, _ = run(
            ["docker", "image", "inspect", "--format", "{{index .RepoDigests 0}}", image]
        )
        local_digest = local.split("@", 1)[1] if "@" in local else ""
        remote_out, remote_code = run(["docker", "manifest", "inspect", image])
        remote_digest = ""
        if remote_code == 0 and remote_out:
            try:
                remote_digest = json.loads(remote_out).get("digest", "")
            except json.JSONDecodeError:
                remote_digest = ""
        if not local_digest or not remote_digest:
            status = "UNKNOWN (khong lay duoc digest de so sanh)"
        elif local_digest == remote_digest:
            status = "OK - dang chay ban moi nhat"
        else:
            status = "UPDATE - co ban moi tren registry, chua update"
        print(f"{name:<20} {image:<45} {status}")
    print("\nLuu y: script nay chi kiem tra, khong pull, khong up -d, khong restart.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
