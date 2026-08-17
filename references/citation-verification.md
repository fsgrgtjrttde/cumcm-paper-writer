# 参考文献真实性核验

参考文献的目标是可复核，不是凑数量。检索工具只用于发现候选；只有原始出版页、DOI 注册记录、出版社页面、数据发布机构页面或官方页面核验过的条目才能进入论文。

## 硬性规则

1. 不从记忆、样本文献表、搜索摘要或二手博客补全作者、卷期、页码、年份和 DOI。
2. 不存在的 DOI、无法打开的出版页、与题名/年份不一致的元数据，均视为 `FAIL`，不改写成看似合理的条目。
3. 仅有搜索结果但不能确认原始来源时，保留为候选，不在正文 `\cite`、`\bibitem` 或 Word 参考文献中使用。
4. 中文图书、标准、数据集和官方网页没有 DOI 时，使用出版社、标准发布机构、数据发布机构或主办方的规范 URL，并记录人工核验依据。
5. 每篇进入论文的文献必须被正文实际引用；每个正文引用必须有一个通过核验的条目。

## 工作流

1. 用 `paper-search` 或 `math-modeling/tools/paper_search/SKILL.md` 的双引擎检索发现候选。
2. 打开 DOI 解析页或原始出版机构/官方页面，核对作者、完整题名、年份、载体、卷期页、DOI 或规范 URL。
3. 将核验字段写入 `PROJECT_ROOT/引用核验台账.tsv`，再从台账生成或校对 `references.bib`。不要手工补写不在台账中的 BibTeX 条目。
4. 运行在线核验器；只在 `RESULT=PASS` 后编辑正文引用和构建 PDF。
5. 完成 LaTeX 编译后运行 LaTeX 工具的 `validate`，确认 `\cite`、`.bib`/`\bibitem`、PDF 中的参考文献三者一致。

## 台账格式

文件必须为 UTF-8 TSV，首行严格包含以下字段；`isbn` 可为空：

```tsv
citation_key	title	authors	year	source_type	doi	canonical_url	isbn	verification_source	verified_at	status
```

- `citation_key`：与 `.bib` 的键完全相同，如 `box1976`。
- `source_type`：`doi`、`publisher`、`official_web`、`book`、`dataset` 或 `standard`。
- `doi`：DOI 条目必须填写，不加 `https://doi.org/` 也可。
- `canonical_url`：没有 DOI 的条目必须是出版方、发布机构或主办方规范页；不能填搜索页、转载页或短链。
- `verification_source`：本次实际打开并核验的 DOI、出版页或官方页。
- `verified_at`：核验日期，格式 `YYYY-MM-DD`。
- `status`：只能是 `verified`。候选、待查和人工摘录不得伪装为已核验。

示例仅展示字段结构；其中内容应由本轮实际核验值填写：

```tsv
citation_key	title	authors	year	source_type	doi	canonical_url	isbn	verification_source	verified_at	status
example_key	<已核验题名>	<已核验作者>	<年份>	doi	<已核验 DOI>	https://doi.org/<已核验 DOI>		<实际打开的 DOI 或出版页>	<YYYY-MM-DD>	verified
```

## 命令与结果

```powershell
python "<SKILL_ROOT>/scripts/verify_references.py" `
  --bib "<PROJECT_ROOT>/完整论文-LaTeX/references.bib" `
  --ledger "<PROJECT_ROOT>/引用核验台账.tsv" `
  --online `
  --report "<PROJECT_ROOT>/引用核验报告.json"
```

- `RESULT=PASS`：台账、BibTeX 元数据和在线 DOI/规范 URL 检查一致；DOI 条目还通过 Crossref 题名、年份和作者姓氏核对。
- `RESULT=FAIL`：字段缺失、BibTeX 与台账不一致、DOI 元数据冲突或 URL 无法确认；必须修正或删除条目。
- `RESULT=UNVERIFIED`：网络或来源不可用；不能提交，也不能用 `--allow-warning` 覆盖。

离线时可以运行 `--offline` 做台账和 `.bib` 一致性预检，但它不产生可提交的核验结论。恢复网络后必须重跑 `--online`。

## LaTeX 编辑约束

- 优先使用一个经核验的 `.bib` 文件和 `\addbibresource` 或 `\bibliography`；不要在多个 `.tex` 文件复制条目。
- 若官方模板强制 `thebibliography`/`\bibitem`，仍须以台账为准，并在最终回复中报告人工条目已逐条核验。
- 修改 `references.bib`、引用键、`.bst` 或后端后，重新执行本核验器、`latex_paper.py build` 和 `latex_paper.py validate`。
