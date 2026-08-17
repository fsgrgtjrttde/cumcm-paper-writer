---
name: cumcm-paper-writer
description: 为高教社杯全国大学生数学建模竞赛（CUMCM）撰写、改写、审校、DOCX/LaTeX 编辑、PDF 生成和排版中文建模论文，适配 2026 年论文格式规范、参赛规则和 AI 工具使用规定；按可追溯的获奖/展示论文结构与中文论证风格组织内容，并以真实来源核验全部参考文献。仅在用户明确提到 CUMCM、高教社杯数学建模国赛、该竞赛的赛题/论文/摘要/附录/支撑材料、往届展示论文风格、CUMCM 2026 格式、LaTeX 项目或论文 PDF 时使用；普通论文、摘要或正文请求不触发。
---

# CUMCM 论文写作

生成贴近中文科技论文语境、证据完整且符合当届官方规则的 CUMCM 论文。论文仅供参赛队研究和修改，不能替代参赛队的核心建模、人工核验与最终责任。

## 强制原则

1. 先核验当届官方规则，再写正文。官方文件高于本 Skill、往届论文和经验模板。
2. 只写有题目、模型、代码输出、图表或可核验文献支撑的内容。禁止编造数据、结果、实验、引用和官方要求。
3. 使用 AI 时遵守 2026 年试行规定：在参考文献前加入 AI 工具使用声明；在支撑材料中提供 `AI工具使用详情.pdf`；逐项人工审查和核实 AI 输出。
4. 只提炼获奖/展示论文的结构、论证顺序和语言功能，不复制样本原句、段落、图表、参考文献或独特表达，不承诺任何奖项结果。
5. 不在论文、附录和支撑材料中泄露参赛者身份、学校或赛区信息。
6. 每条参考文献必须有可追溯的原始出版页、官方页面或 DOI；写入正文或 `.bib` 前建立引用核验台账。无法在线或人工核验的条目只能列为待补材料，不能编入论文。

## 开始时报告

首次进度更新说明：

- 已激活本 Skill，给出 `SKILL_ROOT` 与 `PROJECT_ROOT`。
- 目标届次、题号、交付格式、官方规则来源及核验日期。
- 已取得和仍缺失的题目、附件、模型说明、代码、结果表、图、文献、引用核验台账与赛区补充要求。
- 当前阶段：规则核验、证据盘点、大纲、写作、排版或终检。

## 权威来源顺序

1. 用户提供的当届官方文件、摘要页、承诺书、编号页和赛区补充要求。
2. CUMCM 官网发布的当届格式规范、参赛规则和 AI 工具使用规定。
3. `references/official-2026.md` 中的已核验快照。
4. 现有 `math-modeling` Skill 的“论文手”、DOCX/LaTeX 工具和内置模板。
5. 往届优秀论文只能提供写作风格参考，不能覆盖官方规则。

规则可能更新。每次正式写作前打开官方页面复核；无法联网时明确标注快照日期并提示可能过时。

## 输入门禁

完整论文至少需要：赛题与全部附件；每个子问题的模型、变量、假设、目标函数、约束和求解算法；可运行代码及真实输出；结果表、图和单位；已核验的参考文献元数据；用户要求的 Word、PDF 或 LaTeX 交付格式。缺少核心结果时，先列出缺口并回退到建模或编程阶段，不得用示例数值填充正式结论。

## 渐进式加载

| 任务 | 读取 |
|---|---|
| 核对 2026 硬性格式与 AI 声明 | `references/official-2026.md` |
| 写摘要、正文或中文润色 | `references/chinese-style-guide.md` |
| 按获奖/展示论文风格写摘要、正文或改稿 | `references/award-style-profile.md`，再读取 `references/chinese-style-guide.md` |
| 查阅样本范围与来源 | `references/sample-corpus.md`；需要逐篇 URL 时读取 `references/sample-index.tsv` |
| 建立大纲和主张-证据关系 | `references/evidence-workflow.md` |
| 搜索、录入或核验参考文献 | `references/citation-verification.md`；使用当前环境的 `paper-search` 或 `math-modeling/tools/paper_search/SKILL.md`；运行 `scripts/verify_references.py` |
| 准备 AI 使用详情 | `references/ai-use-detail-template.md` |
| 生成 Word | 当前环境的 `docx` Skill 与 `math-modeling/tools/docx/SKILL.md` |
| 新建或编辑 LaTeX/PDF | `math-modeling/tools/latex/SKILL.md`；PDF 校验再读取 PDF Skill |
| 生成和校验论文 PDF | `references/pdf-generation.md`；运行 `scripts/generate_paper_pdf.py`，再读取 `math-modeling/tools/latex/SKILL.md` 和 PDF Skill |
| 交付前终检 | `references/review-checklist.md` |

