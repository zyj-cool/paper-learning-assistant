---
name: latex-cjk-pdf-verify-loop
description: "中文 LaTeX（ctex/xeCJK）文档的编译—可视化校验—打开闭环。当用户要求编译 .tex 并验证排版（公式、表格、中文混排），或说「编译并打开」「检查排版」「看看公式对不对」时触发。包含 PDF 无法直接 Read 时的 pdftoppm→PNG 降级路径，以及编译后用 WPS wpspdf.exe 打开。"
---

# LaTeX CJK PDF Verify Loop

中文 LaTeX 文档从编译到目视校验再到打开的完整闭环。

## 流程

### 1. 编译（两遍）

```bash
xelatex -interaction=nonstopmode <file.tex>
xelatex -interaction=nonstopmode <file.tex>
```

第二遍解决 TOC、交叉引用和参考文献编号。`-interaction=nonstopmode` 遇错不中断，可能产出不完整 PDF——先查错再打开。

### 2. 查错

```bash
grep '^! ' <file.log>
grep -c 'Overfull' <file.log>
grep -c 'Underfull' <file.log>
```

- `^! ` 行是致命错误，必须修复
- Overfull/Underfull 是警告，数量过多时检查溢出段落

### 3. 可视化校验（pdftoppm → PNG → Read）

Read 工具直接读 PDF 会报 password-protected 失败。用 pdftoppm 渲染目标页为 PNG 后逐页目视核对：

```bash
pdftoppm -png -r 200 -f <first_page> -l <last_page> <file.pdf> /tmp/tex-verify-page
```

生成 `/tmp/tex-verify-page-<page>.png`，用 Read 工具逐张读取，检查：

- 公式是否正确渲染（上下标、分式、矩阵、中文下标）
- 表格是否溢出页边距
- 中文与西文/数字混排间距
- 图表标题与交叉引用编号

校验完毕后清理临时文件：

```bash
rm -f /tmp/tex-verify-page-*.png
```

### 4. 用 WPS 打开 PDF

用户要求用 WPS Office 打开，不用系统默认阅读器：

```bash
"/c/Program Files (x86)/Kingsoft Office Software/WPS Office/12.1.0.24034/office6/wpspdf.exe" "<absolute-path-to-pdf>" &
```

版本号目录会随更新变化。路径失效时重新定位：

```bash
find "/c/Program Files (x86)/Kingsoft Office Software" -name "wpspdf.exe" 2>/dev/null
```

打开后可用 `powershell -c "Get-Process wps"` 确认进程已启动。

## 注意事项

- 编辑 .tex 后应主动重新编译，无需等用户要求
- 若 pdftoppm 不可用，检查 Poppler 是否安装（Git Bash / MSYS2 环境通常自带）
- 中文路径传给 wpspdf.exe 时使用绝对路径，避免相对路径解析问题
