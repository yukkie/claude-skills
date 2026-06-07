---
name: issue
description: >
  GitHub Issue 生成スキル for AgentVillage。個別の Issue を作る・直す・取り込むフェーズ専用（実装フローには入らない）。
  Use this skill when the user wants to create a new GitHub Issue, revise an existing Issue's requirements, or import raw idea notes — or invokes "/issue", "/issue create", "/issue revise <number>", "/issue import <file>", or says "Issue を作りたい", "このIssueを最新化して", "メモをIdeas.mdに取り込んで" など。
  Subcommands: "issue create" gathers requirements conversationally and creates a GitHub Issue; "issue revise <number>" reconciles an existing Issue with the current state and proposes a body update; "issue import <file>" imports raw markdown notes into doc/Ideas.md without creating Issues.
  実装に着手したくなったら本スキルではなく `/idd <番号>`（実装フロー）へ案内する。バックログ全体の棚卸し・優先度づけは `/backlog` を使う。
---

# Issue 生成（create / revise / import）

AgentVillage の GitHub Issue を生成・整備するスキル。**個別の Issue を1件ずつ扱う**フェーズ専用で、実装フロー（branch→設計→実装→PR）には進まない。実装に入りたくなったら `/idd <番号>` を案内する。バックログ全体の棚卸しは `/backlog`。

## サブコマンド: `issue create`

引数が `create` で始まる場合はこのフローへ進む。残りの引数（あれば）は要求の最初のヒントとして扱う。

### 目的
対話ベースで要求を深掘りし、仕様として十分に整理された GitHub Issue を作成する。
Issue には「何を・なぜ・受け入れ条件」を記載する。実装方針は不要（それは `/idd` の設計フェーズで決める）。

### フロー

```
[C-1] ヒアリング（対話で要求を整理）
[C-2] Issue ドラフト提示    ← 確認
[C-3] Issue 作成 + Ideas.md 追記
```

#### C-1 ヒアリング

ユーザーの入力から以下の3点が揃っているか確認し、足りない点だけ追加で質問する:

1. **何を** — 追加/変更したい機能・動作の概要
2. **なぜ** — 背景・動機・解決したい問題
3. **受け入れ条件** — 「これができたら完了」と言える具体的な状態

既に書いてくれている内容は再度聞かない。3点が揃ったら C-2 へ進む。

#### C-2 Issue ドラフト提示

**振る舞い変更のない refactoring の場合**: ラベルが `tech-debt` かつ Requirements に挙動変更が含まれないときは、AC に「既存の振る舞いは変わらない（テスト・ログ出力・表示が変化しない）」を明示的に追加する。実装者が「挙動を改善しよう」と踏み込まないためのガードレール。

以下のフォーマットで提示し、確認を取る:

```
## Issue ドラフト

**タイトル**: {簡潔な英語タイトル（50文字以内）}

**本文**:
---
## Background
{なぜ必要か}

## Requirements
{何を実現するか（箇条書き）}

## Acceptance Criteria
- [ ] {完了条件1}
- [ ] {完了条件2}
---

**ラベル**: {enhancement / tech-debt / bug から該当するもの}

このIssueを作成してよいですか？ [y/N / 修正コメント]
```

修正コメントがあればドラフトを更新して再提示する。

#### C-3 Issue 作成

承認後、`mcp__plugin_github_github__issue_write` ツールで作成する（body の長文 Markdown をシェル経由で渡すと PowerShell のクォート／here-string で事故るため、`gh issue create` を直接呼ばずこのツールを使う）:
```
mcp__plugin_github_github__issue_write(
  method="create",
  owner="yukkie",
  repo="AgentVillage",
  title="{タイトル}",
  body="...",            # 長文 Markdown をそのまま渡せる
  labels=["{ラベル}"],
)
```
返り値の `url` が作成された Issue の URL。

作成後、`doc/Ideas.md` のリスト先頭に `❌` マークで追記する。
`docs/add-issue-{番号}-to-ideas` ブランチを作成してコミットし、PR を作成する。

> **⚠️ 注意**: Ideas.md 追記の PR 本文・コミットメッセージには `Closes #XX` / `Fixes #XX` を**絶対に書かない**。
> GitHub がマージ時に Issue を自動クローズしてしまうため。`Related to #XX` も不要。Issue 番号への言及は一切しないこと。

Issue番号を表示して完了。続けてそのIssueに取り組むか確認する:
```
Issue #{番号} を作成しました。
続けてこのIssueの実装に取り組みますか？ [y/N]
```

`y` の場合は **`/idd {番号}` を実行するよう案内する**（実装フローは別スキル `/idd` が担う。本スキルからは自動遷移できないため、ユーザーに `/idd {番号}` の実行を促す）。

---

## サブコマンド: `issue import <file>`

引数が `import` で始まる場合はこのフローへ進む。続く引数はインポートするファイルパス。

### 目的
チャットやメモで整理した生の Markdown ファイルを読み込み、`doc/Ideas.md` に統合する。
GitHub Issue は作成しない — "アイデアを整理する" フェーズ専用。

### フロー

```
[I-1] ファイル読み込み + Ideas.md の現状確認
[I-2] 整形ドラフト提示    ← 確認
[I-3] Ideas.md に書き込み
```

#### I-1 読み込み

入力ファイルと `doc/Ideas.md`（存在する場合）を読む。

- **Ideas.md が存在しない**: 新規作成モード
- **Ideas.md が存在する**: 追記モード（重複するアイデアはスキップ）

#### I-2 整形ドラフト提示

