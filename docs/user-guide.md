# Highlights to Obsidian — User Guide / 使用指南

A calibre plugin that formats the highlights and notes you make in calibre and sends them to your
Obsidian vault.

一个 calibre 插件:把你在 calibre 里做的高亮和批注格式化后,发送到你的 Obsidian 仓库(vault)。

> For the complete list of every formatting placeholder, see the **Formatting Options** section of
> [README.md](../README.md). This guide focuses on how to use the plugin day to day.
>
> 全部格式化占位符的完整清单见 [README.md](../README.md) 的 **Formatting Options** 一节。本指南侧重日常使用。

---

## 1. Install / 安装

1. In calibre: **Preferences → Plugins → Load plugin from file**, and choose the plugin zip
   (`zip/highlights-to-obsidian-<version>.zip`). Restart calibre.
2. Add the toolbar button: **Preferences → Toolbars & menus → The main toolbar**, add **H2O**.

1. calibre 里:**Preferences → Plugins → Load plugin from file**,选择插件 zip
   (`zip/highlights-to-obsidian-<版本>.zip`),然后重启 calibre。
2. 把按钮加到工具栏:**Preferences → Toolbars & menus → The main toolbar**,加入 **H2O**。

> Install the flat plugin zip, **not** a source-code archive of the whole repository.
>
> 安装的是扁平的插件 zip,**不是**整个仓库的源码包。

---

## 2. The toolbar button / 工具栏按钮

**Clicking the H2O button sends your new highlights** (all books). The dropdown arrow next to it
opens the full menu:

**点击 H2O 按钮 = 发送你的新增高亮**(全部书)。按钮旁的下拉箭头打开完整菜单:

| Menu item / 菜单项 | What it does / 作用 |
| --- | --- |
| **Send New Highlights** | New highlights from all books. / 全部书里的新增高亮。 |
| **Send New Highlights of Selected Books** | New highlights, only the books selected in the library. Does **not** advance the last-send time, so other books' new highlights are still picked up later. / 仅当前选中书的新增高亮;**不会**推进"上次发送时间",其它书的新增之后照常能发。 |
| **Send All Highlights** | Every highlight (asks for confirmation). / 全部高亮(会弹确认框)。 |
| **Send All Highlights of Selected Books** | Every highlight of the selected books. / 选中书的全部高亮。 |
| **Resend Highlights** | Re-sends the most recent "Send New" batch (see §8). / 重发最近一次"发送新增"的批次(见 §8)。 |
| **Config / Help** | Open settings / help. / 打开设置 / 帮助。 |

### What counts as "new"? / 什么算"新增"?

A highlight is **new** if it was made after the last-send time **and** its uuid hasn't been sent
before (or it was edited since being sent). This uuid check makes repeated sends idempotent — sending
twice won't duplicate, and a "selected books" send won't hide other books' new highlights.

一条高亮算**新增**,需同时满足:① 时间晚于"上次发送时间";② 它的 uuid 没发过(或发过之后又被编辑过)。这个 uuid 校验让重复发送是幂等的——发两次不会重复,"选中书"发送也不会把其它书的新增藏掉。

---

## 3. How highlights reach Obsidian / 高亮如何到达 Obsidian

There are two output methods, set in **Config → Other Options**:

在 **Config → Other Options** 里有两种输出方式:

- **obsidian:// URI** (default / 默认): sends notes through Obsidian's URL scheme. Obsidian must be
  open. Because URLs have a length limit, very long notes are split across several notes with
  `(1)`, `(2)`, ... appended to the title. / 通过 Obsidian 的 URL 协议发送,需 Obsidian 处于打开状态。因 URL 有长度上限,过长的笔记会被拆成多条,标题后加 `(1)`、`(2)`…。
- **Write directly to vault files** (recommended / 推荐): tick *"Write highlights directly to vault
  files"* and set **Vault folder path** to your vault's folder. This is more reliable — no length
  limit, doesn't need Obsidian open, and can't silently drop notes. / 勾选 *"Write highlights directly
  to vault files"* 并把 **Vault folder path** 设为你仓库的文件夹路径。更可靠——无长度限制、无需打开
  Obsidian、不会悄悄丢笔记。

