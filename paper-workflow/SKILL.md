---
name: paper-learning-assistant
description: "论文全流程综合工具（适配Codex/Claude/WorkBuddy）：检索论文并验证DOI、按四维度总结论文（中文摘要+公式推导+思路脉络+图表解读）、PDF转Markdown、生成LaTeX PDF、标注Zotero标签、并将解析PDF回写注册为Zotero正式子附件（scripts/zotero_attach.py）。当用户说'总结论文''分析这篇论文''帮我读论文''论文工作流''把解析放进Zotero/归档到Zotero'时触发。自动调度crossref-doi-verification、literature-summary、latex-iterative-refinement、convert-documents-to-markdown等子skill。"
---

# 论文全流程综合工具

> 从检索到总结到LaTeX生成的一站式论文工作流。适配 Claude Code、OpenAI Codex、WorkBuddy 等多平台。

## 平台适配说明

本 skill 设计为**平台无关**，核心逻辑在所有支持 Skill 系统的 AI 编码助手中通用：

| 平台 | 适配状态 | 说明 |
|---|---|---|
| **Claude Code** | 原生支持 | 完整功能，所有子 skill 可直接调度 |
| **OpenAI Codex** | 适配 | 使用 Codex 的 Skill 系统，PDF 处理依赖 `@firecrawl/anydoc` CLI |
| **WorkBuddy** | 适配 | 使用 WorkBuddy 的 Skill 加载机制，工作流逻辑完全兼容 |

**跨平台注意事项**：
- PDF 转 Markdown 统一使用 `convert-documents-to-markdown` skill（基于 `@firecrawl/anydoc`）
- LaTeX 编译需要本地安装 `xelatex`（TeX Live 或 MiKTeX）；**无 LaTeX 时走阶段3的降级路线**（浏览器 headless 打印 HTML→PDF，或 python-docx 生成 Word），不要因缺 LaTeX 而中断流程
- Zotero 集成需要本地 Zotero 数据库访问权限
- 公式验证需要 `pdftoppm`（Poppler 工具包）

## 触发条件

- "总结这篇论文" / "帮我读论文" / "分析这篇论文"
- "论文工作流" / "paper workflow"
- 用户提供PDF/DOI/论文标题，要求全面总结
- 要求生成论文的LaTeX排版总结文档
- 要求将PDF转换为Markdown格式
- **把解析/笔记/补充材料放进 Zotero**（"归档到Zotero""在Zotero里能看到解析""放到对应论文的附件里"）

## 工作流总览

```
阶段1: 检索与定位 → 阶段2: 四维度总结 → 阶段3: LaTeX生成 → 阶段4: Zotero标注 → 阶段5: 解析产物回写Zotero
```

每个阶段可独立执行，也可串联完成全流程。

---

## 阶段1: 论文检索与DOI验证

**输入**: 论文标题 / 关键词 / PDF文件 / 已知DOI

**调度规则**:

| 输入类型 | 调用skill | 说明 |
|---|---|---|
| 关键词/标题检索 | `giiisp-paper-search-apis` | 调用集思谱API检索，输出候选论文列表 |
| 深度调研 | `sci-employee-deep-research` | 需要系统性文献调研时 |
| 已知DOI需验证 | `crossref-doi-verification` | 验证DOI真实性，获取元数据和摘要 |
| 本地PDF文件 | `convert-documents-to-markdown` → `crossref-doi-verification` | 先将PDF转为Markdown提取文本，再用标题反查DOI |

**执行步骤**:

1. 根据输入类型选择检索方式
2. 获取论文元数据（标题、作者、期刊、年份、DOI）
3. 用 `crossref-doi-verification` 验证DOI（**绝不凭记忆写DOI**）
4. 下载或定位PDF全文
5. 输出验证后的论文信息卡片

**输出**: 论文信息卡片（标题、作者、期刊、年份、已验证DOI、摘要）

---

## 阶段2: 四维度论文总结

**输入**: 论文PDF全文 + 论文信息卡片

**PDF处理优先使用 `convert-documents-to-markdown`**：

```bash
# 将PDF转为Markdown（推荐）
npx -y @firecrawl/anydoc paper.pdf -o paper.md

# 如果转换失败（扫描件需要OCR）
npx -y @firecrawl/anydoc paper.pdf --ocr hosted -o paper.md
```

**调度规则**:

