#!/usr/bin/env python3
"""Kiem tra ban moi cua image dang chay, KHONG tu update, KHONG restart container.

Cach hoat dong:
- Lay danh sach container dang chay bang `docker ps`.
- Voi moi image, lay Id cua image local bang `docker image inspect`.
- Lay digest cua manifest list tren registry bang
  `docker buildx imagetools inspect <image>` (chi doc metadata, khong
  tai image ve, khong ton dung luong) va doc dong "Digest:" trong ket qua.
- So sanh hai digest: bang nhau thi image dang chay ban moi nhat, khac
  nhau thi co ban moi tren registry.

Tai sao khong so sanh config digest: ban cu lay config digest cua muc
amd64 trong `docker manifest inspect --verbose` roi so voi Id cua image
local. Tren Docker 29 dung containerd image store, Id cua image la
digest cua manifest list (index), khong phai config digest cua mot
platform, nen hai so nay khong bao gio bang nhau va script luc nao cung
bao UPDATE ke ca image vua pull xong. Da kiem chung ngay 07/11/2026:
`docker pull nginx:alpine` bao "Image is up to date", Id local la
713fc2ebfd92, nhung khong muc nao trong 16 muc cua manifest co config
digest trung voi no. Ban nay so sanh digest cua manifest list voi nhau,
la hai thu cung loai.

In ket qua: OK = dang chay ban moi nhat, UPDATE = co ban moi tren registry,
UNKNOWN = khong lay duoc digest (mang loi, image private, registry khac,
thieu buildx).

Chi chay kiem tra. Muon update that, ban phai tu quyet dinh, tao snapshot
truoc, roi moi chay `docker compose pull` + `docker compose up -d` cho tung app.
Khong co token, mat khau hay API key nao trong file nay.
"""
import re
import subprocess
import sys


def run(cmd):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except (FileNotFoundError, OSError):
        return "", 127
    return out.stdout.strip(), out.returncode


def remote_index_digest(image):
    """Digest cua manifest list tren registry, qua buildx imagetools."""
    out, code = run(["docker", "buildx", "imagetools", "inspect", image])
    if code != 0 or not out:
        return ""
    m = re.search(r"^Digest:\s*sha256:([0-9a-f]+)", out, re.MULTILINE)
    return m.group(1) if m else ""


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
        local, _ = run(["docker", "image", "inspect", "--format", "{{.Id}}", image])
        local_digest = local.split(":", 1)[1] if ":" in local else local
        remote_digest = remote_index_digest(image)
        local_short = local_digest[:12] if local_digest else "?"
        remote_short = remote_digest[:12] if remote_digest else "?"
        if not local_digest or not remote_digest:
            status = f"UNKNOWN (khong lay duoc digest de so sanh; local={local_short} remote={remote_short})"
        elif local_digest == remote_digest:
            status = f"OK - dang chay ban moi nhat (local={local_short} remote={remote_short})"
        else:
            status = f"UPDATE - co ban moi tren registry, chua update (local={local_short} remote={remote_short})"
        print(f"{name:<20} {image:<45} {status}")
    print("\nLuu y: script nay chi kiem tra, khong pull, khong up -d, khong restart.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
