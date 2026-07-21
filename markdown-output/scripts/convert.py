#!/usr/bin/env python3
"""
使用 markitdown + Qwen OCR 批量转换教材 PDF 为 Markdown
"""

import requests, json, os, sys, time, base64, io, tempfile, shutil, re
from urllib.parse import quote

# === 配置 ===
# 按需填入你的 API Key
QWEN_API_KEY = os.environ.get("QWEN_API_KEY", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# markitdown 支持的格式直接用 markitdown
# 扫描型 PDF 用 Qwen OCR
MARKITDOWN_EXTENSIONS = {'.pdf', '.html', '.txt', '.md', '.csv', '.json', '.xml', '.pptx', '.docx', '.xlsx'}


def convert_with_markitdown(pdf_path):
    """使用 markitdown 转换"""
    from markitdown import MarkItDown
    md = MarkItDown()
    result = md.convert_local(pdf_path)
    return result.text_content


def convert_with_qwen_ocr(pdf_path, api_key, model="qwen3.5-ocr"):
    """使用 Qwen OCR 转换扫描型 PDF"""
    import pypdfium2 as pdfium
    
    pdf = pdfium.PdfDocument(pdf_path)
    n_pages = len(pdf)
    print(f"  总页数: {n_pages}")
    
    all_text = []
    batch_size = 20
    
    for start in range(0, n_pages, batch_size):
        end = min(start + batch_size, n_pages)
        tmp_dir = tempfile.mkdtemp(prefix="ocr_batch_")
        
        # 渲染
        for i in range(start, end):
            page = pdf[i]
            bitmap = page.render(scale=120/72)
            pil_image = bitmap.to_pil()
            pil_image.convert('RGB').save(os.path.join(tmp_dir, f"p{i:04d}.jpg"), format='JPEG', quality=70)
            pil_image.close()
            bitmap.close()
            page.close()
        
        # OCR
        for i in range(start, end):
            page_num = i + 1
            img_path = os.path.join(tmp_dir, f"p{i:04d}.jpg")
            with open(img_path, 'rb') as f:
                img_b64 = base64.b64encode(f.read()).decode('utf-8')
            os.remove(img_path)
            
            response = requests.post(
                "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "请完整提取这张图片中的所有文字内容，保持原文结构。输出为Markdown格式。"},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"},
                             "min_pixels": 32*32*3, "max_pixels": 32*32*8192}
                        ]
                    }],
                    "max_tokens": 4096,
                },
                timeout=120
            )
            if response.status_code == 200:
                text = response.json()['choices'][0]['message']['content']
                all_text.append(f"## 第 {page_num} 页\n\n{text}\n\n")
            else:
                all_text.append(f"## 第 {page_num} 页\n\n[OCR 失败: {response.text[:100]}]\n\n")
        
        shutil.rmtree(tmp_dir, ignore_errors=True)
    
    pdf.close()
    return "\n".join(all_text)


def main():
    if len(sys.argv) < 2:
        print("用法: python3 convert.py <pdf_path> [--ocr]")
        print("  --ocr: 强制使用 OCR（扫描型 PDF）")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    use_ocr = "--ocr" in sys.argv
    
    if not os.path.exists(pdf_path):
        print(f"文件不存在: {pdf_path}")
        sys.exit(1)
    
    print(f"转换: {pdf_path}")
    t0 = time.time()
    
    if use_ocr:
        if not QWEN_API_KEY:
            print("需要设置 QWEN_API_KEY 环境变量")
            sys.exit(1)
        text = convert_with_qwen_ocr(pdf_path, QWEN_API_KEY)
    else:
        text = convert_with_markitdown(pdf_path)
        # 如果 markitdown 输出为空，回退到 OCR
        if not text.strip() and QWEN_API_KEY:
            print("  markitdown 输出为空，尝试 OCR...")
            text = convert_with_qwen_ocr(pdf_path, QWEN_API_KEY)
    
    elapsed = time.time() - t0
    print(f"完成: {len(text)} 字符 ({elapsed:.1f}s)")
    
    # 输出到文件
    output_path = pdf_path.replace('.pdf', '.md')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"保存到: {output_path}")


if __name__ == "__main__":
    main()