| 维度 | 方法 | 输出格式 |
|---|---|---|
| 中文摘要+核心贡献 | 阅读Markdown/PDF后提炼 | 结构化中文段落 |
| 公式逐步推导 | `paper-formula-fidelity-check` + `paper-formula-image-verification` | 逐步展开+物理含义 |
| 论文思路脉络 | 分析论文结构 | 流程图/脉络图 |
| 关键图表解读 | 提取并解读图表 | 图表编号+说明 |

**执行步骤**:

1. 用 `convert-documents-to-markdown` 将PDF转为Markdown（首选），或 `pdf-extractor` 提取文本
2. 用 `paper-formula-image-verification` 渲染PDF页面为PNG，以图片为准核对公式
3. 按四维度模板生成总结（模板见 `references/summary-template.md`）
4. 如论文在Zotero中，读取其标签和分类信息

**四维度总结模板**:

### 2.1 中文摘要与核心贡献

```
【研究背景】1-2句话说明研究领域和待解决问题
【核心问题】论文要解决的具体问题
【方法】提出的方法/模型/算法，一句话概括
【关键创新】与已有工作的区别（2-3点）
【主要结论】核心实验结果和结论
【局限性】作者承认的不足或可改进方向
```

### 2.2 公式逐步推导

对论文中的每个核心公式，按以下格式展开：

```
公式编号: (X)
原始形式: [LaTeX公式]
推导步骤:
  步骤1: [从哪来，用了什么假设/定理]
  步骤2: [中间变换，说明每步的数学操作]
  ...
物理/工程含义: [这个公式说明了什么]
符号说明: [每个符号的含义和单位]
```

**重要**: 公式必须以PDF渲染图为准（用 `paper-formula-fidelity-check`），禁止凭OCR文本转录。

### 2.3 论文思路脉络

```
问题提出 → 动机分析 → 方法设计 → 理论分析 → 实验验证 → 结论
    ↑           ↑           ↑           ↑           ↑
 [什么缺口]  [为什么现有  [核心idea   [收敛性/    [对比baselines
             方法不行]    是什么]     稳定性证明]  消融实验]
```

标注关键转折点（如"作者在此处指出已有方法的XX缺陷，因此提出YY"）。

### 2.4 关键图表解读

对论文中每个重要图表：

```
图X: [图题]
位置: 第N页
内容: [图中展示了什么]
说明: [这个图支撑了论文的哪个论点]
关键观察: [从图中能读出的关键信息]
```

---

## 阶段3: 论文总结 PDF 生成

**输入**: 四维度总结内容

### 3.0 环境检测与降级路线（先执行，决定走哪条路）

其他用户环境不一定装了 LaTeX。**第一步先检测**，再选生成方式：

```bash
xelatex --version 2>/dev/null && echo "有LaTeX" || echo "无LaTeX，走降级路线"
```

| 路线 | 适用 | 产物质量 | 依赖 |
|---|---|---|---|
| **A. LaTeX 路线** | 检测到 xelatex | 最佳（专业排版、原生公式） | TeX Live / MiKTeX |
| **B. HTML → 浏览器打印 PDF** | 无 LaTeX（**默认降级**） | 良好（中文用系统字体，公式用 Unicode 符号） | 零安装，Chrome/Edge 几乎必装 |
| **C. python-docx 生成 Word** | 用户想要可编辑文档 | 良好（可在 Word/WPS 中继续编辑、另存 PDF） | `pip install python-docx` |

**降级路线 B 的具体做法**（无 LaTeX 时）：

1. 把四维度总结生成为排版良好的单文件 HTML（内联 CSS）：
   - 中文正文用系统字体栈：`font-family: "Microsoft YaHei","PingFang SC","Noto Sans CJK SC",sans-serif;`
   - 公式用 Unicode 数学符号（∑ ∫ √ α β ρ ∂ ≈ ≤ → 等），**不要**依赖 MathJax/KaTeX CDN（headless 离线环境会渲染失败）
   - 加 `@media print` 样式：A4、页边距 2cm、标题层级清晰
2. 用浏览器 headless 打印为 PDF（按优先级探测）：
   ```bash
   # Windows（Edge 几乎必装）
   "/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" --headless --disable-gpu --print-to-pdf="输出.pdf" "file:///绝对路径/总结.html"
   # macOS
   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --print-to-pdf="输出.pdf" "file:///绝对路径/总结.html"
   # Linux
   google-chrome --headless --print-to-pdf="输出.pdf" "file:///绝对路径/总结.html"
   ```
3. 校验产物：`pdfinfo` 确认页数正常，或 `pdftoppm` 渲染首页目视检查。

