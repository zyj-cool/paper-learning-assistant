# 论文工作流详细指南

## 各阶段详细操作说明

### 阶段1: 检索与定位

#### 1.1 关键词检索流程

```
用户输入关键词/方向
  → 调用 giiisp-paper-search-apis
  → 解析返回的JSONL结果
  → 按相关性排序，取Top-K
  → 对每篇候选论文调用 crossref-doi-verification 验证DOI
  → 输出论文信息卡片列表
```

#### 1.2 PDF反查DOI流程

```
用户提供PDF文件
  → pdf-extractor 提取前2页文本（标题、作者、摘要区域）
  → 用标题调用 crossref-doi-verification 的 search 接口
  → 从搜索结果中选择最匹配的记录
  → 验证DOI返回OK后记录
```

#### 1.3 论文信息卡片格式

```markdown
## 论文信息卡片

- **标题**: [英文原标题]
- **作者**: [第一作者 et al.]
- **期刊/会议**: [全称]
- **年份**: [YYYY]
- **DOI**: [已验证DOI，附链接 https://doi.org/XXXX]
- **arXiv**: [如有预印本编号]
- **引用数**: [Google Scholar / Semantic Scholar]
- **Zotero状态**: [已在库/未在库]
```

---

### 阶段2: 四维度总结

#### 2.1 阅读顺序建议

按以下顺序阅读论文，效率最高：

1. **标题 + 摘要** → 了解研究问题和主要贡献
2. **引言最后一段** → 了解论文的具体贡献列表
3. **结论** → 了解主要发现和局限
4. **方法核心公式** → 理解技术路线
5. **实验设置 + 主要结果图** → 了解验证方式
6. **相关工作** → 了解领域脉络（可选，时间充裕时读）

#### 2.2 公式推导规范

- 每个公式标注原始编号（如 "Eq. (3)"）
- 推导步骤用编号列表，每步说明数学操作和物理含义
- 符号表统一放在公式小节末尾
- 复杂推导用多行align环境展示

#### 2.3 思路脉络图格式

用文本箭头图表示，复杂时可生成TikZ代码：

```
[研究缺口] → [提出假设] → [设计方法] → [理论证明] → [实验验证]
     |              |             |             |            |
  现有方法A      方法A的缺陷    核心创新点    收敛性定理    对比SOTA
  的局限性       方法B的不足    技术路线      稳定性分析    消融实验
```

#### 2.4 图表解读规范

- 优先解读：主方法示意图、主要结果对比图、消融实验图
- 次要解读：数据集统计图、超参数敏感性图
- 每张图标注：图号、位置（页码）、支撑的论点

---

### 阶段3: LaTeX生成

#### 3.1 文档结构

```
paper_summary/
── main.tex          # 主文档
├── sections/
│   ├── info.tex      # 论文信息
│   ├── summary.tex   # 中文摘要
│   ├── formulas.tex  # 公式推导
│   ├── flow.tex      # 思路脉络
│   ── figures.tex   # 图表解读
├── images/           # 提取的论文图表
├── build.log         # 编译日志
└── main.pdf          # 输出PDF
```

#### 3.2 编译检查清单

- [ ] xelatex编译无错误（搜索 `^!` 行）
- [ ] 无overfull hbox警告（或已处理）
- [ ] tcolorbox使用breakable时已加载库
- [ ] pgfkeys逗号参数已用花括号包裹
- [ ] pdftoppm渲染关键页PNG
- [ ] Read工具视觉验证渲染结果
- [ ] WPS打开PDF确认

#### 3.3 常见编译错误速查

| 错误信息 | 原因 | 修复 |
|---|---|---|
| `I do not know the key '/tcb/breakable'` | 缺少tcolorbox库 | 加 `\tcbuselibrary{breakable}` |
| `Environment xxx undefined` | 缺少宏包 | 添加对应 `\usepackage` |
| `Missing $ inserted` | 数学模式缺失 | 检查公式环境 |
| `Overfull \hbox` | 行溢出 | 用 `\sloppy` 或手动断行 |
| `Package pgfkeys Error` with comma | 逗号参数解析 | 用 `{a, b}` 包裹 |

---

### 阶段4: Zotero标注

#### 4.1 Zotero数据库位置

默认路径: `C:\Users\<用户名>\Zotero\zotero.sqlite`
存储目录: `C:\Users\<用户名>\Zotero\storage\`

#### 4.2 查询方式

通过 `literature-summary` skill中的Python脚本查询zotero.sqlite：
- 按DOI匹配论文
- 读取标签（tags表）
- 读取分类集合（collections表）
- 读取用户笔记（notes表）

#### 4.3 标注输出格式

```
【Zotero信息】
- 标签: multi-robot, CBF, collision-avoidance
- 分类: 多机器人协同控制 / 安全控制
- 笔记: [用户在此论文上的笔记内容，如有]
- 附件: [PDF路径，如有]
```
