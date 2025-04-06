# Security Policy

## Supported Versions

OpenKimi 是一个滚动更新的项目，我们基于提交（commit）次数而非传统版本号来定义支持范围。以下是当前支持的安全更新范围：

| Commit Range         | Supported          |
|----------------------|--------------------|
| Latest 100 commits   | :white_check_mark: |
| 101–200 commits ago | :x:                |
| 201–300 commits ago | :white_check_mark: |
| > 300 commits ago    | :x:                |

- **支持策略**：我们始终支持最近 100 次提交的代码版本，并额外支持 201–300 次提交前的版本作为过渡期。超过此范围的旧版本不再提供安全更新。
- **检查方法**：您可以通过 `git log --oneline | wc -l` 查看当前仓库的总提交次数，并与最新提交对比确定您的代码是否在支持范围内。

由于 OpenKimi 是滚动更新项目，我们建议用户始终保持与最新提交同步，以获得最佳的安全性和功能支持。

## Reporting a Vulnerability

如果您发现了 OpenKimi 中的安全漏洞，请按以下流程报告：

- **提交方式**：请在 GitHub 仓库提交 Issue，地址为 [https://github.com/Chieko-Seren/OpenKimi/issues](https://github.com/Chieko-Seren/OpenKimi/issues)。使用标题前缀 `[Vulnerability]` 并提供详细描述。
- **联系方式**：若涉及敏感信息，可通过邮件联系我们：chieko.seren@icloud.com。
- **响应时间**：我们会在收到报告后的 7 个工作日内确认并提供初步反馈。
- **处理流程**：
  - **接受漏洞**：如果漏洞被确认，我们将在下一次提交中修复，并在 Issue 中更新状态。通常修复会在 14 个工作日内完成并推送。
  - **拒绝漏洞**：如果漏洞不适用或无法重现，我们会在 Issue 中说明理由，并可能请求更多信息。
- **期望**：请提供漏洞复现步骤、影响范围及可能的利用方式，以加快处理速度。
