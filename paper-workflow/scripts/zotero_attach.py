#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
zotero_attach.py —— 把本地文件注册为 Zotero 论文的正式子附件

用途
----
把论文解析 PDF、笔记 PDF、补充材料等本地文件，注册成 Zotero 中某篇论文的
子附件，使其在 Zotero 界面论文条目的下拉列表中可见，并参与正常同步。

关键原理（务必理解，否则会踩坑）
--------------------------------
Zotero 的附件列表以 **sqlite 数据库记录** 为准，而不是以文件系统为准：
  - `Zotero/storage/<KEY>/` 中的 `<KEY>` 是 **附件条目自己的 key**，不是论文条目的 key；
  - 一个附件条目对应一个独立 storage 文件夹；
  - 直接把文件拷进已有 storage 文件夹，Zotero **不会显示该文件，也不会同步**。
因此本脚本做的是：新建 key → 建文件夹 → 放文件 → 写 4 张表 → 校验。

前置条件
--------
两种写入模式，按需选择：

【推荐】本地 API 模式（--api）：Zotero **运行中**直接写入，无需退出。
  要求 Zotero 10+，且 设置→高级 勾选“允许此计算机上的其他应用程序与 Zotero 通信”。
  首次写入会弹窗授权，请点 “Always Allow”（密钥缓存于 ~/.zotero_attach_local_key.json）。
  改动立即在 UI 可见、正常参与同步、自动维护全文索引。

sqlite 直写模式（默认）：必须先 **完全退出 Zotero**（含托盘图标），否则 sqlite
被占用且 Zotero 内存状态会与数据库不一致。脚本会自动检测进程并在运行中报错退出。

用法
----
    # 先预演检查（默认行为：不加 --confirm 绝不写入）
    python zotero_attach.py --file "解析.pdf" --parent-key XXXXXXXX --title "论文解析"

    # API 模式（Zotero 运行中，无需退出；首次会弹窗授权）
    python zotero_attach.py --api --file "解析.pdf" --parent-key XXXXXXXX --title "论文解析" --confirm
    python zotero_attach.py --api-probe          # 只探测本地 API 是否可用

    # sqlite 模式（需先完全退出 Zotero）
    python zotero_attach.py --file "解析.pdf" --parent-key XXXXXXXX --title "论文解析" --confirm

    # 按论文标题匹配父条目（必须唯一匹配）
    python zotero_attach.py --file "解析.pdf" --parent-title "Finite-Time Consensus" --title "论文解析" --confirm

    # 批量（JSON 文件）
    python zotero_attach.py --jobs jobs.json --confirm

    # 在临时副本库上做演练（推荐首次使用时先这样试，不碰真实文献库）
    python zotero_attach.py --data-dir ./_zttest --file "解析.pdf" --parent-key XXXXXXXX --title "论文解析" --confirm

jobs.json 格式:
    [
      {"file": "a.pdf", "parent_key": "K46DL2TF", "title": "论文解析A"},
      {"file": "b.pdf", "parent_title": "Some Paper Title", "title": "论文解析B"}
    ]

