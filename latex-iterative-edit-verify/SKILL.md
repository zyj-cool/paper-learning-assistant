---
name: latex-iterative-edit-verify
description: "中文LaTeX文档的迭代编辑—编译—校验—WPS打开闭环。当用户问概念问题后说\"放进去\"\"补充进去\"\"写进去\"\"加进去\"\"要\"\"好的\"（对\"要不要补进PDF\"的肯定回答），或说\"重新生成pdf\"时触发。覆盖：聊天用Unicode数学回答（不用LaTeX语法）；编辑tex添加内容；xelatex编译与错误修复（pgfkeys逗号标题需花括号、breakable需\\tcbuselibrary{breakable}、overfull vbox诊断）；pdftotext+awk定位新内容页码；pdftoppm渲染验证；PowerShell Start-Process打开PDF（兼容中文路径）。编译/校验/打开的基础操作详见latex-iterative-refinement和latex-cjk-pdf-verify-loop。"
---

# LaTeX Iterative Edit–Verify

中文 LaTeX 文档的"聊天问答 → 编辑写入 → 编译校验 → 打开"迭代闭环。

## 触发模式

用户说以下任一关键词时启动本流程：
- "放进去" "补充进去" "写进去" "加进去"
- "要" "好的" "可以" "行"（对"要不要补进PDF"的肯定回答）
- "重新生成pdf" "编译一下"

## 聊天中的公式显示

聊天回复用 **Unicode 数学**，不用 LaTeX 语法：
- ẋ、ẍ、Δ、τ、ω、ρ、δ、Σ 等直接写
- 例：`ẋ_{i-1} − ẋ_i` 而非 `$\dot{x}_{i-1} - \dot{x}_i$`
- 复杂公式分多行纯文本，或用文字描述结构
- PDF 文档内仍用 LaTeX 语法（编译器处理）

## 编辑流程

1. 用 Grep 定位 tex 文件中相关段落
2. 用 Read 查看上下文
3. 用 Edit 插入/修改内容
4. 立即编译（不等用户要求）

## 编译与查错

```bash
cd "<tex目录>"
xelatex -interaction=nonstopmode "<file.tex>" 2>&1 | tee build.log
```

查错顺序：
```bash
grep '^! ' build.log          # 致命错误
grep 'pgfkeys' build.log      # pgfkeys 键错误
grep -c 'Overfull' build.log  # 溢出警告
grep -c 'Underfull' build.log # 欠满警告
```

### 常见问题修复

**pgfkeys 逗号问题**：tcolorbox 的 title 含逗号时报 `I do not know the key`。
修复：title 参数整体加花括号 `title={含,逗号的标题}`。

**breakable 未加载**：报 `I do not know the key '/tcb/breakable'`。
修复：在导言区加 `\tcbuselibrary{breakable}`，且放在 `\usepackage{tcolorbox}` 之后。

**Overfull \vbox**：框或表格溢出页边距。
诊断：`grep 'Overfull \\vbox' build.log` 看溢出量。
修复：给 tcolorbox 加 `breakable` 选项，或用 `\resizebox{\textwidth}{!}{...}` 缩放表格。

## 定位新内容页码

用 pdftotext 提取文本，awk 搜索关键词：
```bash
pdftotext -layout "<file.pdf>" ul.txt
awk '/关键词/{print NR, $0}' ul.txt
```
结合编译 log 中的页码输出 `[N]` 定位新内容所在页。

## 渲染验证

```bash
pdftoppm -png -r 200 -f <页> -l <页> "<file.pdf>" chk/page
```
用 Read 工具读取生成的 PNG，目视检查新增内容的排版。

## 打开 PDF

用 PowerShell Start-Process（兼容中文路径）：
```bash
powershell -c "Start-Process 'wpspdf' -ArgumentList '<绝对路径PDF>'"
```
若 wpspdf 不在 PATH，用绝对路径：
```bash
powershell -c "Start-Process '<wpspdf.exe绝对路径>' -ArgumentList '<PDF绝对路径>'"
```
定位 wpspdf.exe：
```bash
find "/c/Program Files (x86)/Kingsoft Office Software" -name "wpspdf.exe" 2>/dev/null
```

## 与 latex-iterative-refinement 的关系

本 Skill 聚焦"迭代编辑"场景（用户问概念 → 写入 PDF）。
编译两遍、pdftoppm 渲染、WPS 打开等基础操作详见 `latex-iterative-refinement` 和 `latex-cjk-pdf-verify-loop`。
