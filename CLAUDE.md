# Skills Repository

このディレクトリ (`~/.claude/skills/`) がスキルリポジトリのルートです。

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