回滚
----
脚本会在写入前自动备份数据库为 `zotero.sqlite.bak-<时间戳>`。
如需回滚：退出 Zotero → 用备份文件覆盖原 `zotero.sqlite` → 重开 Zotero。
"""

import argparse
import hashlib
import json
import os
import platform
import shutil
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from secrets import choice

# Zotero 生成 item key 使用的字符集（不含 0/1/I/O，避免歧义）
KEY_CHARS = "23456789ABCDEFGHIJKLMNPQRSTUVWXYZ"
KEY_LEN = 8

# 常见扩展名 → Zotero contentType（不要一律写 application/pdf）
CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".doc": "application/msword",
    ".md": "text/markdown",
    ".tex": "application/x-tex",
    ".txt": "text/plain",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def default_data_dir():
    home = os.path.expanduser("~")
    return os.path.join(home, "Zotero")


def _run_out(cmd):
    """执行命令并以忽略非法编码的方式返回小写输出（Windows 的 tasklist 可能输出 GBK 中文）"""
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=15)
        return (p.stdout or b"").decode("utf-8", "ignore").lower()
    except Exception:
        return ""


def zotero_is_running():
    """检测 Zotero 进程是否仍在运行（跨平台，不依赖第三方库）"""
    if platform.system() == "Windows":
        out = _run_out(["tasklist", "/FI", "IMAGENAME eq zotero.exe"])
        return "zotero.exe" in out
    out = _run_out(["pgrep", "-f", "zotero"])
    return bool(out.strip())


def is_locked(db_path):
    """尝试以读写方式短暂打开，判断是否被占用"""
    try:
        con = sqlite3.connect(db_path, timeout=2)
        cur = con.cursor()
        cur.execute("BEGIN IMMEDIATE")
        cur.execute("ROLLBACK")
        con.close()
        return False
    except sqlite3.OperationalError:
        return True


def gen_key(existing):
    while True:
        k = "".join(choice(KEY_CHARS) for _ in range(KEY_LEN))
        if k not in existing:
            existing.add(k)
            return k


# =====================================================================
# 本地 API 模式（Zotero 10+，Zotero 运行中直接写入，无需退出）
# =====================================================================
#
# 官方文档: https://www.zotero.org/support/dev/web_api/v3/local_api
# 要点：
#   - 需 Zotero 10+，且 设置→高级 勾选“允许此计算机上的其他应用程序与 Zotero 通信”；
#   - 读请求无需认证；写请求需 Zotero-Server-ID + Zotero-API-Key；
#   - 写密钥通过 POST /api/local/authorize 运行时弹窗获取（用户点 Always Allow 后可复用）；
#   - 通过 API 写入的改动是 Zotero 的普通本地改动，立即在 UI 可见、正常参与同步、
#     自动维护全文索引——因此比 sqlite 直写更安全，推荐优先使用。

API_KEY_CACHE = os.path.join(os.path.expanduser("~"), ".zotero_attach_local_key.json")


class LocalApiError(Exception):
    def __init__(self, status, body):
        self.status = status
        self.body = body
        super().__init__(f"HTTP {status}: {body[:200]}")


class LocalApiClient:
    """Zotero 10+ 本地 API 最小客户端（仅用标准库）"""

    def __init__(self, port=23119, app_name="paper-workflow zotero_attach", api_key=None):
        self.port = port
        self.base = f"http://127.0.0.1:{port}/api"
        self.app_name = app_name
        self.server_id = None
        self.api_key = api_key
        self._probe()

    # ---- 底层请求 ----
    def _request(self, method, path_or_url, headers=None, body=None,
                 auth=False, timeout=60):
        url = path_or_url if path_or_url.startswith("http") else self.base + path_or_url
        hdrs = dict(headers or {})
        if auth:
            if self.server_id:
                hdrs["Zotero-Server-ID"] = self.server_id
            if self.api_key:
                hdrs["Zotero-API-Key"] = self.api_key
        req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status, resp.headers, resp.read()
        except urllib.error.HTTPError as e:
            return e.code, e.headers, e.read()
        except urllib.error.URLError as e:
            raise SystemExit(
                f"[错误] 无法连接 Zotero 本地 API ({url}): {e.reason}\n"
                "      请确认 Zotero 正在运行。")

    def _json(self, status, body):
        try:
            return json.loads(body.decode("utf-8"))
        except Exception:
            raise LocalApiError(status, body.decode("utf-8", "replace"))

    # ---- 探测与授权 ----
    def _probe(self):
        status, headers, _ = self._request("GET", "/", timeout=15)
        if status == 403:
            raise SystemExit(
                "[错误] Zotero 本地 API 未启用（403）。\n"
                "      请在 Zotero 中：设置 → 高级 → 勾选\n"
                "      “允许此计算机上的其他应用程序与 Zotero 通信”，然后重试。")
        if status != 200:
            raise SystemExit(f"[错误] 本地 API 探测失败: HTTP {status}")
        self.server_id = headers.get("Zotero-Server-ID")
        api_ver = headers.get("Zotero-API-Version", "?")
        schema_ver = headers.get("Zotero-Schema-Version", "?")
        print(f"[信息] 本地 API 已连接 (API v{api_ver}, schema {schema_ver}, "
              f"Server-ID {self.server_id})")
        if not self.server_id:
            raise SystemExit(
                "[错误] 响应中没有 Zotero-Server-ID —— 写入需要 Zotero 10 或更高版本，"
                "请升级 Zotero 或改用 sqlite 模式（需退出 Zotero）。")
        # 从缓存恢复可复用 key
        if not self.api_key:
            self.api_key = self._load_cached_key()

    def _load_cached_key(self):
        try:
            with open(API_KEY_CACHE, encoding="utf-8") as f:
                cache = json.load(f)
            entry = cache.get(self.server_id)
            if entry and entry.get("remember"):
                return entry.get("key")
        except Exception:
            pass
        return None

    def _save_cached_key(self, key, remember):
        if not remember:
            return
        cache = {}
        try:
            with open(API_KEY_CACHE, encoding="utf-8") as f:
                cache = json.load(f)
        except Exception:
            pass
        cache[self.server_id] = {"key": key, "remember": True}
        try:
            with open(API_KEY_CACHE, "w", encoding="utf-8") as f:
                json.dump(cache, f)
        except Exception:
            pass

    def authorize(self):
        """弹窗请求写权限。注意：若用户只点 Allow，该 key 只能消费一个写请求。"""
        print("[授权] Zotero 将弹出授权对话框，请点击 “Always Allow”（允许复用）…")
        status, _, body = self._request(
            "POST", "/local/authorize",
            headers={"Content-Type": "application/json",
                     "Zotero-Server-ID": self.server_id},
            body=json.dumps({"appName": self.app_name}).encode("utf-8"),
            timeout=180)
        if status == 403:
            raise SystemExit("[错误] 用户拒绝了写授权。")
        if status == 429:
            raise SystemExit("[错误] 授权请求过于频繁（429），请稍等片刻后重试。")
        if status != 200:
            raise SystemExit(f"[错误] 授权失败: HTTP {status} {body[:200]}")
        data = self._json(status, body)
        self.api_key = data["key"]
        self._save_cached_key(self.api_key, data.get("remember", False))
        if not data.get("remember"):
            print("[警告] 你选择了单次授权（Allow）。批量挂载会多次弹窗；"
                  "建议点 “Always Allow”。")

    def _write(self, method, path, headers=None, body=None, timeout=60, _retried=False):
        """带 key 的写请求；401 时自动重新授权并重试一次。"""
        if not self.api_key:
            self.authorize()
        status, hdrs, data = self._request(method, path, headers=headers,
                                           body=body, auth=True, timeout=timeout)
        if status == 401 and not _retried:
            self.api_key = None  # 缓存 key 失效（单次 key 已消费或已被清除）
            self.authorize()
            return self._write(method, path, headers=headers, body=body,
                               timeout=timeout, _retried=True)
        return status, hdrs, data

    # ---- 条目操作 ----
    def get_item(self, key):
        status, _, body = self._request("GET", f"/users/0/items/{key}")
        if status != 200:
            return None
        return self._json(status, body)

    def resolve_parent(self, parent_key=None, parent_title=None):
        if parent_key:
            item = self.get_item(parent_key)
            if not item:
                raise SystemExit(f"[错误] 未找到 key 为 {parent_key} 的条目")
            data = item.get("data", {})
            if data.get("itemType") in ("attachment", "note"):
                raise SystemExit(
                    f"[错误] key {parent_key} 指向的是 {data.get('itemType')} 条目，"
                    "请提供论文条目本身的 key（Zotero 界面右键条目 → 复制条目链接可看到 key）")
            return parent_key, data.get("title", parent_key)
        if parent_title:
            q = urllib.parse.quote(parent_title)
            status, _, body = self._request(
                "GET", f"/users/0/items?q={q}&qmode=titleCreatorYear&limit=100")
            if status != 200:
                raise SystemExit(f"[错误] 标题搜索失败: HTTP {status}")
            hits = [it for it in self._json(status, body)
                    if it.get("data", {}).get("itemType") not in ("attachment", "note")]
            hits = [it for it in hits
                    if parent_title.lower() in (it["data"].get("title") or "").lower()]
            if not hits:
                raise SystemExit(f"[错误] 没有标题包含 “{parent_title}” 的论文条目")
            if len(hits) > 1:
                print("[错误] 标题匹配到多篇论文，请改用 --parent-key：")
                for it in hits[:10]:
                    print(f"  key={it['key']}  {it['data'].get('title', '')[:70]}")
                raise SystemExit(1)
            return hits[0]["key"], hits[0]["data"].get("title", "")
        raise SystemExit("[错误] 必须提供 --parent-key 或 --parent-title")

    def child_attachment_exists(self, parent_key, title):
        status, _, body = self._request(
            "GET", f"/users/0/items/{parent_key}/children")
        if status != 200:
            return False
        for it in self._json(status, body):
            d = it.get("data", {})
            if d.get("itemType") == "attachment" and d.get("title") == title:
                return True
        return False

    def create_attachment(self, parent_key, title, filename, ctype):
        payload = [{
            "itemType": "attachment",
            "parentItem": parent_key,
            "linkMode": "imported_file",
            "title": title,
            "accessDate": "",
            "url": "",
            "note": "",
            "tags": [],
            "relations": {},
            "contentType": ctype,
            "charset": "",
            "filename": filename,
            "md5": None,
            "mtime": None,
        }]
        status, _, body = self._write(
            "POST", "/users/0/items",
            headers={"Content-Type": "application/json"},
            body=json.dumps(payload).encode("utf-8"))
        if status != 200:
            raise LocalApiError(status, body.decode("utf-8", "replace"))
        result = self._json(status, body)
        if result.get("failed"):
            raise LocalApiError(status, json.dumps(result["failed"], ensure_ascii=False))
        ok = result.get("successful", {})
        if not ok:
            raise LocalApiError(status, "successful 为空: " + body.decode("utf-8", "replace")[:300])
        return ok["0"]["key"]

    def upload_file(self, item_key, file_path, filename, md5, mtime_ms, ctype):
        """三阶段上传：授权 → POST 字节 → 注册"""
        size = os.path.getsize(file_path)
        form = urllib.parse.urlencode({
            "md5": md5, "filename": filename, "filesize": size, "mtime": mtime_ms,
        }).encode("utf-8")
        status, _, body = self._write(
            "POST", f"/users/0/items/{item_key}/file",
            headers={"Content-Type": "application/x-www-form-urlencoded",
                     "If-None-Match": "*"},
            body=form)
        if status != 200:
            raise LocalApiError(status, body.decode("utf-8", "replace"))
        auth = self._json(status, body)
        if auth.get("exists") == 1:
            print("       (文件内容已存在，直接关联，无需上传)")
            return

        upload_url = auth["url"]
        if upload_url.startswith("/"):
            upload_url = f"http://127.0.0.1:{self.port}" + upload_url
        with open(file_path, "rb") as f:
            blob = f.read()
        # 本地 API 的 prefix/suffix 为空；非空时按 multipart 片段拼接（兼容 Web API 形态）
        data = (auth.get("prefix", "").encode("utf-8") + blob
                + auth.get("suffix", "").encode("utf-8"))
        status, _, resp_body = self._request(
            "POST", upload_url,
            headers={"Content-Type": auth.get("contentType") or ctype},
            body=data, timeout=300)
        if status != 201:
            raise LocalApiError(status, resp_body.decode("utf-8", "replace"))

        reg = urllib.parse.urlencode({"upload": auth["uploadKey"]}).encode("utf-8")
        status, _, body = self._write(
            "POST", f"/users/0/items/{item_key}/file",
            headers={"Content-Type": "application/x-www-form-urlencoded",
                     "If-None-Match": "*"},
            body=reg)
        if status != 204:
            raise LocalApiError(status, body.decode("utf-8", "replace"))


def run_api_mode(args, jobs):
    client = LocalApiClient(port=args.api_port, api_key=args.api_key)
    ok, skipped, failed = 0, 0, 0
    results = []

    for j in jobs:
        try:
            pkey, pdesc = client.resolve_parent(j["parent_key"], j["parent_title"])
            if client.child_attachment_exists(pkey, j["title"]):
                print(f"[跳过] 父条目已存在同名附件 “{j['title']}”，跳过")
                skipped += 1
                continue
            fname = os.path.basename(j["file"]).replace("/", "_").replace("\\", "_")
            with open(j["file"], "rb") as f:
                md5 = hashlib.md5(f.read()).hexdigest()
            mtime_ms = int(os.path.getmtime(j["file"]) * 1000)
            ctype = CONTENT_TYPES.get(os.path.splitext(fname)[1].lower(),
                                      "application/octet-stream")
            new_key = client.create_attachment(pkey, j["title"], fname, ctype)
            client.upload_file(new_key, j["file"], fname, md5, mtime_ms, ctype)
            # 校验
            item = client.get_item(new_key)
            d = (item or {}).get("data", {})
            if d.get("md5") != md5:
                print(f"[警告] 附件已创建但 md5 校验不一致: {new_key}")
            print(f"[完成] “{j['title']}” → key={new_key} 父条目={pdesc}")
            ok += 1
            results.append((j["title"], new_key))
        except LocalApiError as e:
            print(f"[失败] “{j['title']}”: {e}", file=sys.stderr)
            failed += 1

    print(f"\n[汇总] 成功 {ok}，跳过 {skipped}，失败 {failed}")
    if ok:
        print("[提示] API 写入已即时生效，Zotero 界面展开对应论文即可看到附件，"
              "无需重启；如需删除，直接在 Zotero 中右键附件 → 删除。")
    return 0 if failed == 0 else 1


def resolve_parent(cur, parent_key=None, parent_title=None):
    """按 key 或标题解析父论文条目，返回 (itemID, 显示标题)"""
    if parent_key:
        row = cur.execute(
            "SELECT itemID FROM items WHERE key = ? AND itemTypeID != 3", (parent_key,)
        ).fetchone()
        if not row:
            raise SystemExit(f"[错误] 未找到 key 为 {parent_key} 的论文条目（或它是附件条目本身）")
        return row[0], f"key={parent_key}"

    if parent_title:
        rows = cur.execute(
            """
            SELECT i.itemID,
                   (SELECT v.value FROM itemData d
                      JOIN itemDataValues v ON d.valueID = v.valueID
                     WHERE d.itemID = i.itemID AND d.fieldID =
                           (SELECT fieldID FROM fields WHERE fieldName = 'title'))
              FROM items i
             WHERE i.itemTypeID != 3 AND i.itemID NOT IN (SELECT itemID FROM deletedItems)
            """
        ).fetchall()
        hits = [(i, t) for (i, t) in rows if t and parent_title.lower() in t.lower()]
        if not hits:
            raise SystemExit(f"[错误] 没有标题包含 “{parent_title}” 的论文条目")
        if len(hits) > 1:
            print("[错误] 标题匹配到多篇论文，请改用 --parent-key 指定：")
            for i, t in hits[:10]:
                print(f"  itemID={i}  {t[:70]}")
            raise SystemExit(1)
        return hits[0][0], hits[0][1]

    raise SystemExit("[错误] 必须提供 --parent-key 或 --parent-title")


def build_jobs(args):
    if args.jobs:
        with open(args.jobs, encoding="utf-8") as f:
            raw = json.load(f)
        jobs = []
        for j in raw:
            jobs.append({
                "file": j["file"],
                "title": j.get("title") or os.path.splitext(os.path.basename(j["file"]))[0],
                "parent_key": j.get("parent_key"),
                "parent_title": j.get("parent_title"),
            })
        return jobs
    if not (args.file and (args.parent_key or args.parent_title)):
        raise SystemExit("[错误] 单个模式需提供 --file 与 (--parent-key | --parent-title)")
    return [{
        "file": args.file,
        "title": args.title or os.path.splitext(os.path.basename(args.file))[0],
        "parent_key": args.parent_key,
        "parent_title": args.parent_title,
    }]


def main():
    ap = argparse.ArgumentParser(
        description="把本地文件注册为 Zotero 论文的正式子附件")
    ap.add_argument("--file", help="要注册的文件（PDF 等）")
    ap.add_argument("--parent-key", help="父论文条目的 Zotero key（推荐，唯一）")
    ap.add_argument("--parent-title", help="父论文标题（模糊匹配，必须唯一命中）")
    ap.add_argument("--title", help="附件在 Zotero 中显示的标题")
    ap.add_argument("--jobs", help="批量任务 JSON 文件路径")
    ap.add_argument("--data-dir", help=f"Zotero 数据目录（默认 {default_data_dir()}）")
    ap.add_argument("--backup-dir", help="数据库备份目录（默认与数据库同目录）")
    ap.add_argument("--dry-run", action="store_true", help="只检查与预演，不写数据库、不建目录")
    ap.add_argument("--confirm", action="store_true",
                    help="确认实际写入（不加此项只会预演，防止误写真实文献库）")
    ap.add_argument("--force", action="store_true", help="跳过 Zotero 运行检测（不推荐）")
    ap.add_argument("--api", action="store_true",
                    help="走 Zotero 10+ 本地 API 写入（Zotero 运行中使用，无需退出；推荐）")
    ap.add_argument("--api-port", type=int, default=23119, help="本地 API 端口（默认 23119）")
    ap.add_argument("--api-key", default=None,
                    help="已有本地 API 写密钥（不提供则自动弹窗授权）")
    ap.add_argument("--api-probe", action="store_true",
                    help="只探测本地 API 可用性后退出（不执行任何写入）")
    args = ap.parse_args()

    # ---- API 模式：Zotero 运行中写入，无需退出 ----
    if args.api_probe:
        LocalApiClient(port=args.api_port, api_key=args.api_key)
        print("[探测] 本地 API 可用。")
        return
    if args.api:
        jobs = build_jobs(args)
        for j in jobs:
            if not os.path.exists(j["file"]):
                raise SystemExit(f"[错误] 文件不存在: {j['file']}")
        print(f"[信息] 本地 API 模式（无需退出 Zotero），待注册 {len(jobs)} 个附件")
        if args.dry_run or not args.confirm:
            for j in jobs:
                print(f"  [预演] {j['file']}  →  父条目 {j['parent_key'] or j['parent_title']}"
                      f"  标题 “{j['title']}”")
            print("[预演] 未做任何写入。确认无误后加 --confirm 实际执行。")
            return
        sys.exit(run_api_mode(args, jobs))

    # ---- sqlite 直写模式：需先完全退出 Zotero ----
    data_dir = args.data_dir or default_data_dir()
    db_path = os.path.join(data_dir, "zotero.sqlite")
    storage_dir = os.path.join(data_dir, "storage")

    if not os.path.exists(db_path):
        raise SystemExit(f"[错误] 找不到 Zotero 数据库: {db_path}")
    if not os.path.isdir(storage_dir):
        raise SystemExit(f"[错误] 找不到 storage 目录: {storage_dir}")

    jobs = build_jobs(args)
    for j in jobs:
        if not os.path.exists(j["file"]):
            raise SystemExit(f"[错误] 文件不存在: {j['file']}")

    # ---- 安全检查：Zotero 必须已退出 ----
    print(f"[信息] Zotero 数据目录: {data_dir}")
    print(f"[信息] 目标数据库: {db_path}")
    print(f"[信息] 待注册 {len(jobs)} 个附件")

    # 默认只预演：实际写入必须显式 --confirm，避免误写真实文献库
    if args.dry_run or not args.confirm:
        for j in jobs:
            print(f"  [预演] {j['file']}  →  父条目 {j['parent_key'] or j['parent_title']}  标题 “{j['title']}”")
        print("[预演] 未做任何写入。确认无误后加 --confirm 实际执行。")
        return

    # ---- 安全检查：Zotero 必须已退出 ----
    if not args.force:
        if zotero_is_running():
            raise SystemExit(
                "[错误] Zotero 仍在运行。请在 Zotero 中执行 文件→退出，"
                "并确认托盘图标也已退出后重试。\n"
                "      （确认已退出但脚本误判时，可加 --force 跳过检测，风险自负）")
        if is_locked(db_path):
            raise SystemExit(
                f"[错误] 数据库被占用: {db_path}\n"
                "      请确认 Zotero 已完全退出后重试。")

    # ---- 备份数据库 ----
    ts = time.strftime("%Y%m%d_%H%M%S")
    backup_dir = args.backup_dir or data_dir
    backup_path = os.path.join(backup_dir, f"zotero.sqlite.bak-{ts}")
    shutil.copy2(db_path, backup_path)
    print(f"[备份] 数据库已备份 → {backup_path}")

    con = sqlite3.connect(db_path, timeout=20)
    cur = con.cursor()

    try:
        fields = cur.execute("SELECT fieldID FROM fields WHERE fieldName = 'title'").fetchall()
        if not fields:
            raise SystemExit("[错误] fields 表中找不到 title 字段")
        title_fid = fields[0][0]

        existing_keys = set(r[0] for r in cur.execute("SELECT key FROM items"))
        created_folders = []
        cur.execute("SELECT MAX(itemID) FROM items")
        next_id = (cur.fetchone()[0] or 0) + 1
        now = time.strftime("%Y-%m-%d %H:%M:%S")

        for j in jobs:
            parent_id, parent_desc = resolve_parent(cur, j["parent_key"], j["parent_title"])

            # 幂等：同一父条目下已有同名附件则跳过
            dup = cur.execute(
                """
                SELECT a.itemID FROM itemAttachments a
                  JOIN itemData d ON d.itemID = a.itemID AND d.fieldID = ?
                  JOIN itemDataValues v ON v.valueID = d.valueID
                 WHERE a.parentItemID = ? AND v.value = ?
                """, (title_fid, parent_id, j["title"])).fetchone()
            if dup:
                print(f"[跳过] 父条目已存在同名附件 “{j['title']}”，跳过")
                continue

            new_key = gen_key(existing_keys)
            folder = os.path.join(storage_dir, new_key)
            os.makedirs(folder, exist_ok=True)
            created_folders.append(folder)

            fname = os.path.basename(j["file"]).replace("/", "_").replace("\\", "_")
            dst = os.path.join(folder, fname)
            shutil.copy2(j["file"], dst)

            with open(dst, "rb") as f:
                md5 = hashlib.md5(f.read()).hexdigest()
            mtime_ms = int(os.path.getmtime(dst) * 1000)
            ctype = CONTENT_TYPES.get(os.path.splitext(fname)[1].lower(),
                                      "application/octet-stream")

            # 1) items
            cur.execute(
                "INSERT INTO items (itemID, itemTypeID, dateAdded, dateModified, "
                "clientDateModified, libraryID, key, version, synced, clientVersion) "
                "VALUES (?,?,?,?,?,?,?,0,0,0)",
                (next_id, 3, now, now, now, 1, new_key))
            # 2) itemAttachments
            cur.execute(
                "INSERT INTO itemAttachments (itemID, parentItemID, linkMode, contentType, "
                "charsetID, path, syncState, storageModTime, storageHash, "
                "lastProcessedModificationTime, lastRead) VALUES (?,?,?,?,?,?,?,?,?,?,NULL)",
                (next_id, parent_id, 0, ctype, None,
                 f"storage:{fname}", 0, mtime_ms, md5, None))
            # 3) itemDataValues + itemData（附件显示标题）
            # 注意：itemDataValues.value 有 UNIQUE 约束，重复标题必须复用同一个 valueID
            cur.execute("INSERT OR IGNORE INTO itemDataValues (value) VALUES (?)", (j["title"],))
            val_id = cur.execute(
                "SELECT valueID FROM itemDataValues WHERE value = ?", (j["title"],)).fetchone()[0]
            cur.execute("INSERT INTO itemData (itemID, fieldID, valueID) VALUES (?,?,?)",
                        (next_id, title_fid, val_id))

            print(f"[完成] “{j['title']}” → itemID={next_id} key={new_key} 父条目={parent_desc}")
            print(f"       文件: {dst}")
            next_id += 1

        con.commit()

        # ---- 回读校验 ----
        print("\n[校验] 写入结果回读：")
        for j in jobs:
            row = cur.execute(
                """
                SELECT i.itemID, i.key, a.parentItemID, a.path, v.value
                  FROM items i
                  JOIN itemAttachments a ON a.itemID = i.itemID
                  JOIN itemData d ON d.itemID = i.itemID AND d.fieldID = ?
                  JOIN itemDataValues v ON v.valueID = d.valueID
                 WHERE v.value = ?
                """, (title_fid, j["title"])).fetchone()
            print("   ", row if row else f"[警告] 未找到 “{j['title']}”")

    except Exception as e:
        con.rollback()
        for folder in created_folders:
            shutil.rmtree(folder, ignore_errors=True)
        if created_folders:
            print(f"[清理] 已移除 {len(created_folders)} 个未登记的存储文件夹", file=sys.stderr)
        print(f"\n[失败] 已回滚数据库写入。错误: {e}", file=sys.stderr)
        print(f"[提示] 如需回滚备份: 退出 Zotero 后用 {backup_path} 覆盖 {db_path}", file=sys.stderr)
        sys.exit(1)
    finally:
        con.close()

    print("\n[完成] 现在可以重新打开 Zotero 查看。")
    print(f"[提示] 若需回滚: 退出 Zotero 后用 {backup_path} 覆盖 {db_path}")


if __name__ == "__main__":
    main()
