---
name: latex-academic-paper-explanation
description: "论文深度详解工具：将单篇论文拆解为六章结构化中文文档（概览→背景→方法详解→理论分析→实验详解→总结思考），逐步推导核心公式并解释物理含义，用直觉语言讲清定理证明策略，逐图表解读实验设计与消融结果，最终编译为精美LaTeX PDF。适配Codex/Claude/WorkBuddy多平台。当用户说'论文详解''详细解读这篇论文''把论文内容整理成文档''深度分析方法部分'时触发。侧重精读与深度理解，与paper-learning-assistant的快速四维度总结互补。"
---

# 论文详解工具

> 将论文核心内容深度解读并生成LaTeX排版文档。

## 与 paper-workflow 的区别

- `paper-workflow`: 全流程调度（检索→总结→LaTeX→Zotero），适合快速概览
- `latex-academic-paper-explanation`: 专注深度解读，适合精读单篇论文

## 触发条件

- "论文详解" / "详细解读这篇论文"
- "把论文内容整理成文档"
- "深度分析这篇论文的方法部分"
- 用户已用 paper-workflow 做了快速总结，现在需要更深入的解读

## 工作流

```
输入PDF/DOI
  → 提取全文（pdf-extractor）
  → 逐章节深度解读
  → 生成详解LaTeX文档
  → 编译验证（latex-iterative-refinement）
  → WPS打开PDF
```

## 详解文档结构

```latex
\documentclass[12pt,a4paper]{ctexart}
\usepackage{amsmath,amssymb,amsthm}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{tcolorbox}
\usepackage{booktabs}
\usepackage{tikz}
\usetikzlibrary{arrows.meta, positioning, shapes}
\tcbuselibrary{breakable}

% 自定义环境
\newtcolorbox{insight}[1][]{
  breakable,
  colback=blue!5!white,
  colframe=blue!75!black,
  title=#1,
  fonttitle=\bfseries
}

\newtcolorbox{derivation}[1][]{
  breakable,
  colback=green!5!white,
  colframe=green!75!black,
  title=#1,
  fonttitle=\bfseries
}

\title{论文详解: [论文标题]}
\author{详解文档}
\date{\today}

\begin{document}
\maketitle
\tableofcontents

%% 第一章: 论文概览
\section{论文概览}
\subsection{基本信息}
% 标题、作者、期刊、年份、DOI、引用数

\subsection{研究动机}
% 作者为什么做这个研究？领域有什么缺口？

\subsection{核心贡献}
% 论文声称的3-4个贡献，逐条解读

%% 第二章: 背景与相关工作
\section{背景与相关工作}
\subsection{问题定义}
% 形式化的问题定义，符号说明

\subsection{已有方法}
% 论文回顾的相关工作，分类梳理

\subsection{已有方法的不足}
% 论文指出的现有方法缺陷

%% 第三章: 方法详解
\section{方法详解}
% 这是核心章节，每个子方法一个subsection

\subsection{[方法模块1]}
% 直觉解释 → 形式化描述 → 公式推导 → 算法伪代码

\subsection{[方法模块2]}
% 同上

%% 第四章: 理论分析
\section{理论分析}
% 定理、引理、证明思路（非逐字抄证明，而是讲清证明策略）

\subsection{关键定理}
\begin{insight}[定理 X: 定理名称]
[定理内容]
\end{insight}

\textbf{证明思路}: [用直觉语言说明证明的关键步骤]

\textbf{条件解读}: [定理的前提条件在实际中意味着什么]

%% 第五章: 实验详解
\section{实验详解}

\subsection{实验设置}
% 数据集、基线方法、评价指标、实现细节

\subsection{主要结果}
% 核心对比实验，关键数据

\subsection{消融实验}
% 各模块的贡献分析

\subsection{可视化结果}
% 定性分析，图表解读

%% 第六章: 总结与思考
\section{总结与思考}
\subsection{论文总结}
% 一句话总结 + 三个要点

\subsection{优点}
\subsection{不足}
\subsection{延伸方向}

\end{document}
```

## 各章节撰写规范

### 方法详解（最重要）

每个方法模块按以下顺序写：

1. **直觉解释**（1-2段）：用大白话说明这个模块在做什么，为什么需要它
2. **形式化描述**：给出数学定义和符号
3. **公式推导**：逐步展开，每步说明操作和含义
4. **算法伪代码**：如有算法，用algorithmic环境写出
5. **与其他模块的关系**：这个模块在整个方法中的位置

### 理论分析

- 不逐字抄证明，而是讲清**证明策略**
- 标注每个定理的**关键假设**
- 说明定理的**实际含义**（不是纯数学陈述）
- 如有多个定理，说明它们之间的**逻辑关系**

### 实验详解

- 先讲**实验设置**（数据集、基线、指标），再讲结果
- 对每个主要结果图/表，说明**它证明了什么**
- 消融实验要讲清**每个模块的贡献大小**
- 标注**实验的局限性**（如只在仿真中验证）

## 编译流程

使用 `latex-iterative-refinement` skill的闭环流程：

1. 生成 `.tex` 文件
2. `xelatex` 编译（两遍，处理交叉引用）
3. 检查编译日志，修复错误
4. `pdftoppm` 渲染关键页
5. 视觉验证
6. WPS打开PDF

## 注意事项

1. **深度优先**: 这是详解文档，不是快速总结。每个部分都要深入
2. **公式以图为准**: 用 `paper-formula-image-verification` 核对公式
3. **用自己的话**: 不照抄论文原文，用中文重新表述
4. **标注页码**: 重要内容标注原文页码，方便回查
5. **聊天用Unicode**: 对话中用Unicode数学符号，tex文件中用LaTeX语法
