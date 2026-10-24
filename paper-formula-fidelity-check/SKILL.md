---
name: paper-formula-fidelity-check
description: "论文公式逐条核对流程：以原文 PDF 渲染页图（pdf_pages/page-NN.png）为唯一权威，禁止用 OCR 文本做符号级校验。当用户质疑某个符号时先当作转录 bug 假设回查原图，再决定是改文档还是加标注框。适用于论文解读、综述撰写、公式复核、用户说'这个符号不对''原文不是这样''帮我对照 PDF 检查公式'等场景。"
---

# Paper Formula Fidelity Check

以 PDF 渲染页图为唯一权威，逐条核对文档中的公式是否与原文一致。

## 前置条件

需要 `pdftoppm`（poppler-utils）将 PDF 导出为 PNG。运行 `scripts/extract_pdf_pages.sh <pdf> <output_dir>` 完成导出。

Windows 上若 poppler 不可用，用 Python `pdf2image` 库替代：

```python
from pdf2image import convert_from_path
images = convert_from_path("paper.pdf", dpi=200)
for i, img in enumerate(images, 1):
    img.save(f"pdf_pages/page-{i:02d}.png")
```

## 核对流程

### 1. 导出页图

```bash
bash scripts/extract_pdf_pages.sh paper.pdf pdf_pages
```

确认输出目录存在 `page-01.png`, `page-02.png`, ... 等文件。

### 2. 定位公式所在页

根据公式编号或上下文，确定其在原文 PDF 中的页码 N。

### 3. 多模态读图

用 Read 工具读取 `pdf_pages/page-NN.png`。Read 支持多模态，可直接"看到"图片中的公式排版。

### 4. 逐符号对照

将图片中的公式与文档中的 LaTeX 逐符号比对：

- 分子/分母位置
- 系数正负号
- 上下标内容与位置
- 希腊字母形态（ω vs ν, η vs h, ϑ vs θ）
- 矩阵元素的行列位置

### 5. 差异分类与处理

| 类型 | 判定 | 处理 |
|------|------|------|
| 转录错误 | 图片清晰，文档写错 | 修改文档 LaTeX |
| 原文自相矛盾 | 原文两处不一致 | 照原文呈现 + warnbox 标注 |
| 原文模糊不清 | 扫描件分辨率不足 | 加注释说明"原文此处不清" |

## 用户质疑某符号时

**不要为已有排版辩护。** 正确流程：

1. 假设是转录 bug
2. 打开对应页的 PNG 图片
3. 确认原文到底印了什么
4. 若原文确实与文档不同 → 改文档
5. 若原文与文档相同但用户仍质疑 → 检查原文是否自相矛盾，用 warnbox 标注

## 原文自相矛盾的处理

示例：Gao 2016 中公式 (7)/(11) 把 A_c 矩阵的 1 印在第三行，与公式 (6) 矛盾。

正确做法：照原文排版呈现，用 warnbox 标注两种读法：

```latex
\begin{tcolorbox}[colback=yellow!5!white, colframe=orange, title=原文不自洽]
公式 (6) 中 $A_c$ 的 $1$ 位于第\textbf{二}行，但公式 (7)/(11) 中位于第\textbf{三}行。
若取第二行，则\ldots；若取第三行，则\ldots。本文后续推导基于第 X 行的读法。
\end{tcolorbox}
```

若无 tcolorbox，用 `\begin{quote}\bfseries 注：原文此处不自洽。\end{quote}` 替代。

## 禁止行为

- 禁止用 OCR 文本（zotero_pdf_text.txt 等）做符号级校验
- 禁止凭推导"合理化"公式形式
- 禁止在用户截图指出不符后才被动修正
- 禁止用"可能是排版错误"为由自行调整公式而不标注
- 禁止静默"修正"原文矛盾

## OCR 已知系统性误读

以下误读在 zotero_pdf_text.txt 中已确认，遇到时务必回查原图：

| 原文 | OCR 误读为 |
|------|-----------|
| ω (omega) | ν (nu) 或 v |
| η (eta) | h |
| ϑ (vartheta) | 6 |
| ȧ (a with dot) | a |
| 希腊字母 | 形近拉丁字母 |

## 资源

- `scripts/extract_pdf_pages.sh` — PDF 页图导出脚本
