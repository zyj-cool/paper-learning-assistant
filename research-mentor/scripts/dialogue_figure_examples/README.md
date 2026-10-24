# 对话绘图脚本总结

本目录沉淀自近期几个绘图、改图和科研图件复现对话，分为两类：

- Python 绘图脚本：适合真实数据图、统计图、柱状图、误差棒图和期刊级结构复现图。
- GPT 绘图提示脚本：适合图像编辑、风格迁移、流程图重绘、状态图重绘和视频模型宏观演示。

使用边界：没有用户原始数据时，只能使用 `synthetic/demo/illustrative` 数据；不能把结构复现、演示数据或模板风格迁移说成真实实验结果。

## 1. 数据柱状图脚本

### `make_bar_charts.py`

来源对话：把第一张数据画成第二张图，主要连接点数和主要网格数分开画，每组三个数据取均值。

用途：

- 生成两张 GraphPad 风格柱状图。
- `Main connection points` 和 `Main mesh count` 分开输出。
- 每组 3 个重复值，柱高为均值，误差棒为样本标准差 `SD`，即 `std(ddof=1)`。
- 输出 PNG、SVG 和 `summary_means_sd.csv`。

可复用点：

- 参考图配色迁移。
- Pos 组使用与 Gel-3 接近但可区分的暖红色。
- 所有英文和数字统一 Calibri。
- 误差棒 cap 横杠只表示显示样式，竖向长度才表示 SD。

### `make_cell_viability_chart.py`

来源对话：按模板绘制细胞活性柱状图。

用途：

- 绘制 `RAW264.7 Cell viability(%)` 或同类细胞活性柱状图。
- 5 组：`PBS, Gel-0, Gel-1, Gel-2, Gel-3`。
- 柱高为均值，误差棒为用户确认的误差值。
- 输出 PNG、SVG 和 CSV。

可复用点：

- y 轴英文标签与 Calibri 字体强制。
- SVG 中保留可编辑文字：`plt.rcParams["svg.fonttype"] = "none"`。
- 误差棒 cap 长度控制在柱宽以内。

### `make_hemolysis_rate_chart.py`

来源对话：按模板绘制溶血率柱状图，并多轮调整显著性括号。

用途：

- 绘制 `Hemolysis rate (%)` 柱状图。
- 5 组：`PBS, Gel-0, Gel-1, Gel-2, Gel-3`。
- y 轴范围 `0-120`，刻度 `0, 30, 60, 90, 120`。
- 显著性标注使用模板式大括号和 `***`。
- 输出 PNG、SVG 和 CSV。

可复用点：

- 显著性括号拆成顶部横线、竖线、底部横线三段，便于单独移动竖线。
- 括号左端可与 PBS 误差棒中心对齐。
- cap 可适度加长，但不能超过柱宽。

## 2. 顶刊结构复现图包

目录：`top_journal_figures/`

来源对话：根据提示词复现这些图，并把八张复现图加入科研导师 skill 介绍 PPT。

这个图包把单脚本复现重构成期刊级 Matplotlib 工程：

- `make_all_figures.py`：批量生成所有图。
- `style_config.py`：统一 180 mm 双栏尺寸、字体、线宽、配色。
- `data_generators.py`：生成确定性的 synthetic/demo 数据。
- `export_utils.py`：统一导出 SVG、PDF、600dpi PNG 和 preview。
- `validation.py`：写出基础质检报告。
- `figures/fig01_graphcast.py`
- `figures/fig02_alphago_zero.py`
- `figures/fig03_recovery.py`
- `figures/fig04_step5.py`
- `figures/fig05_alphafold.py`
- `figures/fig06_anthropogenic_mass.py`
- `figures/fig07_rationality.py`
- `figures/fig08_moral_machine.py`

八类图件沉淀：

- GraphCast：共享横轴、多面板曲线、RMSE/ACC、skill 热图和色条。
- AlphaGo Zero：训练曲线、网络/自博弈结构和对比趋势。
- RECOVERY：Kaplan-Meier 阶梯曲线与 number-at-risk 风险表。
- STEP：多面板过程曲线与模型/任务阶段表达。
- AlphaFold：结构预测类多面板表达。
- Anthropogenic mass：堆叠面积图、交叉点标注和外推区间。
- Rationality：多行机制对比、点线面板和图例治理。
- Moral Machine：树状聚类、雷达/点图区间、群体分组和共享图例。

运行示例：

```powershell
cd C:\Users\Lenovo\.codex\skills\research-mentor-skill\scripts\dialogue_figure_examples\top_journal_figures
python make_all_figures.py
```

注意：该图包复现的是视觉语法、面板结构和统计表达，不复制原论文真实数据点、原图位图或未授权素材。

## 3. GPT 绘图提示脚本沉淀

这些提示词不作为单独 `.py` 文件，而是作为绘图方法沉淀在本 README 中。使用时先让模型读懂原图，再下重绘要求。

### 风格迁移图

适用：把图 1 改成图 2 的颜色和画风，但不改逻辑。

提示骨架：

