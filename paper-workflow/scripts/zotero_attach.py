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
必须先 **完全退出 Zotero**（含托盘图标），否则 sqlite 被占用且 Zotero 内存
状态会与数据库不一致。脚本会自动检测进程并在运行中报错退出。

用法
----
    # 先预演检查（默认行为：不加 --confirm 绝不写入）
    python zotero_attach.py --file "解析.pdf" --parent-key XXXXXXXX --title "论文解析"

    # 确认无误后实际写入
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
from secrets import choice

# Zotero 生成 item key 使用的字符集（不含 0/1/I/O，避免歧义）
KEY_CHARS = "23456789ABCDEFGHIJKLMNPQRSTUVWXYZ"
KEY_LEN = 8


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
        description="把本地文件注册为 Zotero 论文的正式子附件（需先完全退出 Zotero）")
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
    args = ap.parse_args()

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

            fname = os.path.basename(j["file"]).replace("/", "_").replace("\\", "_")
            dst = os.path.join(folder, fname)
            shutil.copy2(j["file"], dst)

            with open(dst, "rb") as f:
                md5 = hashlib.md5(f.read()).hexdigest()
            mtime_ms = int(os.path.getmtime(dst) * 1000)

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
                (next_id, parent_id, 0, "application/pdf", None,
                 f"storage:{fname}", 0, mtime_ms, md5, None))
            # 3) itemDataValues + itemData（附件显示标题）
            cur.execute("INSERT INTO itemDataValues (value) VALUES (?)", (j["title"],))
            val_id = cur.lastrowid
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
        print(f"\n[失败] 已回滚数据库写入。错误: {e}", file=sys.stderr)
        print(f"[提示] 如需回滚备份: 退出 Zotero 后用 {backup_path} 覆盖 {db_path}", file=sys.stderr)
        sys.exit(1)
    finally:
        con.close()

    print("\n[完成] 现在可以重新打开 Zotero 查看。")
    print(f"[提示] 若需回滚: 退出 Zotero 后用 {backup_path} 覆盖 {db_path}")


if __name__ == "__main__":
    main()