> **Vault folder path** (a filesystem path) is a different field from **Obsidian vault name** (the
> name shown in Obsidian, used only by the URI method).
>
> **Vault folder path**(文件系统路径)与 **Obsidian vault name**(Obsidian 里显示的仓库名,仅 URI 方式用)是两个不同的字段。

### Merge mode / 合并模式

When writing to files, you can also enable **"Keep notes sorted and preserve your edits"**. New
highlights are inserted into the note in sorted position instead of appended, edited highlights are
updated in place, and your own manual edits in the note are preserved. It adds small hidden
`%%h2o%%` markers to track each highlight's position.

直写文件时,还可启用 **"Keep notes sorted and preserve your edits"**:新增高亮按顺序**插入**(而非追加),被编辑过的高亮**就地更新**,你在笔记里的手动修改也会保留。它会加一点隐藏的 `%%h2o%%` 标记来记录每条高亮的位置。

---

## 4. Formatting / 格式化

In **Config → Formatting Options** you set templates for the note **title**, **body**, an optional
separate **body for highlights without notes**, and a once-per-note **header**. Put a placeholder in
curly brackets, e.g. `{title}` or `{blockquote}`.

在 **Config → Formatting Options** 里设置笔记的 **title**(标题)、**body**(正文)、可选的
**无批注时的正文**,以及每条笔记只出现一次的 **header**(头部)。占位符用花括号,如 `{title}`、
`{blockquote}`。

Commonly used placeholders / 常用占位符:

| Placeholder | English | 中文 |
| --- | --- | --- |
| `{title}` `{authors}` | book title / authors | 书名 / 作者 |
| `{highlight}` | the highlighted text | 高亮的原文 |
| `{blockquote}` | the highlight as a `>` blockquote | 原文转成 `>` 引用块 |
| `{notes}` | your note on the highlight | 你对该高亮的批注 |
| `{url}` | a `calibre://` link back to the highlight | 跳回 calibre 原文的链接 |
| `{chaptertitle}` | the chapter/section the highlight is in | 高亮所在章节(最细一级) |
| `{topchapter}` | the first-level (broadest) chapter | 高亮所在的第一级(最顶层)章节 |
| `{color}` `{colorlabel}` | highlight color / its custom label | 高亮颜色 / 你给它配的标签 |
| `{date}` `{time}` `{datetime}` | when the highlight was made (UTC) | 高亮时间(UTC) |
| `{blockid}` | uuid sanitized for an Obsidian `^block` id | 适合做 Obsidian `^块id` 的 uuid |
| `{user}` `{usertype}` | which reader made it / `local` or `web` | 谁做的高亮 / `local` 或 `web` |

> Times use UTC by default; prefix with `local` for local time, e.g. `{localdatetime}`.
> 时间默认 UTC;加 `local` 前缀用本地时间,如 `{localdatetime}`。

### Conditional block / 条件块: `{if_notes}...{end_if_notes}`

Wrap part of the body so it only appears for highlights that **have** a note. Example body:

把正文的一部分包起来,使其**仅在该高亮有批注时**出现。示例正文:

```
> {blockquote}
{if_notes}

### My notes
{notes}
{end_if_notes}

---
```

This is an alternative to filling in the separate "body for highlights without notes" template.

这是除"无批注时的正文"模板之外的另一种做法。

### Frontmatter-safe values / frontmatter 安全值: `:yaml`

For a value used inside YAML frontmatter (e.g. a title containing `:`), add `:yaml`, as in
`{title:yaml}`, so it is properly quoted.

用于 YAML frontmatter 里的值(如含 `:` 的标题),加 `:yaml`,如 `{title:yaml}`,自动加引号转义。

### Frontmatter / 前置元数据