## 2026 规则核验

2026 官方要求至少包括：A4、纸质版至少 2.5 cm 页边距、摘要原则上不超过一页、正文不超过 30 页、正文不设目录、电子论文不含承诺书和编号页、电子论文与支撑材料分别不超过 20 MB。其中“原则上”是摘要页数的限定语；正文页数和文件大小是明确上限。完整条款见 `references/official-2026.md`。

## 写作工作流

1. 记录竞赛全称、届次、官方 URL、核验日期和赛区补充要求，把官方硬约束与质量目标分开。
2. 按 `references/evidence-workflow.md` 为每个子问题建立主张—证据台账；摘要中的数值必须能回溯到正文和结果文件。
3. 读取 `references/award-style-profile.md`，按题型选择样本归纳出的章节功能、证据顺序与中文句法。形成“标题与摘要页—问题重述与分析—假设和符号—各子问题模型/求解/结果/验证—稳健性或误差—模型评价—AI 声明—参考文献—附录”的论证结构；正文不生成目录。
4. 摘要按“任务概括 -> 各子问题方法和关键结果 -> 验证/稳健性 -> 关键词”写。每个子问题优先保留输入/约束、核心方法、关键结果和验证。按题型选择证据：机理题给方程对象、参数与误差，优化题给目标/约束、方案值与对照，数据题给预处理、指标与验证，预测题给时间划分、误差与稳健性。不要只罗列算法名，也不要把样本句式机械替换名词。
5. 正文按“问题分析 -> 变量与假设 -> 数学定义 -> 求解方法 -> 运行参数 -> 真实结果 -> 验证 -> 小结”展开。使用“本文”“针对问题一”“结果表明”等客观连接；每段只承担一个可核验的论证功能，避免无证据的“效果很好”“意义重大”。
6. 每幅图和每个表有连续编号、准确题注和正文引用；公式、单位、有效数字和结果源一致；每个子问题至少有正式结果证据。
7. 对每条文献先运行双引擎或 OpenAlex 检索发现候选，再打开 DOI 或出版机构/官方页面核对作者、题名、年份、来源、卷期页、DOI/URL。把核验值写入 `引用核验台账.tsv`，再生成 `.bib` 或手工条目；不得把样本论文参考文献直接当作已核验文献。
8. 运行 `scripts/verify_references.py`。任何 `FAIL` 或 `UNVERIFIED` 都阻断写入参考文献和最终交付；不因凑数量而保留待核验、二手转录或搜索结果页条目。

## 样本学习边界

样本仅用于结构、术语和证据组织的迁移。标题可采用“对象 + 任务/目标 + 方法”，但方法不是必需；算法必须伴随变量、约束、输出指标和验证。读取 `references/award-style-profile.md` 后，先给出“题型—章节功能—证据—语言动作”映射，再写正文。禁止复制原句、段落、图表、参考文献或独特表达。当前样本中部分页面没有统一奖项级别，必须按 `sample-corpus.md` 的证据范围表述，不能将全部样本虚称为国奖论文。

## AI 详情与排版

默认生成 Word；用户要求 LaTeX 时支持新建和编辑既有 LaTeX 项目。先读取 `math-modeling/tools/latex/SKILL.md` 并运行 `latex_paper.py doctor`；新项目必须用 `latex_paper.py init` 复制官方或内置模板，既有项目先定位主 `.tex`、模板来源、引擎、参考文献后端与 `latex-project.json`。只编辑 `PROJECT_ROOT` 中的副本，保留 `.cls`、`.sty`、`.bst` 和资源；禁止为了改一节另写脱离模板的临时 `main.tex`。引用统一维护在经核验的 `.bib` 或可追溯的 `\bibitem` 条目中，改动后重新编译、消除未解析引用，并执行 `latex_paper.py validate`。

