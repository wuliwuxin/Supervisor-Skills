# 全局安装与跨 harness 使用

本仓库新增了离线安装器和 `supervisor` 总入口。12 个原有技能安装为
`supervisor-<原名>`，避免覆盖已有的 `deep-research` 等技能；原仓库文件保持原样。
安装器仅需 Python 3.9+，不下载模型、不修改 API key、系统提示词或 shell 配置。

## 安装

在本仓库根目录执行：

```bash
python3 scripts/supervisor_skills.py install --dry-run
python3 scripts/supervisor_skills.py install
supervisor-skills doctor
```

默认创建：

| 位置 | 内容 |
| --- | --- |
| `~/.local/share/supervisor-skills/releases/` | 独立版本副本，包含原始技能、脚本、中英文手册、PDF、图片和许可证 |
| `~/.local/share/supervisor-skills/current` | 当前版本链接 |
| `~/.agents/skills/supervisor*` | 13 个标准 Agent Skills 入口 |
| `~/.claude/skills/supervisor*` | 指向同一份技能的 Claude Code 入口 |
| `~/.local/bin/supervisor-skills` | 通用命令行入口 |

现有同名文件或不属于本安装的链接会导致安装停止，不会被覆盖。全局副本不依赖当前
仓库的位置，仓库被移动后仍能使用。若命令不在 PATH，可使用
`~/.local/bin/supervisor-skills`；安装器不改 shell 配置。

## 各工具如何发现

| Harness | 本次使用的全局发现目录 | 显式使用示例 |
| --- | --- | --- |
| Codex | `~/.agents/skills` | `$supervisor` 或 `$supervisor-paper-writer` |
| Claude Code | `~/.claude/skills` | `/supervisor` 或 `/supervisor-paper-writer` |
| Cursor | `~/.agents/skills` | 输入 `/`，选择 `supervisor` |
| Gemini CLI | `~/.agents/skills` | 自然语言指定技能；`/skills reload` 刷新 |
| OpenCode | `~/.agents/skills` | 自然语言指定 `supervisor` |
| GitHub Copilot | `~/.agents/skills` | 自然语言指定 `supervisor`，支持程度取决于客户端版本 |
| Pi | `~/.agents/skills` | `/skill:supervisor` |

例如：“请用 supervisor 评估这个研究想法……”或“用 supervisor-paper-polish 润色这段英文”。
原有单项技能保留自动匹配能力。新技能可在后续轮次发现；如果当前客户端缓存了技能，
刷新技能列表或新开会话。旧版本客户端若不识别共享目录，可用下面的 `--target`
安装到其原生目录，例如 `~/.cursor/skills` 或 `~/.codex/skills`。

这些是本机当前用户的全局安装，不会自动同步到另一台电脑或云端会话。
远程机器需复制本仓库并运行安装器，或使用导出的上下文。

目录规则核对来源（2026-11-27）：
[Codex](https://developers.openai.com/codex/skills)、
[Claude Code](https://code.claude.com/docs/en/skills)、
[Cursor](https://cursor.com/docs/skills)、
[Gemini CLI](https://geminicli.com/docs/cli/using-agent-skills/)、
[OpenCode](https://opencode.ai/docs/skills/)、
[GitHub Copilot](https://docs.github.com/en/copilot/concepts/customizations/agent-skills)。
Pi 另外核对了本机 1.5.2 安装包的 `docs/skills.md`。

## 任意支持 shell 或文本上下文的 harness

```bash
supervisor-skills list
supervisor-skills show idea-evaluator
supervisor-skills show paper-writer --file references/verification-ladder.md
supervisor-skills path paper-writer
supervisor-skills handbook
supervisor-skills export paper-writer > paper-writer-context.md
```

有文件访问能力的 agent 可直接运行 `show` 并按需读取引用文件。
`export` 将**所选的一个技能**及其 `references/*.md` 合并成文本，适合粘贴或上传到
没有 Skill 加载器的助手。它不附带其他技能、二进制图片、工具或渲染器；跨技能任务需
再导出对应技能。导出 `supervisor` 得到的是路由索引，并非全部技能全文。

接入新的 Skill 目录（会保留此前已登记的目录）：

```bash
supervisor-skills install --target "$HOME/.new-harness/skills"
```

独立测试或自定义安装位置：

```bash
python3 scripts/supervisor_skills.py --prefix /tmp/supervisor-demo install \
  --target /tmp/supervisor-demo-skills --bin-dir /tmp/supervisor-demo-bin
/tmp/supervisor-demo-bin/supervisor-skills doctor
```

## 更新与检查

本地仓库更新后，重新执行该仓库的安装脚本即可。也可以显式指定源码目录：

```bash
supervisor-skills install --source /path/to/Supervisor-Skills
supervisor-skills doctor
```

安装器先准备完整版本，再原子切换 `current`。之前的版本保留在 `releases/`；
新旧版本的来源、文件校验值和发现目录记录在各自的 `manifest.json`。
内容和发现目录相同且校验通过时，重复安装直接复用已有版本。若新源码删掉了已安装
技能，安装器会拒绝更新并保留原版本，避免残留断链。
`doctor` 验证文件完整性和发现链接，不代表已在每个客户端实际运行研究任务。

## 项目阅读结论与使用边界

主体是 10 个科研技能，另有 rebuttal 与 Draw.io 两个扩展。最主要的工作流是
选题/调研 → 论文逻辑 → 写作/作图 → 润色/投稿审核；手册是按需参考资料。
现有 `deep-research` 与本项目同名，因此采用统一前缀。原技能的检索、视觉和子代理
能力由运行它的 harness 提供；无子代理时可串行执行。

已通读主技能及 64 份参考资料、扩展技能与脚本、36 篇双语手册和项目文档；
配套 PDF 共 70 页已提取阅读文字，未逐页视觉审查所有截图。
旧手册包含与新版正文起草流程不同的限制、旧工具价格和实验室设置，安装器不将这些
内容写成全局规则，也不自动配置其中提及的服务。

Draw.io 裁图需要 Pillow，PNG 导出需要 Draw.io Desktop；纯文本技能不依赖它们。
批处理前需保证输出文件名唯一，并显式指定独立预览路径，避免覆盖已有示例图。
Rebuttal 技能中的经验统计缺少附带原始数据，不应作为新论文录用概率。

主体遵循 CC BY-NC-SA 4.0，保留 HKUST DIAL / Yuyu Luo 及贡献者署名；
Draw.io 扩展保留 MIT LICENSE。新增适配为路由入口、安装器、名称和本地链接转换。
