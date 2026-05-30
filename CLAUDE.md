# Skills Repository

このディレクトリ (`~/.claude/skills/`) がスキルリポジトリのルートです。

> **このディレクトリは git 管理されている**（リポジトリルートは `~/.claude/skills/`、remote: `yukkie/claude-skills`）。
> 親の `~/.claude/` は git リポジトリではないので、`~/.claude/` で `git` を実行すると "not a repository" になる。
> スキルファイルを編集したら、必ず `~/.claude/skills/` で `git` を実行してコミットすること。

## 構造

各スキルは独自のサブディレクトリに格納されています:

```
skills/
├── CLAUDE.md            # このファイル
├── idd/
│   ├── SKILL.md         # IDD スキル本体
│   └── references/      # フロー別参照ファイル
└── wisdom-capture/
    └── SKILL.md         # 教訓の言語化・固着スキル
```

## スキルの呼び出し

ユーザーが `/idd` などのスラッシュコマンドを入力すると、対応する `SKILL.md` がロードされます。

## 全スキル共通の姿勢: 教訓の取りこぼし防止

スキルの種類を問わず、作業セッションで「**ユーザーが Claude の提案を否認・修正し、その後に承認へ到達した**」場面があったら、そこに*言語化できる暗黙知*が表面化している。作業の区切り（PR 作成後・タスク完了時など）に達したら `wisdom-capture` スキルを起動し、その教訓をルール化・Issue 化・寝かせる、のいずれかとして y/N で提案する。

否認の瞬間には起動しない（割り込みは禁止）。承認到達まで待ち、区切りで一度だけ差し出す。詳細・不変条件は `wisdom-capture/SKILL.md` を参照。

## 変更時のルール

- スキルファイルを編集したら必ずコミットする
- コミットメッセージ形式: `feat(skills):` / `fix(skills):` / `docs(skills):`
- コミットしたら `origin master` に直接 push してよい（このリポジトリは master 直 push を許可する。AgentVillage の「master 直 push 禁止」ルールとは別運用）