入力内容をクラスタリングして以下のカテゴリに振り分ける:

| カテゴリ | 説明 |
|---|---|
| コア機能 | ゲームの根幹に関わる機能 |
| 拡張機能 | あると良い追加機能 |
| 技術的負債 / 改善 | リファクタリング・設計改善 |
| 保留 / 未検討 | まだ判断できないもの |

ドラフトを提示して確認を取る:

```
## import ドラフト

### 新規追加（{N}件）
{カテゴリごとに箇条書き}

### スキップ（重複 {M}件）
{重複と判断した理由を簡潔に}

このまま doc/Ideas.md に書き込みますか？ [y/N / 修正コメント]
```

修正コメントがあれば振り分けを更新して再提示する。

#### I-3 書き込み

承認後、`doc/Ideas.md` を更新する。

- 新規作成モード: ファイルを新規作成して書き込む
- 追記モード: 既存の各セクションに追記する（既存の内容は変更しない）

完了後:
```
{N}件のアイデアを doc/Ideas.md に追加しました。
続けて GitHub Issue を作成しますか？ [y/N]
```

`y` の場合は `issue create` フロー（C-1）へ進む。

---

## サブコマンド: `issue revise <番号>`

引数の先頭語が `revise` の場合はこのフローへ進む。続く引数は対象 Issue の番号。

### 目的
Issue 作成時点から状況が変わっているケース（別 Issue の実装で AC が既に満たされた・要件がユーザーの実際の意図と乖離した・関連 Issue のコメントに調査メモが蓄積した）を検知し、**Issue 本文を現状に合わせて最新化する**。

このサブコマンドは **Issue の整備専用**。照合 → Issue 更新 →（必要なら）Ideas.md 同期までで完結し、**実装フローには進まない**。実装に入りたい場合は revise 後に改めて `/idd {番号}` を実行する。

### フロー

```
[V-1] 照合（本文・全コメント・関連 Issue・memory・最近クローズ Issue を読む）
[V-2] 乖離レポート + revise 案提示    ← 確認（自動編集しない）
[V-3] Issue 更新 +（必要なら）Ideas.md 同期
```

#### V-1 照合

実装フロー（`/idd`）の「事前調査（関連の全数洗い出し）」と同じ要領で、以下を読んで現状と Issue 本文の差分を洗う:

- 対象 Issue の本文（`mcp__plugin_github_github__issue_read(method="get", owner="yukkie", repo="AgentVillage", issue_number={番号})`）+ 全コメント（`method="get_comments"` で同様に取得）
- 本文・コメント中の `#NN` 言及から関連 Issue を引く
- `memory/MEMORY.md` と関連 memory
- 関連キーワードで**最近クローズされた Issue**（`mcp__plugin_github_github__list_issues(owner="yukkie", repo="AgentVillage", state="CLOSED")`）

#### V-2 乖離レポート + revise 案提示

照合結果を以下のフォーマットで提示する。**この時点では Issue を編集しない**:

```
## issue revise: Issue #{番号} 照合結果

### 現状と乖離している箇所
- {要件X}: {何がどう変わったか・根拠（別 Issue #NN / コメント / memory）}

### 既に解決済みの AC
- [x] {AC}: {#NN で充足済み}

### 意図と異なる要件
- {要件Y}: {乖離内容}

### revise 案（更新後の本文）
---
## Background
...
## Requirements
...
## Acceptance Criteria
- [ ] ...
---

この内容で Issue を更新しますか？ [y/N / 修正コメント]
```

修正コメントがあれば案を更新して再提示する。
**乖離が見つからなければ**「現状と一致しています。更新は不要です」と報告して終了する。

#### V-3 Issue 更新 +（必要なら）Ideas.md 同期

承認後、`mcp__plugin_github_github__issue_write` ツールで Issue 本文を更新する（長文 body をシェルに渡さないため）:
```
mcp__plugin_github_github__issue_write(
  method="update",
  owner="yukkie",
  repo="AgentVillage",
  issue_number={番号},
  body="...",   # 新しい Issue 本文（既存 body を置き換える）
)
```

続けて `doc/Ideas.md` を確認する。当該 Issue の行があり、revise でタイトル・要約が変わった場合のみ同期する（変化がなければ何もしない）。同期する場合は master 直 push 禁止のため `docs/revise-issue-{番号}` ブランチを作成してコミット・PR を作成する:
```bash
git checkout -b docs/revise-issue-{番号}
git add doc/Ideas.md
git commit -m "docs: sync issue #{番号} summary in Ideas.md after revise"
git push -u origin docs/revise-issue-{番号}
```
push 後、PR は `mcp__plugin_github_github__create_pull_request` ツールで作成する:
```
mcp__plugin_github_github__create_pull_request(
  owner="yukkie",
  repo="AgentVillage",
  head="docs/revise-issue-{番号}",
  base="master",
  title="docs: sync issue #{番号} in Ideas.md",
  body="...",   # Closes #XX は書かない（自動クローズ防止）
)
```

> Ideas.md 同期 PR の本文・コミットには `Closes #XX` を**書かない**（自動クローズ防止）。

更新内容を表示して完了。**ここで終了する**（実装フローには進まない。実装するなら `/idd {番号}`）。

---

## エラー処理

| 状況 | 対応 |
|---|---|
| `issue_read` が失敗 | Issue番号を確認してユーザーに報告。`doc/Ideas.md` の情報だけで続けるか確認する |
| `gh_issue_create` が失敗（`ok=false`） | `stderr` を表示し、ラベル名・リポジトリ指定を確認して再試行 |
