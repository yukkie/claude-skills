# Skills Repository

このディレクトリ (`~/.claude/skills/`) がスキルリポジトリのルートです。

> **このディレクトリは git 管理されている**（リポジトリルートは `~/.claude/skills/`、remote: `yukkie/claude-skills`）。
> 親の `~/.claude/` は git リポジトリではないので、`~/.claude/` で `git` を実行すると "not a repository" になる。
> スキルファイルを編集したら、必ず `~/.claude/skills/` で `git` を実行してコミットすること。

## 構造

各スキルは独自のサブディレクトリに格納されています:

```
skills/
├── CLAUDE.md          # このファイル
└── idd/
    ├── SKILL.md       # IDD スキル本体
    └── references/    # フロー別参照ファイル
```

## スキルの呼び出し

ユーザーが `/idd` などのスラッシュコマンドを入力すると、対応する `SKILL.md` がロードされます。

## 変更時のルール

- スキルファイルを編集したら必ずコミットする
- コミットメッセージ形式: `feat(skills):` / `fix(skills):` / `docs(skills):`
- コミットしたら `origin master` に直接 push してよい（このリポジトリは master 直 push を許可する。AgentVillage の「master 直 push 禁止」ルールとは別運用）
