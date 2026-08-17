#!/bin/sh
# 合并 ChinaTextbook 仓库中被拆分的 PDF 分片（书名.pdf.1、书名.pdf.2 …）。
# 用法: 将本脚本放到需要处理的目录（或其上级目录）中, 在该目录下执行:
#   sh mergePDFs.sh
# 会递归处理当前目录下所有分片, 在分片所在目录生成 "书名.pdf";
# 分片为字节级切割, 按序号直接拼接即可还原。脚本不会删除任何文件。
# 若 "书名.pdf" 已存在（例如该书同时有整本形式）则跳过。

set -eu

merged=0
skipped=0
failed=0

find . -type f -name '*.pdf.1' | (while IFS= read -r first; do
    base="${first%.pdf.1}"
    out="$base.pdf"

    if [ -f "$out" ]; then
        echo "[跳过] 已存在整本: $out"
        skipped=$((skipped + 1))
        continue
    fi

    # 按序号 1,2,3… 依次收集分片（避免 .10 排到 .2 前的字典序问题）
    list=''
    expect=0
    k=1
    while [ -f "$base.pdf.$k" ]; do
        if [ -n "$list" ]; then
            list="$list \"$base.pdf.$k\""
        else
            list="\"$base.pdf.$k\""
        fi
        expect=$((expect + $(wc -c < "$base.pdf.$k" | tr -d ' ')))
        k=$((k + 1))
    done

    # shellcheck disable=SC2086
    if eval "cat $list" > "$out"; then
        got=$(wc -c < "$out" | tr -d ' ')
        head4=$(head -c 4 "$out" 2>/dev/null || true)
        if [ "$got" != "$expect" ] || [ "$head4" != "%PDF" ] \
           || ! tail -c 2048 "$out" | grep -aq '%%EOF'; then
            echo "[失败] 校验不通过, 已删除: $out (期望 $expect 字节, 实际 $got)"
            rm -f "$out"
            failed=$((failed + 1))
        else
            echo "[合并] $out ($got 字节, $((k - 1)) 片)"
            merged=$((merged + 1))
        fi
    else
        echo "[失败] 拼接出错: $out"
        rm -f "$out"
        failed=$((failed + 1))
    fi
done
echo
echo "完成: 合并 $merged 个, 跳过 $skipped 个, 失败 $failed 个。"
echo "确认无误后可自行删除各 *.pdf.N 分片。")