生成 PDF 时运行 `scripts/generate_paper_pdf.py`。该模块强制要求引用核验报告为 `PASS`，依次调用 `latex_paper.py doctor`、`build` 和 `validate`，并在 PDF 旁写出包含源码/PDF 哈希、引擎、题号和页数阈值的 `.pdf-generation.json`。任何编译错误、未解释警告、页数超限、资源哈希漂移或引用报告为 `UNVERIFIED` 都阻断交付；生成后仍须按 PDF Skill 提取文本、渲染页面并人工抽检。

优先使用用户提供或官网下载的当届模板，无模板时使用数学建模工具基线但不得称为官方模板。电子版第一页必须是摘要专用页，不含纸质版承诺书和编号页；附录列出支撑材料文件名和全部完整、可运行源程序。

使用 AI 时，按 `references/ai-use-detail-template.md` 先生成详情 DOCX，再导出为文件名严格等于 `AI工具使用详情.pdf` 的 PDF。调用 PDF Skill 提取文本并逐页渲染，核对字段完整、中文不乱码、表格不跨页丢失、无身份信息；未完成文本和版面双重核验不得放入支撑材料。

## 校验与交付

DOCX 示例：

```powershell
python "<SKILL_ROOT>/scripts/validate_cumcm_paper.py" "<PROJECT_ROOT>/完整论文.docx" --electronic --abstract-pages <实际摘要页数> --body-pages <实际正文页数> --expect-ai used --support "<PROJECT_ROOT>/支撑材料.zip" --support-pdf-verified --citation-report "<PROJECT_ROOT>/引用核验报告.json"
```

引用核验（写入 `.bib` 后、编译前）示例：

```powershell
python "<SKILL_ROOT>/scripts/verify_references.py" --bib "<PROJECT_ROOT>/完整论文-LaTeX/references.bib" --ledger "<PROJECT_ROOT>/引用核验台账.tsv" --online --report "<PROJECT_ROOT>/引用核验报告.json"
```

LaTeX 编辑与校验示例：

```powershell
python "<SKILL_ROOT>/tools/latex/scripts/latex_paper.py" doctor --engine xelatex --bibliography-backend biber
python "<SKILL_ROOT>/tools/latex/scripts/latex_paper.py" build "<PROJECT_ROOT>/完整论文-LaTeX/main.tex" --engine xelatex --publish "<PROJECT_ROOT>/完整论文.pdf"
python "<SKILL_ROOT>/tools/latex/scripts/latex_paper.py" validate "<PROJECT_ROOT>/完整论文-LaTeX/main.tex" --pdf "<PROJECT_ROOT>/完整论文.pdf" --contest cumcm --quality-checks --questions <q1 q2 ...> --min-image-dpi 300 --max-pages <当届官方正文上限> --body-start-page <正文起始页>
```

统一生成 PDF 示例：

```powershell
python "<SKILL_ROOT>/scripts/generate_paper_pdf.py" "<PROJECT_ROOT>/完整论文-LaTeX" --main "main.tex" --citation-report "<PROJECT_ROOT>/引用核验报告.json" --questions <q1 q2 ...> --body-start-page <正文起始页> --max-pages 30 --output "<PROJECT_ROOT>/完整论文.pdf"
```

若提交论文是 PDF，先用 PDF Skill 提取全文到 UTF-8 文本并完成逐页渲染核验，再运行：

```powershell
python "<SKILL_ROOT>/scripts/validate_cumcm_paper.py" "<PROJECT_ROOT>/完整论文.pdf" --pdf-text "<PROJECT_ROOT>/完整论文-pdf提取.txt" --pdf-layout-verified --pdf-metadata-verified --electronic --abstract-pages <实际摘要页数> --body-pages <实际正文页数> --expect-ai used --support "<PROJECT_ROOT>/支撑材料.zip" --support-pdf-verified --citation-report "<PROJECT_ROOT>/引用核验报告.json"
```

再执行 DOCX/LaTeX/PDF 工具规定的结构、编译和渲染门禁。RAR 或不可解析的二进制支撑文件会产生人工核验警告；只有实际核验后才能同时传入 `--allow-warning --override-reason "<核验依据>"`。任何错误、未核验引用或未解释的警告都视为未完成。交付回复报告官方来源、样本风格映射、引用核验报告、摘要/正文页数、文件大小、图表公式计数、子问题证据覆盖、AI 声明和全部命令退出码。
