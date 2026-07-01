#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@file    dxsd_parse.py
@brief   解析动芯/Digsight .dxsd 音效包：Base_Info + 按键映射 + AUX分配 + 声音链 + 批量解码音频。
         流式 iterparse（defusedxml 防 XXE），适合 16MB 大 XML。
@usage   python3 dxsd_parse.py <file.dxsd> [out_dir]
"""

import sys
import os
import base64
import wave
from collections import defaultdict
from defusedxml import ElementTree as ET  # 安全解析器

SR = 44100  # 动芯音频采样率（试听确认）


def streamParse(path):
    """流式解析，返回 {table_tag: [record_dict, ...]}。"""
    tables = defaultdict(list)
    ctx = ET.iterparse(path, events=("start", "end"))
    stack = []
    for ev, el in ctx:
        if ev == "start":
            stack.append(el.tag)
            continue
        if len(stack) == 2:  # 顶层表元素结束
            rec = {ch.tag: (ch.text or "").strip() for ch in el}
            tables[el.tag].append(rec)
            el.clear()
        stack.pop()
    return tables


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else input(".dxsd 路径: ").strip().strip('"')
    outdir = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(path)[0] + "_out"
    os.makedirs(outdir, exist_ok=True)

    print("解析中（流式）...")
    t = streamParse(path)

    # Base_Info
    bi = (t.get("Base_Info") or [{}])[0]
    print("\n=== Base_Info ===")
    for k, v in bi.items():
        print(f"  {k} = {v}")

    # CV 字典
    cv = {}
    for r in t.get("Random_CV_Table", []):
        try:
            cv[int(r.get("CV_Address", 0))] = (r.get("CV_Value", ""), r.get("CV_Description", ""))
        except ValueError:
            continue

    # Slot 名
    slotNames = {}
    for s in t.get("Slot_Table", []):
        try:
            slotNames[int(s.get("Slot_ID", 0))] = s.get("Slot_Name", "")
        except ValueError:
            continue

    # 按键 → Slot (CV171-234)
    print("\n=== 按键 → Slot → 场景 (CV171-234) ===")
    for a in range(171, 235):
        if a in cv:
            v = cv[a][0]
            if v and v != "0" and v != "255":
                sid = a - 170
                print(f"  F{v} → Slot{sid}「{slotNames.get(sid, '')}」")

    # AUX 分配 (CV33-52)
    print("\n=== AUX 功能分配 (CV33-52) ===")
    auxNames = ["FL", "RL"] + [str(i) for i in range(1, 19)]
    for i, nm in enumerate(auxNames):
        a = 33 + i
        if a in cv:
            val = cv[a][0]
            interp = f"=F{val}" if val and val not in ("0",) and 1 <= int(val or 0) <= 28 else ""
            print(f"  CV{a} AUX_{nm} = {val} {interp}")

    # 音频解码 (16-bit PCM @ 44100)
    print(f"\n=== 音频解码 (16-bit PCM @{SR}Hz) ===")
    wdir = os.path.join(outdir, "wav")
    os.makedirs(wdir, exist_ok=True)
    n = 0
    for f in t.get("SoundFile_Table", []):
        fid = f.get("File_ID", "0")
        fname = f.get("File_Name", f"sound{fid}")
        data = f.get("File_Data", "")
        if not data:
            continue
        try:
            raw = base64.b64decode(data)
            frames = raw[:len(raw) // 2 * 2]  # 16-bit 对齐
            safe = fname.replace("/", "_")
            p = os.path.join(wdir, f"File{fid}_{safe}.wav")
            with wave.open(p, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(SR)
                wf.writeframes(frames)
            n += 1
        except Exception as e:
            print(f"  File{fid} 解码失败: {e}")
    print(f"解码 {n} 个 WAV -> {wdir}")

    # 保存 Base_Info
    with open(os.path.join(outdir, "base_info.txt"), "w", encoding="utf-8") as f:
        f.write(str(bi))
    print(f"\n完成。输出目录: {outdir}")


if __name__ == "__main__":
    main()
