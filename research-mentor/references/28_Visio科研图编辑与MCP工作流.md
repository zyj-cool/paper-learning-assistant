# Visio 科研图编辑与 MCP 工作流

本文件用于 `.vsdx`、Microsoft Visio、工程系统图、控制框图、拓扑图、流程图、网络图和论文式 Visio 图升级。目标是把 Visio 从“办公软件画图”提升为可进入论文图件工程包的可编辑矢量源。

## 能力分层

处理 Visio 任务时先判断属于哪一档：

1. **Visio 风格重绘**：用户给截图、PPT、论文图或草图，要求升级为工程论文图。优先用 SVG/PDF/PPT shapes/Illustrator 生成可编辑矢量，不要求保留 `.vsdx`。
2. **`.vsdx` 文件级编辑**：用户给 `.vsdx`，要求改文字、统一颜色、线宽、字体、简单 shape 或检查图结构。可先把 `.vsdx` 当作 OpenXML 压缩包检查 `visio/pages/page*.xml`，必要时输出新的 `.vsdx`，不覆盖原文件。
3. **Visio 原生自动化**：用户要求打开 Visio、批量导出、生成 Visio 源文件或保持 Visio 原生可编辑。若本机已安装 Microsoft Visio，使用项目内 Visio MCP/COM 桥。

不要把三档混说。若只是能生成 Visio 风格图，不等于已经无损编辑复杂 `.vsdx` 模板。

## 默认工具链

项目级 Visio MCP 位于：

```powershell
G:\演示\mechanism-figure\mcp\visio_mcp_server.py
G:\演示\mechanism-figure\mcp\call_visio_mcp.py
```

常用命令：

```powershell
python -X utf8 G:\演示\mechanism-figure\mcp\call_visio_mcp.py status
python -X utf8 G:\演示\mechanism-figure\mcp\call_visio_mcp.py inspect input_path="input.vsdx"
python -X utf8 G:\演示\mechanism-figure\mcp\call_visio_mcp.py replace-text input_path="input.vsdx" output_path="edited.vsdx" replacements="{\"old\":\"new\"}" scope=pages
python -X utf8 G:\演示\mechanism-figure\mcp\call_visio_mcp.py export input_path="edited.vsdx" export_dir="exports" formats=pdf,svg,png
python -X utf8 G:\演示\mechanism-figure\mcp\call_visio_mcp.py create-demo output_path="engineering_visio_template.vsdx"
```

MCP 工具语义：

- `visio_status`：检测 Visio COM 是否可用，返回版本和文档数。
- `visio_inspect_vsdx`：不打开 Visio，读取 `.vsdx` 包结构、页面、shape 数、文字样本。
- `visio_replace_text_vsdx`：文件级 XML 文本替换，输出新 `.vsdx`，不覆盖源文件。
- `visio_export_vsdx`：通过 Visio 原生 COM 打开 `.vsdx` 并导出 PDF、逐页 SVG/PNG/EMF。
- `visio_create_engineering_demo`：生成一个 synthetic/demo 的 Visio 原生工程模型模板，用于验证桥接和复用样式。

## `.vsdx` 文件级编辑边界

可直接做：

- 文本替换、术语统一、英文标签统一；
- 页面数量、shape 数、文字样本、media/embedding 数检查；
- 简单颜色、线宽和 XML 属性级调整；
- 输出新文件并保留原始 `.vsdx`。

需谨慎或转 Visio COM：

- 复杂连接器 reroute；
- stencil/master 继承样式；
- data graphics、图层锁定、容器和泳道；
- 文本被拆成多个 run 的替换；
- 包含外链、嵌入 Excel、CAD 或高分辨率位图的图。

原则：先 inspect，再修改；修改后再 inspect/export 验证。不要直接覆盖用户原始文件。

## 期刊级 Visio 图审美

Visio 图进入论文前，默认按 T1 工科图标准处理：

- 白底、低饱和、细线、黑白打印可读；
- 主流程单向，反馈线弱化，避免多条箭头交叉；
- 模块大小按层级统一，变量标注贴近箭头；
- 外层分区只做浅色背景，不把长文字居中压住内部模块；
- 文本短、术语准，长解释放图注；
- 输出 SVG/PDF 作为主交付，PNG 只做预览。

## 交付与 QA

Visio 交付至少说明：

- 源文件：原始 `.vsdx` 是否保留，编辑后 `.vsdx` 路径；
- 导出：PDF、SVG、PNG/EMF 路径；
- 处理方式：文件级 XML 修改、Visio COM 原生导出，或重绘式复现；
- 风险：复杂模板、连接器、嵌入对象或 split text run 是否需要人工打开 Visio 复核。

没有真实数据或真实工程对象时，Visio demo 图必须标为 `synthetic/demo/illustrative`，不能写成实测系统图。
