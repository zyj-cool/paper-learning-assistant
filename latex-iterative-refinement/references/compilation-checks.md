# 编译错误与警告处理详细指南

## 错误搜索模式

```bash
# 致命错误
grep -n "^!" build.log
grep -n "Error:" build.log

# 溢出警告
grep -n "Overfull" build.log

# 欠满警告（低优先级）
grep -n "Underfull" build.log

# 未定义引用
grep -n "undefined" build.log
```

## Overfull \vbox 处理决策树

```
Overfull \vbox 出现在哪里？
│
├─ tcolorbox 附近
│  ├─ 检查导言区是否有 \tcbuselibrary{breakable}
│  │  └─ 没有 → 添加
│  ├─ 检查 \newtcolorbox 定义是否有 breakable 选项
│  │  └─ 没有 → 添加 breakable
│  └─ 已有 breakable 但仍溢出 → 检查是否用了 \newtcolorbox 而非 \newtcolorbox[...]{...}[...]
│
├─ 大公式/大表格
│  ├─ 单行公式过宽 → \resizebox{\textwidth}{!}{$...$}
│  ├─ 多行公式过宽 → 用 aligned/split 手动断行
│  └─ 表格过宽 → \resizebox{\textwidth}{!}{\begin{tabular}...\end{tabular}}
│
└─ 普通段落
   └─ 通常是长单词/长URL无法断行 → 用 \sloppy 或 \hspace{0pt} 插入断点
```

## Overfull \hbox 处理

```
Overfull \hbox (Xpt too high)
│
├─ X < 5pt → 可忽略，视觉上不明显
├─ X >= 5pt
│  ├─ 在公式环境中 → 检查公式是否过长
│  │  └─ 用 \resizebox 或 \begin{split}...\end{split}
│  ├─ 在表格中 → 表格列宽不够
│  │  └─ 用 \resizebox 或调整列格式 p{Xcm}
│  └─ 在普通文本中 → 长单词/URL
│     └─ 手动插入 \- 或 \hspace{0pt}
```

## tcolorbox breakable 常见陷阱

1. **忘记加载库**：只写了 `breakable` 选项但没加 `\tcbuselibrary{breakable}`
   → 报错 `Package pgfkeys Error: I do not know the key '/tcb/breakable'`

2. **breakable 位置错误**：
```latex
% 错误：breakable 在 \newtcolorbox 的选项之外
\newtcolorbox{mybox}[1][]{colback=blue, title=#1} breakable

% 正确：breakable 在选项内
\newtcolorbox{mybox}[1][]{colback=blue, title=#1, breakable}
```

3. **嵌套 box 不可 breakable**：外层 breakable 但内层也是 breakable 时，断开位置可能不理想
   → 内层 box 不加 breakable，让外层统一管理断开

## pdftoppm 参数说明

```bash
pdftoppm -png -r 150 -f <起始页> -l <结束页> "输入.pdf" "输出前缀"
```

- `-png`：输出 PNG 格式（Read 工具可查看）
- `-r 150`：分辨率 150 DPI（够用且文件不太大）
- `-f N`：起始页
- `-l N`：结束页
- 输出文件名：`输出前缀-页码.png`（如 `chk/p-01.png`）

**常用场景：**
- 检查单页：`-f 5 -l 5` → 输出 `chk/p-05.png`
- 检查跨页断开：`-f 4 -l 6` → 输出 3 张图，看断开位置
- 全文检查：`-f 1 -l <总页数>` → 输出所有页

## WPS wpspdf.exe 路径查找

WPS Office 安装路径不固定（版本号变化），用 find 动态查找：

```bash
find "/c/Users/<用户名>/AppData/Local/Kingsoft/WPS Office" -name "wpspdf.exe" 2>/dev/null | head -1
```

典型路径：
```
/c/Users/<用户名>/AppData/Local/Kingsoft/WPS Office/<版本号>/office6/wpspdf.exe
```

后台打开（不阻塞终端）：
```bash
"<wpspdf.exe路径>" "<PDF绝对路径>" &
```
