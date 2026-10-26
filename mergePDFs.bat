@echo off
setlocal EnableExtensions
chcp 65001 >nul
rem ============================================================
rem 合并 ChinaTextbook 仓库中被拆分的 PDF 分片(书名.pdf.1, 书名.pdf.2 ...)
rem 用法: 将本文件放到需要处理的目录(或其上级目录), 双击运行。
rem 会递归处理当前目录下所有分片, 在分片所在目录生成 "书名.pdf";
rem 若 "书名.pdf" 已存在(例如该书同时有整本形式)则跳过。
rem 本脚本不会删除任何文件。分片为字节级切割, 按序号拼接即可还原。
rem 注意: 若文件名中含有 + 或 %% 字符, 请改用 copy /b 手动合并。
rem ============================================================

set /a MERGED=0
set /a SKIPPED=0
set /a FAILED=0

for /r %%F in (*.pdf.1) do call :merge_one "%%~dpF" "%%~nF"

echo.
echo 完成: 合并 %MERGED% 个, 跳过 %SKIPPED% 个, 失败 %FAILED% 个。
echo 确认无误后可自行删除各 *.pdf.N 分片。
pause
exit /b 0

:merge_one
rem 参数: %1 = 目录(以\结尾)   %2 = 书名.pdf (不含 .N 序号)
set "OUTBASE=%~1%~2"
if exist "%OUTBASE%" (
    set /a SKIPPED+=1
    echo [跳过] 已存在整本: %~2
    goto :eof
)
set "LIST="
set /a TOTAL=0
set /a K=1
:collect
if not exist "%OUTBASE%.%K%" goto :domerge
call :size "%OUTBASE%.%K%" SZ
set /a TOTAL+=SZ
if defined LIST (set "LIST=%LIST%+"%OUTBASE%.%K%"") else (set "LIST="%OUTBASE%.%K%"")
set /a K+=1
goto :collect
:domerge
if not defined LIST (
    set /a FAILED+=1
    echo [失败] 未找到分片: %~2
    goto :eof
)
copy /b %LIST% "%OUTBASE%" >nul
call :size "%OUTBASE%" GOT
if %GOT% NEQ %TOTAL% (
    set /a FAILED+=1
    echo [失败] 大小不符, 已删除输出, 请检查分片是否齐全: %~2
    del "%OUTBASE%" 2>nul
    goto :eof
)
set /a MERGED+=1
echo [合并] %~2 ^(%K% 片, %GOT% 字节^)
goto :eof

:size
rem 参数: %1 = 文件   %2 = 接收大小的变量名
for %%Z in ("%~1") do set "%~2=%%~zZ"
goto :eof