**降级路线 C 的具体做法**（用户要可编辑文档时）：用 python-docx 生成 .docx（标题样式 + 公式用 Unicode），交付时说明"可在 Word/WPS 中打开继续编辑，文件→另存为→PDF 即可导出 PDF"。

> 降级路线的产物同样可进入阶段5 回写 Zotero（`zotero_attach.py` 已按扩展名识别 contentType，docx/html 都支持）。

### 3.1 LaTeX 路线（有 LaTeX 时）

**调度规则**:

| 需求 | 调用skill |
|---|---|
| 编辑tex并编译 | `latex-iterative-refinement` |
| 快速编译验证 | `latex-cjk-pdf-verify-loop` |
| 聊天中问答后写入 | `latex-iterative-edit-verify` |

**执行步骤**:

1. 根据总结内容生成LaTeX源文件（使用ctex/xeCJK中文支持）
2. 用 `latex-iterative-refinement` 闭环编译：
   - `xelatex` 编译 → 检查日志 → 修复错误 → 重新编译
   - `pdftoppm` 渲染关键页 → 视觉验证
   - WPS打开PDF供用户确认
3. 迭代修改直到用户满意

**LaTeX模板要点**:

```latex
\documentclass[12pt,a4paper]{ctexart}
\usepackage{amsmath,amssymb,amsthm}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{tcolorbox}
\tcbuselibrary{breakable}

\title{论文总结: [论文标题]}
\author{自动生成}
\date{\today}

\begin{document}
\maketitle
\tableofcontents

\section{论文信息}
% 标题、作者、期刊、DOI链接

\section{中文摘要与核心贡献}
% 四维度2.1内容

\section{公式推导}
% 四维度2.2内容，每个公式一个subsection

\section{论文思路脉络}
% 四维度2.3内容，可用tikz画流程图

\section{关键图表解读}
% 四维度2.4内容

\section{个人思考与延伸}
% 可选：对该论文的评注和后续研究方向

\end{document}
```

---

## 阶段4: Zotero标注（简单集成）

**输入**: 论文信息 + 总结内容

**执行步骤**:

1. 检查论文是否已在Zotero库中（通过DOI匹配）
2. 如在库中：
   - 读取该论文的Zotero标签和分类
   - 在总结文档中标注：`【Zotero标签: tag1, tag2 | 分类: collection_name】`
   - 读取用户在该论文上的笔记（如有），融入总结
3. 如不在库中：
   - 提示用户可手动添加到Zotero
   - 建议标签（基于论文关键词自动生成）

**调度**: 使用 `literature-summary` skill中的Zotero数据库查询逻辑（读取 `zotero.sqlite`）。

---

## 阶段5: 解析产物回写 Zotero（注册为正式子附件）

**输入**: 阶段3生成的解析PDF + 论文在Zotero中的条目

**核心原则（必须先理解，否则会做错）**:

> Zotero 的附件列表以 **sqlite 数据库记录** 为准，不以文件系统为准。
> - `Zotero/storage/<KEY>/` 中的 `<KEY>` 是 **附件条目自己的 key**，不是论文条目的 key；
> - 一个附件条目对应一个独立 storage 文件夹（**一文件夹一附件**）；
> - **直接把文件拷进已有 storage 文件夹，Zotero 不会显示它，也不会同步** —— 用户会看到"文件放进去了但界面里没有"。
>
> 所以要让解析文件出现在论文的下拉列表里，必须：**新建 key → 建独立文件夹 → 放文件 → 写数据库 → 校验**。

**工具**: `scripts/zotero_attach.py`（本skill自带，见下节）

### 执行步骤

1. **定位论文条目**（先查再写，别猜）：
   ```bash
   # 复制数据库后只读查询（Zotero 运行时会锁原文件）
   cp ~/Zotero/zotero.sqlite ./zt.sqlite
   python -c "
   import sqlite3; con=sqlite3.connect('zt.sqlite')
   # 按标题找论文条目（itemTypeID != 3 才是论文，3 是 attachment）
   print(con.execute(\"SELECT itemID,key FROM items WHERE itemID=597\").fetchone())
   "
   ```
   确认拿到的是**论文父条目的 key**（形如 `BSQC5T58`），而不是 PDF 附件的 key。

2. **先预演**（默认行为，不加 `--confirm` 绝不写入）：
   ```bash
   python scripts/zotero_attach.py --file "解析.pdf" --parent-key <论文条目KEY> --title "论文解析（XXX）"
   ```