To add YAML frontmatter, put it in the **header** (it's written once, at the top of each note).
Frontmatter must be the very first thing in the file, so the header must **start with `---` with no
blank line before it**. Use `:yaml` for values that may contain special characters:

要给笔记加 YAML frontmatter,把它写进 **header**(每篇笔记开头只写一次)。frontmatter 必须在文件
最开头,所以 header 要**以 `---` 开头、前面不能有空行**。含特殊字符的值用 `:yaml`:

```
---
title: {title:yaml}
author: {authors:yaml}
isbn: {isbn}
published: {pubdate}
tags: [book, highlights]
---
```

On later sends the header isn't repeated, so frontmatter isn't duplicated; in merge mode your existing
frontmatter is left untouched. H2O only writes frontmatter when a note is first created — it doesn't
edit fields in an already-existing note's frontmatter.

之后再发送时 header 不会重复,所以 frontmatter 不会重复;合并模式下你已有的 frontmatter 原样保留。
H2O 只在笔记**首次创建**时写 frontmatter,不会去修改已存在笔记里 frontmatter 的字段。

### Note template file / 笔记模板文件

Instead of typing the header in the config, you can keep it in a **template file** in your vault. Set
**Config → Formatting Options → Note template file** to a vault-relative path, e.g.
`Reference/Templates/Book`. Its content becomes each new note's header/scaffold, with the same
`{placeholders}` filled in — a natural home for the frontmatter above. It needs the **Vault folder
path** (Other Options) set so the file can be found, is applied once when a note is created, and uses
H2O's `{placeholder}` syntax (not Obsidian/Templater's `{{...}}` or `<% %>` — H2O can't run Obsidian's
own template plugins).

除了在配置里输入 header,你也可以把它放进 vault 里的**模板文件**。在 **Config → Formatting Options →
Note template file** 填一个相对 vault 的路径,如 `Reference/Templates/Book`。文件内容会作为每篇新
笔记的 header/骨架,里面同样的 `{占位符}` 会被填充——正好用来放上面的 frontmatter。它需要设置
**Vault folder path**(Other Options)才能找到文件;只在笔记创建时套用一次;用的是 H2O 的 `{占位符}`
语法(不是 Obsidian/Templater 的 `{{...}}` 或 `<% %>`——H2O 无法运行 Obsidian 自己的模板插件)。

### Group by chapter / 按章节分组 + 目录

