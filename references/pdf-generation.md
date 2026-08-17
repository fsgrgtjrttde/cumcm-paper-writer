# 论文 PDF 生成模块

`scripts/generate_paper_pdf.py` 是 CUMCM LaTeX 论文的统一 PDF 入口。它调用数学建模 Skill 的 `latex_paper.py`，不自行猜测模板、引擎或页数规则；命令依次执行环境诊断、真实编译和质量校验，任何一步失败都返回 `RESULT=FAIL`。

## 前置条件

- `PROJECT_ROOT` 中已有官方或内置模板复制件、主 `.tex`、图表/代码资源和 `latex-project.json`（由 `latex_paper.py init` 生成）。
- 参考文献已经写入 `.bib` 或可追溯的 `\bibitem`，并由 `scripts/verify_references.py --online` 生成 `RESULT=PASS` 的 JSON 报告。
- 已按当届规则确定所有题号、正文起始页和正文页数上限。CUMCM 2026 默认正文上限为 30 页；摘要页数和电子版匿名要求仍需人工检查。
- 运行环境可找到 `math-modeling/tools/latex/scripts/latex_paper.py`、XeLaTeX（或官方指定引擎）、参考文献后端、PDF 审计工具和 `pdftoppm`。缺少依赖时先报告阻塞，不要改用未经校验的替代编译链。

## 生成流程

新建项目先执行 `latex_paper.py doctor` 和 `init`；编辑已有项目时先确认主入口、模板来源和 `latex-project.json`，只修改 `PROJECT_ROOT` 副本。然后运行：

```powershell
python "<SKILL_ROOT>/scripts/generate_paper_pdf.py" `
  "<PROJECT_ROOT>/完整论文-LaTeX" `
  --main "main.tex" `
  --citation-report "<PROJECT_ROOT>/引用核验报告.json" `
  --questions q1 q2 q3 `
  --body-start-page 2 `
  --max-pages 30 `
  --output "<PROJECT_ROOT>/完整论文.pdf"
```

有附录时增加 `--appendix-start-page <实际页码>`；模板要求 LuaLaTeX 或 pdfLaTeX 时增加对应 `--engine`。主入口不在项目根目录时，`--main` 必须写相对路径。若需要替换已有 PDF，先确认旧版本可被替换，再传 `--overwrite`。

脚本执行：

1. 检查引用 JSON 的 `result=PASS` 和已核验条目数；不通过则不编译。
2. 运行 `latex_paper.py doctor` 检查引擎、文献后端和 PDF 审计依赖。
3. 在工具规定的临时副本中真实编译，发布 PDF 与 `.build.json` 成对生成。
4. 运行 `latex_paper.py validate`，检查公式、图表、引用、页数、页面尺寸、字体、图片 DPI、资源哈希和附录边界。
5. 在 PDF 旁写入 `<PDF文件名>.pdf-generation.json`，记录 PDF SHA-256、题号、页数阈值、引擎和引用报告路径。

## 生成后核验

通过脚本只表示 LaTeX 工具门禁通过，仍需按 PDF Skill 用 `pdftotext`/`pypdf` 提取文本，并用 `pdftoppm` 渲染摘要页、正文首尾页、公式、表格、图片和参考文献页进行人工抽检。电子版 CUMCM 论文还要运行 `validate_cumcm_paper.py`，提供 PDF 提取文本、实际摘要/正文页数、PDF 布局/元数据核验标记和 `--citation-report`。

以下情况不得交付：编译日志存在未解释警告、PDF 与源码哈希不匹配、引用报告为 `UNVERIFIED`、正文超过当届上限、摘要/正文边界不清、字体或中文乱码、图表缺失或任何子问题没有图表证据。