3. **让用户完全退出 Zotero**（文件→退出，确认托盘图标也退出），脚本会自动检测进程与数据库锁并在运行时拒绝写入。

   > **为什么必须完全退出？**（用户常问"能不能不关 Zotero"，答案：用本脚本的 sqlite 直写方式**不能**）
   > - **内存缓存覆盖**：Zotero 把条目数据缓存在内存里，外部写库它看不见；它下次提交自己的事务时，会用旧缓存覆盖你的改动，刚挂上的附件会直接消失。
   > - **SQLite 锁冲突**：Zotero 持有连接与 WAL 锁，外部并发写入可能触发 `database is locked`，严重时损坏库文件。
   > - **索引与同步不一致**：`fulltext.sqlite`（全文索引）、`version`/`synced` 标记不会自动更新；若开着官方同步，最坏触发云端"最后写入者胜"覆盖数据。
   >
   > 注意 Windows 上**托盘图标也要退出**（关窗口 ≠ 退出），`Get-Process zotero` 无输出才算退干净。
   >
   > **若用户不想关闭 Zotero**，给出两条替代路径：
   > - **本地 API 模式（推荐，本脚本已内置 `--api`）**：Zotero 10+ 的本地 API（`http://localhost:23119/api/`）支持写入（7–9 仅只读），Zotero **运行中**即可挂载，改动立即在 UI 可见、正常参与同步、自动维护全文索引。首次写入会弹窗授权，请用户点 **Always Allow**（可复用；只点 Allow 则每个写请求都要再弹一次）。前置：设置 → 高级 → 勾选"允许此计算机上的其他应用程序与 Zotero 通信"。用法：
   >   ```bash
   >   python scripts/zotero_attach.py --api-probe                                   # 先探测可用性
   >   python scripts/zotero_attach.py --api --file "解析.pdf" --parent-key <KEY> --title "…" --confirm
   >   python scripts/zotero_attach.py --api --jobs jobs.json --confirm              # 批量
   >   ```
   > - **手动 UI 导入**（零风险，适合单篇）：右键论文 → 添加附件 → 附加存储文件的副本 → 选解析 PDF。
   >
   > **模式选择**：优先 `--api`；用户是 Zotero 7–9（本地 API 只读）或 API 未启用时，退回 sqlite 直写模式（需退出 Zotero）。

4. **正式写入**（脚本会自动备份数据库）：
   ```bash
   python scripts/zotero_attach.py --file "解析.pdf" --parent-key <论文条目KEY> --title "论文解析（XXX）" --confirm
   ```

5. **回读校验**：脚本内置回读，确认 itemID / key / parentItemID / path / title 正确，且孤儿记录为 0。

6. 请用户重新打开 Zotero，展开论文条目应能看到新附件。

### 数据库写入细节（出错时排查用）

需写 4 张表：

| 表 | 关键字段 |
|---|---|
| `items` | `itemTypeID=3`(attachment), `libraryID=1`, `key`=新8位key, `version=0`, `synced=0`, `clientVersion=0` |
| `itemAttachments` | `parentItemID`=论文条目ID, `linkMode=0`, `contentType='application/pdf'`, `path='storage:文件名'`, `syncState=0`, `storageModTime`=毫秒时间戳, `storageHash`=文件MD5 |
| `itemDataValues` | `value`=附件显示标题 |
| `itemData` | `itemID` + `fieldID=1`(title) + `valueID` |

Zotero 的 item key 字符集：`23456789ABCDEFGHIJKLMNPQRSTUVWXYZ`（不含易混淆的 0/1/I/O），长度 8。

### 安全红线

1. **必须先退出 Zotero** —— 运行中写库会导致 Zotero 内存状态与数据库不一致。
2. **必须先备份** —— 脚本自动备份为 `zotero.sqlite.bak-<时间戳>`；回滚＝退出 Zotero 后用备份覆盖。
3. **默认只预演** —— 不加 `--confirm` 一律不写入，防止误写真实文献库。
4. **首次使用建议先在临时副本库演练**：`--data-dir ./_zttest`（复制 zotero.sqlite + 建空 storage/ 目录）。
5. **幂等** —— 同一父条目下已存在同名附件时自动跳过，不会产生重复条目。

---

## 子Skill索引

本skill调度以下已有skill，按需加载：

