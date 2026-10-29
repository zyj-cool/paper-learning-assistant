# 论文学习助手 · Skills 集合

> 一套面向科研工作者的 AI 技能体系，覆盖论文从检索、阅读、总结、写作到排版投稿的全流程。

[![Skills](https://img.shields.io/badge/skills-13-blue)](#)
[![License](https://img.shields.io/badge/license-MIT-green)](#)
[![Platform](https://img.shields.io/badge/platform-Claude%20%7C%20Codex%20%7C%20WorkBuddy-purple)](#)

---

## 这是什么？

这是为 AI 编码助手打造的一套 **论文科研技能包**。每个 skill 是一个独立的能力模块，加载后就能在对应场景下自动触发，把通用 AI 变成你的专属科研助手。

**平台适配：**
- ✅ **Claude Code** — 原生支持，完整功能
- ✅ **OpenAI Codex** — 完全适配，使用 Codex Skill 系统
- ✅ **WorkBuddy** — 完全适配，工作流逻辑兼容

**适合谁用：** 研究生、博士生、科研工作者——尤其是控制理论、电子信息、自动化、计算机方向，但大部分技能对所有理工科通用。

---

## 技能全景图

![技能架构图](assets/skills-architecture.png)

> 三层架构：**文献检索层** → **论文理解层** → **输出与排版层**，由 `Paper Learning Assistant（论文学习助手）` 统一调度，`research-mentor` 作为综合入口覆盖写作、审稿、投稿、绘图全流程。

---

## 技能清单

### 核心工作流

| Skill | 一句话说明 | 触发词 |
|---|---|---|
| **论文学习助手**（`paper-learning-assistant`） | 论文全流程综合工具（适配Codex/Claude/WorkBuddy）。检索→四维度总结→PDF转Markdown→LaTeX PDF→Zotero标注→**解析产物回写Zotero**，一站式完成 | "总结论文""帮我读论文""论文工作流""把解析放进Zotero" |
| **latex-academic-paper-explanation** | 论文详解工具。深度解读单篇论文，生成六章结构LaTeX文档 | "论文详解""详细解读""整理成文档" |

### 文献检索与验证

| Skill | 一句话说明 | 触发词 |
|---|---|---|
| **crossref-doi-verification** | DOI 真实性验证。通过 Crossref + OpenAlex API 验证 DOI，获取摘要，绝不凭记忆编造 | "验证DOI""查DOI""参考文献审计" |
| **giiisp-paper-search-apis** | 集思谱论文检索。支持 OA 标题摘要检索和 arXiv 多字段检索 | "检索论文""找论文""文献初筛" |
| **sci-employee-deep-research** | 深度文献调研。系统性检索+关键词拆解+证据组织，输出可核验研究报告 | "深度调研""开题调研""文献综述" |

### 论文阅读与理解

| Skill | 一句话说明 | 触发词 |
|---|---|---|
| **literature-summary** | Zotero 文献总结。从 Zotero 提取 PDF → 结构化中文总结 → 导出 Word → 可选上传飞书 | "文献总结""paper summary" |
| **pdf-extractor** | PDF 内容提取。用 pdfplumber 提取文本、表格、图片，支持批量处理 | "提取PDF""PDF转文本" |
| **convert-documents-to-markdown** | 文档格式转换。Word/PPT/Excel/PDF → Markdown（基于 @firecrawl/anydoc） | "转换文档""PDF转Markdown""读取PDF" |
| **paper-formula-fidelity-check** | 公式逐条核对。以 PDF 渲染图为唯一权威，禁止 OCR 文本做符号级校验 | "公式不对""对照PDF检查公式" |
| **paper-formula-image-verification** | 公式图像验证。逐符号比对（分子分母、上下标、希腊字母），以图为准 | "核对公式""公式验证" |

### LaTeX 编译与排版

| Skill | 一句话说明 | 触发词 |
|---|---|---|
| **latex-iterative-refinement** | 迭代式编辑-编译-校验闭环。xelatex 编译 → 查错 → pdftoppm 渲染 → WPS 打开 | "编译并打开""检查排版""重新生成PDF" |
| **latex-cjk-pdf-verify-loop** | 中文 LaTeX 快速编译验证。两遍编译 + 可视化校验 + WPS 打开 | "编译tex""看看公式对不对" |
| **latex-iterative-edit-verify** | 聊天问答后写入 tex 的闭环。聊天中用 Unicode 数学，编辑后自动编译验证 | "放进去""补充进去""写进去" |

### 科研写作与投稿

| Skill | 一句话说明 | 触发词 |
|---|---|---|
| **research-mentor** | 科研导师。论文写作/重构/润色/审稿回复/投稿检查/科研绘图/研究生陪跑，29 个参考文件 | 几乎所有科研需求 |

---

## 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/zyj-cool/paper-learning-assistant.git

# 复制到对应平台的 skill 目录
# Claude Code:
cp -r paper-learning-assistant/* ~/.claude/skills/

# OpenAI Codex:
cp -r paper-learning-assistant/* ~/.codex/skills/

# WorkBuddy:
cp -r paper-learning-assistant/* ~/.workbuddy/skills/

# 或在对应平台中执行 reload 命令
```

### 典型使用场景

**场景 1：拿到一篇 PDF，快速总结**
```
你: 帮我总结这篇论文 [附PDF]
AI: [自动触发 Paper Learning Assistant（论文学习助手）]
  → convert-documents-to-markdown 转 Markdown + crossref 验证DOI
  → 四维度总结（摘要/公式/脉络/图表）
  → 生成LaTeX PDF
  → 标注Zotero标签
```

**场景 2：深度精读一篇论文**
```
你: 论文详解 [附PDF]
AI: [自动触发 latex-academic-paper-explanation]
  → 六章详解文档（概览/背景/方法/理论/实验/思考）
  → 编译为LaTeX PDF
  → WPS打开
```

**场景 3：检索某方向最新论文**
```
你: 帮我找几篇关于CBF多机器人避碰的最新论文
AI: [自动触发 giiisp-paper-search-apis]
  → 检索候选论文
  → 验证每篇DOI
  → 输出论文信息卡片
```

**场景 4：写论文时检查公式**
```
你: 这个符号不对，帮我对照PDF检查公式
AI: [自动触发 paper-formula-fidelity-check]
  → 渲染PDF页面为PNG
  → 逐符号比对
  → 标注差异类型
```

**场景 5：将 PDF 转为 Markdown**
```
你: 把这篇PDF转成Markdown
AI: [自动触发 convert-documents-to-markdown]
  → npx @firecrawl/anydoc paper.pdf -o paper.md
  → 输出 .md 文件
```

---

## 新增功能：解析产物回写 Zotero（阶段5）

> 2026-10-29 更新。让 AI 生成的**论文解析 PDF** 直接出现在 Zotero 论文条目的**附件下拉列表**里，而不是躺在一个你看不到的文件夹里。

### 为什么需要它

Zotero 的附件列表以 **sqlite 数据库记录**为准，不以文件系统为准：

```
Zotero/storage/<KEY>/     ← 这是【附件条目自己的 key】，不是论文条目的 key
                          ← 一个附件条目 = 一个独立 storage 文件夹
```

所以**直接把解析 PDF 拷进论文 PDF 所在文件夹是无效的**：

- 文件确实在磁盘上，资源管理器能看到；
- 但 Zotero 界面里**不会出现**，也**不会同步**。

要让它显示，必须：新建 key → 建独立文件夹 → 放文件 → **写数据库** → 校验。本 skill 的 `scripts/zotero_attach.py` 把这一串动作封装成一条命令。

### ⚠️ 使用前必读：为什么必须先完全退出 Zotero

**结论：本 skill 采用的方法是直接写 `zotero.sqlite`，因此执行 `--confirm` 前必须让 Zotero 完全退出。**这不是脚本的保守设计，而是硬性要求。

Zotero 运行时不能从外部改库，原因有三：

| # | 风险 | 后果 |
|---|---|---|
| 1 | **内存缓存覆盖** | Zotero 把条目数据缓存在内存中，外部写库它**看不见**。它下一次提交自己的事务时，会用旧缓存覆盖你的改动——你刚挂上的附件可能直接消失 |
| 2 | **SQLite 锁冲突** | Zotero 持有数据库连接与 WAL 锁，外部并发写入可能触发 `database is locked`，严重时损坏库文件 |
| 3 | **索引与同步状态不一致** | `fulltext.sqlite`（全文索引）、`version`/`synced` 标记不会自动更新，可能导致界面显示异常；若开着官方同步，最坏情况触发云端"最后写入者胜"，把你的改动或云端数据覆盖掉 |

**确认退干净的方法**（脚本会自动检测，但建议自己确认一次）：

1. Zotero 菜单 **文件 → 退出**（不是关窗口、不是最小化）；
2. Windows 上**右下角托盘图标也要退出**，这是最常见的漏网之处；
3. `Get-Process zotero` 无输出才算真的退出。

> 脚本若提示"Zotero 仍在运行"而你确信已退出，多半就是托盘进程还活着。

### 不想关闭 Zotero？两条免关闭路径（2026-10-29 起脚本已内置 API 模式）

| 方案 | 是否需关闭 | 说明 |
|---|---|---|
| **A. 本地 API 模式（推荐）** | 否 | 脚本加 `--api` 即可在 Zotero **运行中**批量挂载：`zotero_attach.py --api --jobs jobs.json --confirm`。走 `http://localhost:23119/api/`，**Zotero 10.0 起本地 API 支持写入**（7–9 只能读）。前置：设置 → 高级 勾选"允许此计算机上的其他应用程序与 Zotero 通信"；首次写入弹窗授权，请点 **Always Allow**（密钥缓存于 `~/.zotero_attach_local_key.json`）。API 写入即时生效、正常参与同步、自动维护全文索引，比 sqlite 直写更安全 |
| **B. Zotero 界面手动导入** | 否 | 右键论文 → **添加附件** → **附加存储文件的副本** → 选中解析 PDF。官方路径、零风险，缺点是得一篇一篇点 |
| **C. 本脚本 sqlite 直写** | **是** | 适合 Zotero 7–9（本地 API 只读）或 API 未启用的场景，快，但必须退出 Zotero |

先用 `python scripts/zotero_attach.py --api-probe` 探测本地 API 是否可用，再决定走 A 还是 C。

### 用法

```bash
# ① 先预演（默认行为，不加 --confirm 绝不写入）
python scripts/zotero_attach.py \
  --file "论文解析_XXX.pdf" \
  --parent-key <论文条目KEY> \
  --title "论文解析（XXX）"

# ② 完全退出 Zotero 后，确认执行（自动备份 + 回读校验）
python scripts/zotero_attach.py \
  --file "论文解析_XXX.pdf" \
  --parent-key <论文条目KEY> \
  --title "论文解析（XXX）" --confirm

# ③ 批量（JSON）
python scripts/zotero_attach.py --jobs jobs.json --confirm
```

**定位论文条目 key**（注意取的是论文条目，不是 PDF 附件）：

```bash
cp ~/Zotero/zotero.sqlite ./zt.sqlite     # Zotero 运行时会锁原文件，先复制
python -c "import sqlite3;print(sqlite3.connect('zt.sqlite').execute(
  \"SELECT itemID,key FROM items WHERE itemTypeID!=3 AND itemID=597\").fetchone())"
```

### 脚本已内置的安全机制

| 机制 | 说明 |
|---|---|
| 默认只预演 | 不加 `--confirm` 一律不写库，防止误写真实文献库 |
| 进程/锁检测 | Zotero 未退出时直接拒绝写入 |
| 自动备份 | 写入前备份为 `zotero.sqlite.bak-<时间戳>`，可一键回滚 |
| 幂等 | 同一父条目下已存在同名附件自动跳过，不产生重复 |
| 回读校验 | 写入后回读 itemID/key/父条目/path/标题并打印 |
| 失败回滚 | 任何异常 `rollback`，不留下半截数据 |
| 临时库演练 | `--data-dir ./_zttest` 可在副本库上试跑，不碰真实数据 |

### 数据库写入细节（排查用）

写 4 张表：`items`（itemTypeID=3 附件条目）、`itemAttachments`（父条目/路径/MD5）、`itemDataValues`（显示标题）、`itemData`（fieldID=1 即 title）。
Zotero 的 item key 字符集为 `23456789ABCDEFGHIJKLMNPQRSTUVWXYZ`（不含易混淆的 0/1/I/O），长度 8。

---

## 技能间的协作关系

这套技能不是孤立存在的，它们通过 `Paper Learning Assistant（论文学习助手）` 统一调度，形成完整闭环：

![协作关系流程图](assets/workflow-flowchart.png)

每个环节都可以**单独使用**，也可以**串联执行**。比如你可以只用 `crossref-doi-verification` 验证一个 DOI，也可以让 `Paper Learning Assistant（论文学习助手）` 自动走完整个流程。

---

## 设计原则

- **DOI 必须验证**：绝不凭记忆写 DOI，必须通过 Crossref API 验证
- **公式以图为准**：公式核对必须用 PDF 渲染图，不用 OCR 文本
- **编译用 xelatex**：中文文档必须用 xelatex，不用 pdflatex
- **WPS 打开 PDF**：编译后用 WPS 打开，不用系统默认阅读器
- **聊天用 Unicode**：对话中用 Unicode 数学符号，tex 文件中用 LaTeX 语法
- **PDF 转 Markdown 优先**：阶段2优先使用 `convert-documents-to-markdown`，失败时回退到 `pdf-extractor`

---

## 目录结构

![目录结构图](assets/directory-structure.png)

---

## 更新日志

### 2026-10-29
- **改名：统一为「论文学习助手」`paper-learning-assistant`**
  - 仓库 `paper-learning-assistant` → `paper-learning-assistant`（https://github.com/zyj-cool/paper-learning-assistant）
  - skill 目录 `paper-workflow` → `paper-learning-assistant`，显示名去掉个人前缀
  - `latex-academic-paper-explanation` → `latex-academic-paper-explanation`
  - 发布包 `paper-learning-assistant_skill.zip` → `paper_learning_assistant_skill.zip`
  - 文档中的平台表述改为中性的 Codex / Claude / WorkBuddy；仅 qmind-knowledge 因面向
    特定平台产品而保留其官方名称
- **`paper-learning-assistant` 新增阶段5「解析产物回写 Zotero」**
  - 新增 `scripts/zotero_attach.py`：把论文解析 PDF 注册为 Zotero 论文的正式子附件，
    含预演/备份/幂等/回读校验/失败回滚，默认只预演、写入需 `--confirm`
  - 修正常见误区：Zotero 附件以数据库记录为准，只把文件拷进 storage 文件夹不会显示
  - `references/workflow-guide.md` 补充阶段5 详细指南与常见坑对照表
- **补充说明：为什么必须先完全退出 Zotero**
  - 本 skill 采用直接写 `zotero.sqlite` 的方案，**执行前必须完全退出 Zotero**（含托盘图标）
  - 三个原因：内存缓存覆盖改动、SQLite 锁冲突、全文索引与同步状态不一致（最坏触发云端覆盖）
  - 给出两条"不用关闭"的替代路径：Zotero 界面手动导入；Zotero 10+ 本地 API
    （`localhost:23119`，10.0 起支持写入，7–9 仅只读，需先在设置中开启并授权）
- **`zotero_attach.py` 新增 `--api` 本地 API 模式**：Zotero 运行中即可批量挂载，无需退出
  （Zotero 10+；含授权弹窗、密钥缓存、三阶段文件上传、401 自动重授权重试）；
  另新增 `--api-probe` 探测命令
- **阶段3 新增无 LaTeX 降级路线**：先检测 `xelatex`，缺失时自动降级为
  「HTML（内联CSS+Unicode公式）→ Chrome/Edge headless `--print-to-pdf`」或 python-docx 生成 Word，
  不再因环境没有 LaTeX 而中断
- **隐私清理**：移除各 skill 文档中残留的本机绝对路径（替换为 `C:\Users\<用户名>` 占位符），
  删除误提交的运行时调试报告，并用 git filter-repo 重写了全部历史；
  新增 `.gitignore` 规则阻止 `tool/reports/` 再次被提交

### 2026-10-24
- 新增 `Paper Learning Assistant（论文学习助手）`：论文全流程综合工具，四阶段工作流，适配 Codex/Claude/WorkBuddy
- 集成 `convert-documents-to-markdown`：PDF 转 Markdown 作为核心依赖
- 补全 `latex-academic-paper-explanation`：论文详解工具，六章深度解读
- 同步所有现有论文相关 skill 到仓库

---

## 版权与致谢

本 skill 集合的设计与实现借鉴、结合了以下来源：

- **网络公开 Skill**：参考了 开源社区、GitHub 上开源的 AI 编码助手 Skill 设计模式和工作流最佳实践
- **开源数据**：部分工作流逻辑和模板参考了 GitHub 上的开源论文处理工具、学术研究辅助项目和文档转换工具
- **API 服务**：集成了 Crossref、OpenAlex、Giiisp/集思谱、Firecrawl 等公开学术 API 和文档处理服务
- **社区贡献**：感谢各 AI 编码助手平台的开发者社区提供的 Skill 系统架构参考

本 skill 集合基于 **MIT 许可证** 开源。如引用内容涉及您的知识产权，请随时通过 [GitHub Issues](https://github.com/zyj-cool/paper-learning-assistant/issues) 或邮件联系，我们将及时修改或删除相关内容。

**作者**: zyj-cool  
**仓库**: https://github.com/zyj-cool/paper-learning-assistant  
**许可证**: MIT

---

## License

MIT
