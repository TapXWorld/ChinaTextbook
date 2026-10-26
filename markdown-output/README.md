# 教材 Markdown 解析结果

本目录包含通过 [markitdown](https://github.com/microsoft/markitdown) + [Qwen VL OCR](https://help.aliyun.com/zh/model-studio/qwen-vl-ocr) 从 [ChinaTextbook](https://github.com/TapXWorld/ChinaTextbook) 转换的初高中人教版教材 Markdown 文件。

## 统计

| 学段 | 数量 |
|------|:----:|
| 小学 (语文/数学/英语) | 32 本 |
| 初中 (全科) | 42 本 |
| 高中 (全科) | 50 本 |
| **总计** | **124 本** |

## 覆盖科目

- **小学**：语文、数学、英语（统编版/人教版/人教版 PEP）
- **初中**：语文、数学、英语、物理、化学、生物、历史、地理、道德与法治（人教版/统编版）
- **高中**：语文、数学、英语、物理、化学、生物、历史、地理、政治（人教版/统编版）

## 解析方法

- 常规 PDF（含文字层）：使用 `markitdown` 的 pdfplumber 引擎直接提取
- 扫描型 PDF（无文字层，约 11 本）：先渲染为图片，再调用 `Qwen3.5-OCR` 进行文字识别

## 使用方式

```bash
# 安装
pip install 'markitdown[all]'

# 解析 PDF
from markitdown import MarkItDown
md = MarkItDown()
result = md.convert_local("path/to/file.pdf")
print(result.text_content)
```

## 注意事项

- 部分 PDF 为双栏排版，文字顺序可能有错乱
- 数学公式、化学方程式等以文本形式提取，非 LaTeX 格式
- 转换脚本见 `markitdown-scripts/` 目录