| 阶段 | Skill名称 | 路径 |
|---|---|---|
| 检索 | `giiisp-paper-search-apis` | 插件: research-copilot |
| 深度调研 | `sci-employee-deep-research` | 插件: research-copilot |
| DOI验证 | `crossref-doi-verification` | 用户级skills |
| **PDF转Markdown** | **`convert-documents-to-markdown`** | **用户级skills（核心依赖）** |
| PDF提取 | `pdf-extractor` | 用户级skills（备用） |
| 公式核对 | `paper-formula-fidelity-check` | 用户级skills |
| 公式验证 | `paper-formula-image-verification` | 用户级skills |
| 文献总结 | `literature-summary` | 用户级skills |
| LaTeX编译 | `latex-iterative-refinement` | 用户级skills |
| LaTeX快速编译 | `latex-cjk-pdf-verify-loop` | 用户级skills |
| LaTeX交互编辑 | `latex-iterative-edit-verify` | 用户级skills |
| 论文详解 | `latex-academic-paper-explanation` | 用户级skills |
| 引用审计 | `papercheck` | 插件: research-copilot |
| 科研导师 | `research-mentor` | 用户级skills |

### 本skill自带脚本

| 阶段 | 脚本 | 说明 |
|---|---|---|
| 阶段5 | `scripts/zotero_attach.py` | 把本地PDF注册为Zotero论文的子附件（预演/备份/批量/幂等/回读校验） |

## 快速使用示例

**示例1: 给一篇PDF做全面总结**
```
用户: 帮我总结这篇论文 [附PDF]
→ 阶段1: convert-documents-to-markdown转Markdown + crossref验证DOI
→ 阶段2: 四维度总结
→ 阶段3: 生成LaTeX PDF
→ 阶段4: 检查Zotero标签
```

**示例2: 检索并总结某方向论文**
```
用户: 帮我找几篇关于CBF多机器人避碰的最新论文并总结
→ 阶段1: giiisp-paper-search-apis检索
→ 阶段2: 对每篇论文做四维度总结
→ 阶段3: 汇总生成对比LaTeX文档
```

**示例3: 只生成LaTeX总结文档**
```
用户: 把刚才的论文总结生成PDF
→ 阶段3: latex-iterative-refinement编译
```

**示例4: 将PDF转为Markdown**
```
用户: 把这篇PDF转成Markdown
→ 直接调用 convert-documents-to-markdown
→ 输出 .md 文件
```

**示例5: 把解析归档到Zotero论文的附件列表**
```
用户: 把这篇论文的解析放到Zotero里 / 我想在Zotero展开论文时看到解析
→ 阶段5:
   1. 查 zotero.sqlite 确认【论文父条目key】（注意不是PDF附件的key）
   2. python scripts/zotero_attach.py --file 解析.pdf --parent-key <KEY> --title "论文解析（…）"   ← 预演
   3. 请用户完全退出 Zotero（脚本会检测进程/锁并拒绝）
   4. 加 --confirm 实际写入（自动备份 + 回读校验）
   5. 请用户重开 Zotero，展开论文即可看到新附件
```

## 注意事项

1. **DOI必须验证**: 绝不凭记忆写DOI，必须通过Crossref API验证
2. **公式以图为准**: 公式核对必须用PDF渲染图，不用OCR文本
3. **编译用xelatex**: 中文文档必须用xelatex，不用pdflatex；若环境没有 LaTeX，按阶段3.0 走降级路线（浏览器打印 HTML→PDF / python-docx），不要卡住
4. **WPS打开PDF**: 编译后用WPS打开，不用系统默认阅读器
5. **聊天公式用Unicode**: 对话中用Unicode数学符号，不用LaTeX原始语法
6. **PDF转Markdown优先**: 阶段2优先使用 `convert-documents-to-markdown`，失败时回退到 `pdf-extractor`
7. **Zotero回写不是拷贝文件**: 阶段5必须写数据库注册附件条目，只把文件塞进 storage 文件夹用户是看不到的
8. **写Zotero库前三件事**: 退出Zotero → 备份zotero.sqlite → 先预演（不加 `--confirm` 不写入）

---

## 版权与致谢

本 skill 的设计与实现借鉴、结合了以下来源：

- **网络公开 Skill**：参考了 开源社区、GitHub 上开源的 AI 编码助手 Skill 设计模式
- **开源数据**：部分工作流逻辑参考了 GitHub 上的开源论文处理工具和研究工作流项目
- **API 服务**：集成了 Crossref、OpenAlex、Giiisp/集思谱等公开学术 API

本 skill 基于 MIT 许可证开源。如引用内容涉及您的知识产权，请随时联系，我们将及时修改或删除。

**作者**: zyj-cool
**仓库**: https://github.com/zyj-cool/paper-learning-assistant
**许可证**: MIT
