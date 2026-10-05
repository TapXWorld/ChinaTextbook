#!/usr/bin/env python3
"""Download all repository files without Git or an archive (Python 3.9+)."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path, PurePosixPath
import time
from urllib.parse import quote
from urllib.request import Request, urlopen

REPO = "TapXWorld/ChinaTextbook"


def request(url):
    return urlopen(Request(url, headers={"User-Agent": "ChinaTextbook-downloader"}), timeout=120)


def file_hash(path, size):
    digest = hashlib.sha1(("blob %d\0" % size).encode())
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(entry, destination, revision):
    relative = PurePosixPath(entry["path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Unsafe path: " + entry["path"])
    target = destination.joinpath(*relative.parts)
    if not target.resolve().is_relative_to(destination.resolve()):
        raise ValueError("Path outside destination: " + entry["path"])
    if target.exists():
        if target.stat().st_size == entry["size"] and file_hash(target, entry["size"]) == entry["sha"]:
            return "已存在", entry["path"]
        raise ValueError("已有文件内容不同，未覆盖：" + str(target))
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + ".download-part")
    url = "https://raw.githubusercontent.com/%s/%s/%s" % (REPO, revision, quote(entry["path"], safe="/"))
    for attempt in range(3):
        try:
            digest = hashlib.sha1(("blob %d\0" % entry["size"]).encode())
            size = 0
            with request(url) as response, partial.open("wb") as output:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                    digest.update(chunk)
                    output.write(chunk)
            if size != entry["size"] or digest.hexdigest() != entry["sha"]:
                raise ValueError("下载校验失败：" + entry["path"])
            partial.replace(target)
            return "已下载", entry["path"]
        except Exception:
            partial.unlink(missing_ok=True)
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def main():
    parser = argparse.ArgumentParser(description="直接下载全部仓库文件，不克隆 Git、不下载 ZIP。重新运行可跳过已校验的完整文件。")
    parser.add_argument("destination", nargs="?", default="ChinaTextbook", type=Path)
    parser.add_argument("--workers", type=int, default=4, choices=range(1, 9), metavar="1-8")
    args = parser.parse_args()
    with request("https://api.github.com/repos/%s/commits/master" % REPO) as response:
        revision = json.load(response)["sha"]
    with request("https://api.github.com/repos/%s/git/trees/%s?recursive=1" % (REPO, revision)) as response:
        tree = json.load(response)
    if tree.get("truncated"):
        raise RuntimeError("GitHub 返回了不完整的文件清单，已停止下载。")
    files = [entry for entry in tree["tree"] if entry["type"] == "blob"]
    print("版本 %s；%d 个文件，共 %.2f GiB；目标 %s" % (
        revision, len(files), sum(entry["size"] for entry in files) / 2**30, args.destination), flush=True)
    failures = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(download, entry, args.destination, revision): entry for entry in files}
        for number, future in enumerate(as_completed(futures), 1):
            try:
                status, name = future.result()
                print("[%d/%d] %s %s" % (number, len(files), status, name), flush=True)
            except Exception as error:
                failures += 1
                print("失败 %s: %s" % (futures[future]["path"], error), flush=True)
    if failures:
        raise SystemExit("%d 个文件失败；排除原因后重新运行即可重试。" % failures)
    print("全部文件下载并校验完成。PDF 分块仍需按 README 合并。")


if __name__ == "__main__":
    main()
