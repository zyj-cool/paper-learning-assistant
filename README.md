# 论文学习助手 · Skills 集合

> 一套面向科研工作者的 AI 技能体系，覆盖论文从检索、阅读、总结、写作到排版投稿的全流程。

[![Skills](https://img.shields.io/badge/skills-13-blue)](#)
[![License](https://img.shields.io/badge/license-MIT-green)](#)

---

## 这是什么？

这是为 [Claude Code](https://claude.ai) 打造的一套 **论文科研技能包**。每个 skill 是一个独立的能力模块，加载后就能在对应场景下自动触发，把通用 AI 变成你的专属科研助手。

**适合谁用：** 研究生、博士生、科研工作者——尤其是控制理论、电子信息、自动化、计算机方向，但大部分技能对所有理工科通用。

---

## 技能全景图

```
                    ┌─────────────────────────────────────────┐
                    │           paper-workflow (总调度)         │
                    │   检索 → 总结 → LaTeX → Zotero 一站式    │
                    ──────┬──────────┬──────────┬────────────┘
                           │          │          │
              ┌────────────┘          │          └────────────┐
              ▼                       ▼                       ▼
     ┌────────────────┐    ┌──────────────────┐    ──────────────────┐
     │   文献检索层    │    │   论文理解层      │    │   输出与排版层    │
     ├────────────────┤    ├──────────────────┤    ├──────────────────
     │ giiisp 论文检索 │    │ literature-summary│    │ latex-iterative  │
     │ deep-research  │    │ pdf-extractor    │    │ -refinement      │
     │ scispark       │    │ paper-formula-*  │    │ latex-cjk-pdf    │
     │ DOI 验证       │    │ paper-workflow   │    │ -verify-loop     │
     │                │    │ paper-explanation│    │ convert-documents│
     └────────────────┘    └──────────────────┘    └──────────────────┘
              │                       │                       │
              └───────────────────────┼───────────────────────┘
                                      ▼
                          ┌───────────────────────┐
                          │  research-mentor (导师) │
                          │  写作·审稿·投稿·绘图    │
                          └───────────────────────┘
```

---

## 技能清单

### 核心工作流

| Skill | 一句话说明 | 触发词 |
|---|---|---|
| **paper-workflow** | 论文全流程综合工具。检索→四维度总结→LaTeX PDF→Zotero标注，一站式完成 | "总结论文""帮我读论文""论文工作流" |
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
| **convert-documents-to-markdown** | 文档格式转换。Word/PPT/Excel/PDF → Markdown | "转换文档""读取PDF" |

---

## 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/zyj-cool/paper-learning-assistant.git

# 复制到 用户级 skill 目录
cp -r paper-learning-assistant/* ~/.claude/skills/

# 或在对应平台中执行
/skills reload
```

### 典型使用场景

**场景 1：拿到一篇 PDF，快速总结**
```
你: 帮我总结这篇论文 [附PDF]
AI: [自动触发 paper-workflow]
  → 提取PDF + 验证DOI
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

---

## 技能间的协作关系

这套技能不是孤立存在的，它们通过 `paper-workflow` 统一调度，形成完整闭环：

```
检索论文 ──→ 验证DOI ──→ 提取PDF ──→ 四维度总结 ──→ LaTeX排版 ──→ Zotero归档
   │            │            │            │              │             │
   │            │            │            │              │             │
giiisp      crossref     pdf-extractor  paper-workflow  latex-iter-   literature-
            -doi-verif.                 + formula-check -refinement   summary
```

每个环节都可以**单独使用**，也可以**串联执行**。比如你可以只用 `crossref-doi-verification` 验证一个 DOI，也可以让 `paper-workflow` 自动走完整个流程。

---

## 设计原则

- **DOI 必须验证**：绝不凭记忆写 DOI，必须通过 Crossref API 验证
- **公式以图为准**：公式核对必须用 PDF 渲染图，不用 OCR 文本
- **编译用 xelatex**：中文文档必须用 xelatex，不用 pdflatex
- **WPS 打开 PDF**：编译后用 WPS 打开，不用系统默认阅读器
- **聊天用 Unicode**：对话中用 Unicode 数学符号，tex 文件中用 LaTeX 语法

---

## 目录结构

```
paper-learning-assistant/
├── paper-workflow/              # 论文全流程综合工具（总调度）
│   ├── SKILL.md
│   └── references/
│       ├── workflow-guide.md    # 详细操作指南
│       └── summary-template.md  # 四维度总结模板
── latex-academic-paper-explanation/  # 论文详解工具
│   ── SKILL.md
├── crossref-doi-verification/   # DOI 验证
├── literature-summary/          # Zotero 文献总结
├── latex-iterative-refinement/  # LaTeX 迭代编译
├── latex-cjk-pdf-verify-loop/   # LaTeX 快速编译
├── latex-iterative-edit-verify/ # LaTeX 交互编辑
├── paper-formula-fidelity-check/    # 公式核对
├── paper-formula-image-verification/ # 公式图像验证
├── pdf-extractor/               # PDF 提取
├── convert-documents-to-markdown/   # 文档转换
├── research-mentor/             # 科研导师（综合入口）
└── qmind-knowledge/             # QMind 知识库
```

---

## 更新日志

### 2026-10-24
- 新增 `paper-workflow`：论文全流程综合工具，四阶段工作流
- 补全 `latex-academic-paper-explanation`：论文详解工具，六章深度解读
- 同步所有现有论文相关 skill 到仓库

---

## License

MIT
