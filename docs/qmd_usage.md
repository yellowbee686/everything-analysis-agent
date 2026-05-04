# QMD 使用说明

调查日期：2026-05-04

参考来源：

- `/Users/bytedance/code/qmd/README.md`
- `/Users/bytedance/code/qmd/skills/qmd/SKILL.md`
- `qmd --help`

## 当前已配置内容

- QMD CLI：已安装为全局命令 `qmd`
- QMD skill：已软链到 `/Users/bytedance/.agents/skills/qmd`
- skill 源目录：`/Users/bytedance/code/qmd/skills/qmd`
- 数据集目录：`/Users/bytedance/code/analysis-agent/data/analysis_md_files`
- collection 名称：`analysis_md_files`
- index 名称：`analysis-md`
- index 文件：`/Users/bytedance/.cache/qmd/analysis-md.sqlite`
- collection 配置：`/Users/bytedance/.config/qmd/analysis-md.yml`

建议把这个数据集放在独立 named index 中，而不是默认 `index`。原因是该目录文件量较大，独立 index 可以避免污染个人默认知识库，也便于单独更新、备份和清理。

当前文档/BM25 索引已完成，`qmd --index analysis-md search ...` 可直接使用。该数据集很大，`qmd embed` 单次 session 约 30 分钟后会退出；需要重复运行 `qmd --index analysis-md embed`，直到 `qmd --index analysis-md status` 不再显示 `Pending`，语义检索才算完整补齐。首次运行 `embed`、`vsearch` 或 `query` 时，QMD 可能会把模型下载到 `~/.cache/qmd/models`。

## QMD 是否有 setup/install 脚本

QMD 没有一个专门叫 `setup` 的数据集初始化命令。构建目录索引的标准流程是：

```bash
qmd --index analysis-md collection add /Users/bytedance/code/analysis-agent/data/analysis_md_files --name analysis_md_files --mask "**/*.md"
qmd --index analysis-md embed
```

后续同步目录变更用：

```bash
qmd --index analysis-md update
qmd --index analysis-md embed
```

其中：

- `collection add`：注册目录并建立文档/BM25 索引
- `update`：重新扫描 collection，增量更新索引
- `embed`：生成或补齐语义向量，用于 `vsearch` 和更高质量的 `query`
- `qmd skill install --global`：安装 QMD agent skill，不是数据集索引初始化命令

如果 `embed` 输出 `Session expired`，直接重新执行同一条 `qmd --index analysis-md embed` 即可续跑。

## macOS

安装 CLI：

```bash
npm install -g @tobilu/qmd
```

软链安装 skill：

```bash
mkdir -p ~/.agents/skills
ln -sfn /Users/bytedance/code/qmd/skills/qmd ~/.agents/skills/qmd
```

首次构建当前数据集：

```bash
qmd --index analysis-md collection add /Users/bytedance/code/analysis-agent/data/analysis_md_files --name analysis_md_files --mask "**/*.md"
qmd --index analysis-md embed
```

查看状态：

```bash
qmd --index analysis-md status
qmd --index analysis-md collection list
```

检索示例：

```bash
qmd --index analysis-md search "上古汉语" -c analysis_md_files
qmd --index analysis-md vsearch "讨论汉语方言声调演变的文章" -c analysis_md_files
qmd --index analysis-md query "清代文献中的语法研究" -c analysis_md_files -n 10
```

获取文档：

```bash
qmd --index analysis-md get "qmd://analysis_md_files/文件名.md" --full
qmd --index analysis-md multi-get "*.md" -l 80 --md
```

更新索引：

```bash
qmd --index analysis-md update
qmd --index analysis-md embed
```

## Windows

安装 CLI：

```powershell
npm install -g @tobilu/qmd
```

建议使用 Windows 用户目录作为 QMD 配置和缓存位置。路径示例：

```powershell
$DataDir = "D:\analysis-agent\data\analysis_md_files"
$IndexName = "analysis-md"
```

首次构建数据集：

```powershell
qmd --index $IndexName collection add $DataDir --name analysis_md_files --mask "**/*.md"
qmd --index $IndexName embed
```

查看状态：

```powershell
qmd --index $IndexName status
qmd --index $IndexName collection list
```

检索示例：

```powershell
qmd --index $IndexName search "上古汉语" -c analysis_md_files
qmd --index $IndexName vsearch "讨论汉语方言声调演变的文章" -c analysis_md_files
qmd --index $IndexName query "清代文献中的语法研究" -c analysis_md_files -n 10
```

更新索引：

```powershell
qmd --index $IndexName update
qmd --index $IndexName embed
```

Windows 上的 index 默认会放在用户缓存目录下的 `qmd` 子目录中；如果设置了 `XDG_CACHE_HOME`，则会放在 `$env:XDG_CACHE_HOME\qmd\analysis-md.sqlite`。
