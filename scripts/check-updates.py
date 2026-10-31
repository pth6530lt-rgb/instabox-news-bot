#!/usr/bin/env python3
"""Kiem tra ban moi cua image dang chay, KHONG tu update, KHONG restart container.

Cach hoat dong:
- Lay danh sach container dang chay bang `docker ps`.
- Voi moi image, lay digest cau hinh (config digest) tren registry bang
  `docker manifest inspect --verbose` (chi doc metadata, khong tai image
  ve, khong ton dung luong). Ban chi tiet nay tra ve mot danh sach, moi
  muc co Descriptor va OCIManifest; lay muc co platform amd64/linux.
- So sanh config digest tren registry voi Id cua image local
  (docker image inspect). Hai digest nay bang nhau khi image khong doi,
  khac nhau khi co ban moi. So sanh voi RepoDigest se sai vi RepoDigest
  la digest cua manifest list, khong phai digest cua image amd64.
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
        local, _ = run(["docker", "image", "inspect", "--format", "{{.Id}}", image])
        local_digest = local.split(":", 1)[1] if ":" in local else local
        # Ban --verbose tra ve mot danh sach, khong phai mot dict.
        remote_out, remote_code = run(
            ["docker", "manifest", "inspect", "--verbose", image]
        )
        remote_digest = ""
        if remote_code == 0 and remote_out:
            try:
                data = json.loads(remote_out)
                entries = data if isinstance(data, list) else [data]
                chosen = None
                for entry in entries:
                    desc = entry.get("Descriptor") or {}
                    platform = desc.get("platform") or {}
                    if platform.get("architecture") == "amd64" and platform.get(
                        "os"
                    ) in ("linux", None):
                        chosen = entry
                        break
                if chosen is None and entries:
                    chosen = entries[0]
                if chosen is not None:
                    oci = chosen.get("OCIManifest") or {}
                    config = oci.get("config") or {}
                    remote_digest = config.get("digest", "")
                    if remote_digest.startswith("sha256:"):
                        remote_digest = remote_digest.split(":", 1)[1]
            except (json.JSONDecodeError, AttributeError, TypeError):
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