Tick **Config → Formatting Options → "Group highlights by first-level chapter, with a clickable table
of contents"** to turn each book into one note where the highlights are grouped under `## chapter`
headings (the book's first-level table-of-contents sections). A list of `[[#chapter]]` links is added
at the top, and clicking one jumps to that chapter further down the note. Set the **Table-of-contents
heading** to the label above those links, e.g. `## Contents` or `## 目录` (empty = no link list). The
in-note links only work when the whole book is one file, so use this with **Write highlights directly
to vault files** (the max note size is then ignored and the note isn't split), and sort by `location`
so chapters stay in reading order. It isn't combined with merge mode (grouping wins if both are on),
and re-sending appends a fresh table of contents — so it's best when you send a book's highlights
together. The resulting note looks like:

勾选 **Config → Formatting Options → "Group highlights by first-level chapter, with a clickable table
of contents"**,整本书会变成一篇笔记:高亮按 `## 章节` 标题分组(章节取书目录的**第一级**),笔记
顶部生成一串 `[[#章节]]` 链接,点一下就跳到下面对应的章节。**Table-of-contents heading** 填目录上方
的标题,如 `## Contents` 或 `## 目录`(留空则不生成链接列表)。笔记内跳转只有在整本书是同一个文件时
才有效,所以请配合 **Write highlights directly to vault files** 使用(此时忽略最大笔记长度、不再切分),
并把排序键设为 `location` 让章节按阅读顺序排列。它不与合并模式叠加(两者都开时以分组为准);重复发送会
再追加一份目录,所以最好一次性发送一本书的高亮。生成的笔记大致是:

```markdown
## 目录
- [[#第一章 绪论]]
- [[#第二章 方法]]

## 第一章 绪论
> 第一条高亮原文
我的批注…

---

## 第二章 方法
> 另一条高亮
```

---

## 5. Multiple readers / 多个读书人

calibre stores annotations per user. **By default the plugin only sends your own highlights** (the
desktop reader, stored as user `viewer`). If several people read the same library through calibre's
content server with separate accounts, you can:

calibre 按用户存注释。**插件默认只发你本人的高亮**(桌面阅读器,存为用户 `viewer`)。如果多人通过
calibre 内容服务器、各自账号读同一个库,你可以:

- enable **"Send highlights from ALL users"** in Other Options to export everyone's highlights at
  once; / 在 Other Options 里勾选 **"Send highlights from ALL users"**,一次导出所有人的高亮;
- use `{user}` to label whose is whose, or even route them to separate folders with a title like
  `Books/{user}/{title}`. / 用 `{user}` 标明是谁的,甚至用 `Books/{user}/{title}` 这样的标题把不同人
  分流到各自文件夹。

> Note: this is a *view* convenience, not access control — anyone with the library files or this
> plugin can read every user's annotations.
>
> 注意:这是*视图*上的便利,不是权限控制——任何拿到库文件或用本插件的人都能读到所有用户的注释。

---

## 6. Colors / 颜色

- **Highlight color labels** (Formatting Options): map a color to text, one per line, e.g.
  `yellow = Important`. Then `{colorlabel}` prints the label (falling back to the color name). /
  把颜色映射为文字,一行一个,如 `yellow = Important`;`{colorlabel}` 就会输出标签(没配则用颜色名)。
- **Only send these highlight colors** (Other Options): a comma-separated list, e.g. `yellow, blue`.
  Leave empty to send all colors. / 逗号分隔,如 `yellow, blue`;留空则发送所有颜色。

---

## 7. Other useful settings / 其它实用设置

- **Sort key**: how highlights sent to the same note are ordered — any formatting option without
  brackets, e.g. `location` (in-book order) or `timestamp`. / 同一笔记内高亮的排序依据,填某个格式选项
  (不带括号),如 `location`(书内顺序)或 `timestamp`。
- **Last send time**: highlights made after this are "new". Set it to now to skip everything older.
  / 此时间之后的高亮算"新增";设为现在可跳过更早的全部。
- **Read annotations from a custom column**: instead of calibre's own annotations, send the contents
  of a custom column (e.g. one filled by the *Annotations* plugin), one note per book. / 不读 calibre
  自带注释,而读某个自定义列(如 *Annotations* 插件填充的列),每本书一条笔记。
- **Maximum note size**, **confirmation dialog for "send all"**, **wait time between notes**, and
  **open with the OS's command** (instead of a web browser) are also in Other Options. / 最大笔记
  大小、"发送全部"确认框、笔记之间的等待时间、用系统命令打开(而非浏览器)也都在 Other Options。

---

## 8. Resend & troubleshooting / 重发与排障

- **Resend Highlights** re-sends the most recent "Send New" batch. Use it if Obsidian wasn't open or
  missed some highlights. / **Resend Highlights** 重发最近一次"发送新增"的批次;若当时 Obsidian 没开或
  漏收了高亮,用它补发。
- If highlights open a **web browser** instead of Obsidian, or large notes aren't sent, try **"Open
  Obsidian with the OS's command"**, or switch to **writing directly to vault files**. / 如果高亮把
  **浏览器**打开了、或大笔记发不出去,试试 **"Open Obsidian with the OS's command"**,或改用**直写文件**。
- **Logs**: the plugin writes a rotating log to `<calibre config dir>/plugins/highlights_to_obsidian.log`,
  and to calibre's debug output (run `calibre-debug -g`). Failures include a full traceback there. /
  **日志**:插件会把滚动日志写到 `<calibre 配置目录>/plugins/highlights_to_obsidian.log`,以及 calibre
  的调试输出(运行 `calibre-debug -g`);出错时那里有完整堆栈。
- **Keyboard shortcuts**: set them in calibre's **Preferences → Shortcuts → H2O**. / 在 calibre 的
  **Preferences → Shortcuts → H2O** 里设置快捷键。
