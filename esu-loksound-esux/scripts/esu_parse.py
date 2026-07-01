#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@file    esu_parse.py
@brief   解析 ESU LokSound .esux：提取 meta.xml 功能映射，列出文件表，导出 .wav 条目的加密载荷。
@usage   python3 esu_parse.py <file.esux> [out_dir]
"""

import sys
import re
import struct
import os
import math
from collections import Counter
from defusedxml import ElementTree as ET  # 防 XXE


def parseContainer(path):
    """解析 .esux 容器：返回 (raw, metaXml, entries)。"""
    data = open(path, "rb").read()
    if data[:4] != b"ESU ":
        raise ValueError("非 ESU .esux 文件（魔数应为 'ESU '）")
    mlen = struct.unpack_from("<I", data, 14)[0]
    meta = data[18:18 + mlen].decode("utf-8", "replace")  # type=16 块，明文
    # 命名文件表条目（允许 UTF-8 高位字节，处理德语变音符 äöü）
    entries = []
    for m in re.finditer(rb'[\x20-\xff]{3,80}\.(wav|xml|bmp|png)', data):
        off = m.start()
        nb = m.group(0)
        if off < 8:
            continue
        B = struct.unpack_from("<I", data, off - 4)[0]
        if B != len(nb) + 16:  # 校验 B = nameLen + 16
            continue
        ne = off + len(nb)
        if ne + 38 > len(data):
            continue
        entries.append((off, nb, ne))
    entries.sort(key=lambda e: e[0])
    return data, meta, entries


def extractFunctions(meta):
    """从 meta.xml 提取功能键→描述。返回 [(fid, en_desc)]。"""
    root = ET.fromstring(meta.encode("utf-8"))
    funcs = []
    for fn in root.iter():
        if fn.tag.endswith("function"):
            fid = fn.get("id", "?")
            descs = {}
            for d in fn:
                if d.tag.endswith("description"):
                    lang = d.get("{http://www.w3.org/XML/1998/namespace}lang", "de")
                    descs[lang] = (d.text or "").strip()
            funcs.append((fid, descs.get("en", descs.get("de", ""))))
    return funcs


def indexOfCoincidence(raw):
    """计算 byte-level IC；随机密文通常接近 1/256 = 0.0039。"""
    n = len(raw)
    if n < 2:
        return 0.0
    counts = Counter(raw)
    return sum(c * (c - 1) for c in counts.values()) / (n * (n - 1))


def entropy(raw):
    """计算 byte entropy。"""
    n = len(raw)
    if not n:
        return 0.0
    counts = Counter(raw)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def exportEncryptedPayloads(data, entries, outdir):
    """导出 .wav 条目的加密载荷；不伪解码为可播放 WAV。"""
    os.makedirs(outdir, exist_ok=True)
    n = 0
    rows = []
    for i in range(1, len(entries)):
        name = entries[i][1].decode("utf-8", "replace")
        if not name.endswith(".wav"):
            continue
        dataStart = entries[i - 1][2] + 38      # 前条目 nameEnd + 38
        dataEnd = entries[i][0] - 8              # 本条目 A 字段前
        raw = data[dataStart:dataEnd]
        safe = name.replace("/", "_") + ".encrypted.bin"
        with open(os.path.join(outdir, safe), "wb") as f:
            f.write(raw)
        rows.append((name, len(raw), entropy(raw), indexOfCoincidence(raw)))
        n += 1
    with open(os.path.join(outdir, "payload_summary.tsv"), "w", encoding="utf-8") as f:
        f.write("name\tsize\tentropy\tic\n")
        for name, size, ent, ic in rows:
            f.write(f"{name}\t{size}\t{ent:.4f}\t{ic:.6f}\n")
    return n


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else input(".esux 路径: ").strip().strip('"')
    outdir = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(path)[0] + "_out"
    data, meta, entries = parseContainer(path)
    print("meta.xml: %d 字节, 文件表条目: %d" % (len(meta), len(entries)))
    funcs = extractFunctions(meta)
    print("\n=== 功能键映射 (%d 个) ===" % len(funcs))
    for fid, desc in funcs:
        print("  F%s: %s" % (fid, desc))
    os.makedirs(outdir, exist_ok=True)
    open(os.path.join(outdir, "meta.xml"), "w", encoding="utf-8").write(meta)
    n = exportEncryptedPayloads(data, entries, os.path.join(outdir, "encrypted_audio"))
    print("\n导出 %d 个 .wav 加密载荷 -> %s/encrypted_audio/" % (n, outdir))
    print("payload_summary.tsv 中 IC 接近 0.0039 通常表示随机密文；不要伪解码为 WAV。")


if __name__ == "__main__":
    main()
