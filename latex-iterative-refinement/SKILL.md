---
name: latex-iterative-refinement
description: 中文LaTeX文档的迭代式编辑-编译-可视化校验-打开闭环工作流。当用户要求编辑tex文件并生成PDF、检查排版、修改后重新编译、或说「编译并打开」「检查排版」「看看公式对不对」时触发。包含错误/警告检查、溢出处理（tcolorbox breakable）、分页验证、pdftoppm渲染校验、WPS打开。与latex-cjk-pdf-verify-loop互补——后者只覆盖编译-打开，本技能覆盖完整的迭代校验闭环。
---

# LaTeX 迭代式编辑-编译-可视化校验闭环

## 工作流

每次编辑 tex 后执行以下闭环，不可跳过任何环节：

```
编辑 .tex
  → xelatex 编译
  → 检查编译日志（错误 + 警告）
  → 修复问题（如有），重新编译
  → pdftoppm 渲染关键页面为 PNG
  → Read 渲染图做视觉验证
  → WPS 打开 PDF
  → 等待用户反馈
  → 循环
```

## 1. 编译

使用 xelatex（中文文档必须）。编译命令示例：

```bash
cd "<tex所在目录>" && xelatex -interaction=nonstopmode "<文件名.tex>" 2>&1 | tee build.log
```

## 2. 检查编译日志

编译后立即检查 build log，按优先级处理：

### 2.1 致命错误（必须修复）

搜索 `^!` 或 `! ` 开头的行。常见错误：
- `Package pgfkeys Error: I do not know the key '/tcb/breakable'` → 缺少 `\tcbuselibrary{breakable}`
- `LaTeX Error: Environment xxx undefined` → 缺少宏包或拼写错误
- `! Emergency stop` → 语法未闭合

### 2.2 溢出警告（必须修复）

搜索 `Overfull`：
- `Overfull \hbox (Xpt too high)` → 水平溢出，内容超出页面右边距
- `Overfull \vbox (Xpt too high)` → 垂直溢出，内容超出页面底边

**处理策略见** [references/compilation-checks.md](references/compilation-checks.md)

### 2.3 低优先级警告（可忽略）

- `Underfull \hbox (badness 10000)` → 段落间距略大，不影响阅读
- `Package hyperref Warning: Token not allowed in a PDF string` → PDF 书签含数学符号，不影响正文
- `LaTeX Warning: Reference xxx undefined` → 交叉引用未定义，再编译一次通常消失

## 3. 溢出处理

### tcolorbox 溢出

如果 `Overfull \vbox` 出现在 tcolorbox 附近，原因是框内容超过一页但不可跨页。

**修复方法：**
1. 在导言区添加 `\tcbuselibrary{breakable}`
2. 给每个 `\newtcolorbox` 定义加上 `breakable` 选项：
```latex
\newtcolorbox{notebox}[1][]{..., breakable}
```

### 大公式/大表格溢出

- 公式：用 `\resizebox{\textwidth}{!}{...}` 缩放，或拆分为多行
- 表格：同上 `\resizebox`，或改用 `longtable` 跨页

## 4. 分页验证

修复溢出后，必须验证分页是否正确：

1. 用 pdftoppm 渲染受影响页面及前后页：
```bash
pdftoppm -png -r 150 -f <N-1> -l <N+1> "文件.pdf" chk/p
```
2. 用 Read 工具查看渲染的 PNG
3. 检查：
   - 公式是否被页面切断（公式应完整在一页内，或合理使用 split 跨页）
   - 表格是否被切断
   - tcolorbox 断开位置是否落在段落之间（不应切断公式或表格）
   - 页码是否压在框线上

## 5. 视觉验证

对修改涉及的页面做视觉检查：

```bash
pdftoppm -png -r 150 -f <起始页> -l <结束页> "文件.pdf" chk/v
```

用 Read 工具逐页查看 PNG，确认：
- 新增/修改的内容确实出现在正确位置
- 排版无异常（文字重叠、公式错位、框线断裂）
- 中文与公式/数字之间间距正常

## 6. 打开 PDF

使用 WPS Office 的 wpspdf.exe 打开（非系统默认阅读器）：

```bash
"/c/Users/<用户名>/AppData/Local/Kingsoft/WPS Office/<版本号>/office6/wpspdf.exe" "<PDF绝对路径>" &
```

查找 wpspdf.exe 路径：
```bash
find "/c/Users/<用户名>/AppData/Local/Kingsoft/WPS Office" -name "wpspdf.exe" 2>/dev/null
```

## 7. 用户反馈循环

打开 PDF 后等待用户反馈。用户常见纠正类型：

- **数量/表述错误**：如「三项」实际是「两项」——回到 tex 精确修改
- **单位不统一**：如 N/kg 与 m/s² 混用——统一为同一单位制
- **公式表述不准确**：如「没有具体公式」vs「有定义公式和控制律公式」——区分层次，精确表述
- **分页问题**：如内容显示不完全——检查 tcolorbox breakable 或 \resizebox

每次修改后回到步骤 1 重新执行闭环。

## 关键原则

1. **编译无错误无警告后才能打开 PDF**——不要把带 Overfull 的 PDF 给用户
2. **渲染验证不可跳过**——编译通过不代表排版正确，必须看 PNG
3. **分页验证不可跳过**——修复溢出可能导致页码变化，需重新检查
4. **用户纠正必须精确回改**——不要只改表面，要理解用户纠正的根因