```text
请将图1重绘为图2的视觉风格，但保持图1的逻辑、数据关系、流程顺序、变量含义和所有文字含义不变。
只做颜色、线条、字体和排版质感转换。
参考风格：白色背景、蓝色主线、橙色关键强调、干净的科技论文插图风格、矢量感强。
必须保留原图中的曲线、阈值线、阶段划分、箭头关系、公式变量和关键标注，不要漏字、不要改字、不要重排逻辑。
```

### 生命科学 Graphical Abstract

适用：Nature / Cell / Science Translational Medicine 风格的机制示意图、Working Model、细胞-蛋白-通路-微环境图。

提示骨架：

```text
请基于我提供的机制链或原图提示词，重绘一张 Nature / Cell / Science Translational Medicine 风格的生命科学 Graphical Abstract。

要求：
1. 只保留一条主叙事链：Trigger -> Cellular response -> Molecular mechanism -> Functional outcome。
2. 画面只能有一个主方向，默认从左到右，不要改成多面板拼盘。
3. 只保留 3-4 种主要细胞、5-8 个关键蛋白、2-3 条主通路，图层必须可编辑。
4. 细胞要有不规则膜边界、双层膜、细胞核、必要的细胞器；蛋白不要画成普通圆点。
5. 颜色低饱和，白底，English labels only，SVG/PDF/AI 结构可编辑。
6. 不要使用 PPT 方框、SmartArt、粗箭头、低质量 icon、发光效果或大面积空白。
7. 如果是“修改现有图”，优先保留原图的方向、顺序和层级，只优化版式和细节，不重写故事。
```

### 黑白灰工程流程图

适用：工程类中文核心论文流程图，如 `CAPTURE.CFG` 配置装载、采样链路初始化、异常校验。

提示骨架：

```text
请将原图重绘为工程类中文核心论文风格的黑白灰技术流程图。
主流程清晰，异常流程用虚线箭头；模块边框规整，节点编号统一，文字短语化。
保留配置读取、字段解析、通道校验、ADC/TIM2/DMA约束、PRE/POST容量校验、有效配置写入和采样链路启动。
图要看起来比普通流程图更完整、更工程化，但不要堆叠过多小字。
```

### 椭圆状态转换图

适用：嵌入式系统状态机、采样与存储系统状态转换。

提示骨架：

```text
请参考椭圆形状态图风格，绘制“STM32多通道高速采样与存储系统状态转换图”。
节点控制在 10-12 个左右：系统上电、系统初始化、自检判断、等待指令、参数配置、采样准备、循环采样、数据缓存、数据存储、数据上传、低功耗、异常处理。
主流程放中央，参数配置和数据上传放两侧，低功耗和异常处理放下方或外围。
箭头尽量顺时针或沿单一主方向流动，返回箭头用弧线，避免交叉。
```

### 环形缓存机理图

适用：SDRAM ring buffer、ADC DMA、Bounce Buffer、SDIO DMA、SD NAND 等系统机理图。

提示骨架：

```text
请绘制“STM32F429 基于 32MiB SDRAM Ring Buffer 的 ADC DMA 连续采集与 SDIO DMA 异步落盘机制”。
中央放 SDRAM Ring Buffer 圆环，左侧放 ADC DMA Producer，右侧放 Bounce Buffer、SDIO DMA Consumer 和 SD NAND，底部放 32MiB ring 线性展开图，右下角放公式约束框。
实线箭头表示数据流，虚线箭头表示控制流/写完成确认。
必须区分 head 与 tail：head 由 ADC DMA 写入推进；tail 只能在 SDIO DMA 写完成确认后推进，不能在提交 DMA 时提前推进。
必须标注 Q(t)、B_free、B_high、B_guard 和安全条件 B_free >= B_next。
```

### 科幻宏观视频提示

适用：即梦/NIM 等视频模型，表现环形缓存调度和异步写入，不用于论文数据图。

提示骨架：

```text
8-second cinematic hard sci-fi engineering visualization, 16:9.
Deep black background, blue-silver palette, transparent glass, brushed metal, volumetric lighting, glowing data particles, precise HUD.
A large transparent 3D ring buffer floats in the center. Blue data light flows around the ring, gray transparent area shows free space, thin orange arc shows high-water warning.
Left input module sends blue waveform particles into the ring; right dual-buffer chambers alternate and write glowing data blocks to a crystalline storage core.
After each write, a green confirmation pulse returns to the ring, the release pointer advances, backlog shrinks, system stabilizes.
Minimal English labels only: INPUT, RING BUFFER, DUAL BUFFER, ASYNC WRITE, SAFE RELEASE, STABLE FLOW.
```

## 4. 复用检查清单

每次复用这些脚本或提示词前，至少检查：

- 数据来源是否真实，demo 数据是否明确标注。
- 均值、SD、SEM、误差棒 cap 是否区分清楚。
- 轴标签、单位、字体、图例是否符合目标论文/汇报要求。
- SVG/PDF/600dpi PNG 是否都能导出。
- 图例、色条、风险表、显著性括号和面板字母是否遮挡数据。
- 图片重绘是否只迁移风格，没有篡改原图逻辑。
