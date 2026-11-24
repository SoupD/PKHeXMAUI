# -*- coding: utf-8 -*-
"""
PKHeX MAUI 中文化脚本
在 CI 中于 dotnet publish 之前运行，把 XAML/C# 中的英文界面文本替换为中文。
- 按 translations.json 精确匹配，不碰代码逻辑、变量名、绑定表达式。
- 对 AppShell.xaml.cs 依赖的 3 个 Title 值豁免（Box/Party、pk editor、File），
  因为代码用它们判断 Flyout 模板，翻译会破坏菜单渲染。
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DICT_PATH = os.path.join(ROOT, "localization", "translations.json")

with open(DICT_PATH, encoding="utf-8") as fp:
    TRANS = json.load(fp)

# 这些 Title 值被 AppShell.xaml.cs 用于逻辑判断，必须保留英文
TITLE_EXEMPT = {"Box/Party", "pk editor", "File"}

# XAML 中需要翻译的属性
XAML_ATTRS = ("Text", "Title", "Placeholder")
# C# 中需要翻译的 .Text = "..." 赋值
CS_TEXT_RE = re.compile(r'(\.Text\s*=\s*")([^"{}]+)(")')

stats = {"xaml_files": 0, "xaml_replacements": 0, "cs_files": 0, "cs_replacements": 0, "skipped": 0}


def apply_xaml(path):
    with open(path, encoding="utf-8-sig") as fp:
        src = fp.read()
    result = src
    n = 0
    skipped = 0

    # 逐属性匹配：attr="value"，value 内不含双引号
    for attr in XAML_ATTRS:
        pat = re.compile(r'(\b' + re.escape(attr) + r'=")([^"]*)(")')

        def repl(m):
            nonlocal n, skipped
            prefix, value, suffix = m.group(1), m.group(2), m.group(3)
            if "{" in value:  # 绑定 / StaticResource 表达式，跳过
                return m.group(0)
            # 字典 key 即原始文本（含菜单缩进空格），直接精确匹配
            if value not in TRANS:
                return m.group(0)
            # Title 豁免：这些值被代码用于判断
            if attr == "Title" and value.strip() in TITLE_EXEMPT:
                skipped += 1
                return m.group(0)
            n += 1
            return prefix + TRANS[value] + suffix

        result = pat.sub(repl, result)

    if result != src:
        with open(path, "w", encoding="utf-8") as fp:
            fp.write(result)
        stats["xaml_files"] += 1
    stats["xaml_replacements"] += n
    stats["skipped"] += skipped


def apply_cs(path):
    with open(path, encoding="utf-8-sig") as fp:
        src = fp.read()
    result = src
    n = 0

    def repl(m):
        nonlocal n
        value = m.group(2)
        if value not in TRANS:
            return m.group(0)
        n += 1
        return m.group(1) + TRANS[value] + m.group(3)

    result = CS_TEXT_RE.sub(repl, result)
    if result != src:
        with open(path, "w", encoding="utf-8") as fp:
            fp.write(result)
        stats["cs_files"] += 1
    stats["cs_replacements"] += n


for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in (".git", "localization", "bin", "obj")]
    for name in filenames:
        path = os.path.join(dirpath, name)
        if name.endswith(".xaml"):
            apply_xaml(path)
        elif name.endswith(".cs") and "Platforms" not in path:
            apply_cs(path)

print("=== 汉化完成 ===")
print(f"XAML 文件修改: {stats['xaml_files']}, 替换: {stats['xaml_replacements']}")
print(f"C# 文件修改: {stats['cs_files']}, 替换: {stats['cs_replacements']}")
print(f"Title 豁免（逻辑依赖，保留英文）: {stats['skipped']}")
