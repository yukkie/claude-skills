---
name: idd
description: >
  Issue Driven Development skill for AgentVillage. Use this skill whenever the user wants to start working on a task, pick up an issue, begin development from a GitHub issue, or asks "次のIssueをやりたい", "このIssueを実装して", "/idd", or similar. Subcommands: "idd create" creates a new GitHub Issue through conversational requirement gathering; "idd import <file>" imports raw markdown notes into doc/Ideas.md without creating Issues; "idd refine" runs a backlog refinement session (promote Ideas.md items to Issues + update Issue priorities). Guides the full development lifecycle: idea import → backlog refinement → issue creation → issue selection → branch → design approval → docs update → implementation → PR. Always use this skill when the user invokes /idd (with or without an issue number or subcommand).
---

# Issue Driven Development (IDD)

このスキルは AgentVillage プロジェクトの開発フローをガイドする。

## サブコマンド: `idd create`

引数が `create` で始まる場合はこのフローへ進む。残りの引数（あれば）は要求の最初のヒントとして扱う。

### 目的
対話ベースで要求を深掘りし、仕様として十分に整理された GitHub Issue を作成する。
Issue には「何を・なぜ・受け入れ条件」を記載する。実装方針は不要（それは後の Phase 4 で決める）。

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

承認後:
```bash
gh issue create \
  --title "{タイトル}" \
  --body "..." \
  --label "{ラベル}" \
  --repo yukkie/AgentVillage
```

作成後、`doc/Ideas.md` の適切なセクションに `❌` マークで追記する。
`docs/add-issue-{番号}-to-ideas` ブランチを作成してコミットし、PR を作成する。

Issue番号を表示して完了。続けてそのIssueに取り組むか確認する:
```
Issue #{番号} を作成しました。
続けてこのIssueの実装に取り組みますか？ [y/N]
```

`y` の場合は Phase 2（ブランチ作成）へ進む。

---

## サブコマンド: `idd import <file>`

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

`y` の場合は `idd create` フローへ進む。

---

## プロジェクト規律ファイル: `doc/project-discipline.md`

`idd refine` が参照するプロジェクト固有の価値観・優先度方針ファイル。
リポジトリに置くことでプロジェクトと一緒に管理・バージョン管理できる。

### ファイル形式

```markdown
# Project Discipline

## Sprint Goal
<!-- 現在のゴール。idd refine 実行時に更新する -->
ゴール: {例: ゲームが1ラウンド最後まで回ること}

## 優先度の価値観
<!-- 相対的な優先度判断の軸。考え方が変わったときだけ更新する -->
- リファクタリング vs 新機能: {例: 新機能優先 / バランス / リファクタリング優先}
- tech-debt の姿勢: {例: 積極的に返す / 詰まったら返す / 後回し}
- 安定性 vs 速度: {例: 安定性重視 / スピード重視 / バランス}
- その他: {プロジェクト固有の判断軸があれば}
```

---

## サブコマンド: `idd refine`

引数が `refine` の場合はこのフローへ進む。

### 目的
定期的なバックログ整理セッション。以下の2つをまとめて行う:
1. **昇格レビュー** — Ideas.md の未実装アイデアを GitHub Issue に昇格できるか判断する
2. **優先度メンテ** — 既存 Issue のバックログを整理し、優先度ラベルを最新化する

Issue は作成/更新の直前に必ず確認を取る。

### フロー

```
[R-0]  project-discipline.md の確認・更新
[R-SP] Story Point 見積もり           ← 確認
[R-1]  Ideas.md 昇格候補レビュー      ← 確認
[R-2]  選択候補を Issue 化（必要に応じてヒアリング）
[R-3]  Issue バックログ優先度サジェスト ← 確認
[R-4]  優先度ラベル更新
```

#### R-0 project-discipline.md の確認・更新

`doc/project-discipline.md` が存在するか確認する。

**存在しない場合 — 初回インタビュー**:

以下をヒアリングし、ファイルを新規作成する:

```
project-discipline.md がまだありません。優先度サジェストのために数点確認します。

1. 今の Sprint Goal を一言で教えてください
   （例: ゲームが1ラウンド回る、デモ準備 など）

2. リファクタリングと新機能、どちらを優先しますか？
   （例: 新機能優先 / バランス / リファクタリング優先）

3. tech-debt はどう扱いますか？
   （例: 積極的に返す / 詰まったら返す / 後回し）

4. 他に判断軸があれば教えてください（スキップ可）
```

回答をまとめてファイル内容を提示し、承認後に `doc/project-discipline.md` を作成する。

**存在する場合 — Sprint Goal の確認のみ**:

ファイルを読み込み、Sprint Goal だけ更新が必要か確認する:

```
現在の Sprint Goal: {記載されているゴール}

今もこのままですか？変わっていれば教えてください。[Enter でそのまま続行]
```

変更があればファイルを更新してから次へ進む。

#### R-SP Story Point 見積もり

オープンな Issue 一覧を取得し、`sp:X` ラベルが付いていない Issue に SP を見積もって提示する。

**SP スケール（フィボナッチ）**:

| SP | 目安工数 | 例 |
|---|---|---|
| 1 | 数時間 | 定数の置き換え、小さなリネーム |
| 2 | 半日〜1日 | 単一クラスのリファクタリング |
| 3 | 1〜2日 | 複数ファイルにまたがる中規模変更 |
| 5 | 3〜5日 | モジュール分割・新機能の骨格実装 |
| 8 | 1〜2週間 | 大規模リファクタリング・機能追加 |
| 13 | 2週間以上 | アーキテクチャ変更・大型新機能 |

**ラベル形式**: `sp:1` / `sp:2` / `sp:3` / `sp:5` / `sp:8` / `sp:13`

表示フォーマット（SP未設定 Issue のみ対象）:

```
## Story Point 見積もり

| # | タイトル | 提案SP | 根拠 |
|---|---|---|---|
| 71 | Eliminate redundant role: str from ActorState | sp:2 | 単一クラスの変更、影響範囲は限定的 |
| 58 | Split GameEngine phases into dedicated modules | sp:8 | 複数モジュールへの分割、テスト影響大 |
| 21 | Day 2+ pre-night judgment phase | sp:5 | 新フェーズの追加、複数ファイル変更 |

変更を適用しますか？個別に修正する場合は番号=SP で指定してください。
例: "そのまま" / "58=5" / "skip"
```

`skip` の場合は R-1 へ。

承認後:
```bash
gh issue edit {番号} --add-label "sp:{値}" --repo yukkie/AgentVillage
```

全 Issue の処理が終わったら R-1 へ進む。

#### R-1 昇格候補レビュー

`doc/Ideas.md` を読み、`❌`（未実装）アイテムを列挙する。
各アイテムについて「受け入れ条件が書けそうか」で昇格準備度を判定する:

```
## Ideas.md 昇格候補レビュー

| # | アイデア | 判定 | 理由 |
|---|---|---|---|
| - | エージェントの感情モデル | ✅ 昇格可能 | 要件が明確 |
| - | BGM・SE の追加 | ⚠️ 要詳細化 | スコープ不明 |
| - | リプレイ機能 | ✅ 昇格可能 | 独立した機能として切り出せる |

Issue 化したいアイデアを選んでください（番号をカンマ区切り、または "skip"）:
（⚠️ のものも選択可。足りない情報はその場でヒアリングします）
```

`skip` の場合は R-3 へ。

#### R-2 選択候補を Issue 化

選択された各アイデアを1件ずつ処理する。

**✅ 昇格可能な場合**: Ideas.md の内容を元に Issue ドラフトを自動生成して提示する。

**⚠️ 要詳細化の場合**: `idd create` の C-1 と同様に、不足している情報だけヒアリングする。
- 何が不明かを明示してから質問する（例：「スコープが不明です。どの画面/フェーズが対象ですか？」）
- 3点（何を・なぜ・受け入れ条件）が揃ったら Issue ドラフトを生成する

いずれの場合もドラフトのフォーマットは `idd create` の C-2 と同じ（Background / Requirements / Acceptance Criteria）。
承認後に `gh issue create` で作成する。

#### R-3 Issue バックログ優先度サジェスト

オープンな Issue 一覧を取得する:
```bash
gh issue list --repo yukkie/AgentVillage --state open --json number,title,labels,body
```

`doc/project-discipline.md` の Sprint Goal・価値観と Issue 間の依存関係・工数感を踏まえて優先度をサジェストする:

```
## Issue バックログ 優先度サジェスト

Sprint Goal「{ゴール}」・価値観「{リファクタリング vs 新機能}」をもとにサジェストします。

| # | タイトル | 現在 | サジェスト | 理由 |
|---|---|---|---|---|
| 21 | Day 2+ pre-night judgment phase | （なし） | 🔴 high | Sprint Goal に直結するコア機能 |
| 38 | GameState dataclass導入 | 🟡 medium | 🟡 medium | tech-debt、後回し方針と一致 |
| 42 | エージェント感情モデル | （なし） | 🟢 low | 今の Goal では不要な拡張機能 |

変更を適用しますか？個別に修正する場合は番号と優先度を指定してください。
例: "そのまま" / "21=medium" / "skip"
```

**優先度ラベルの種類**: `priority:high` / `priority:medium` / `priority:low`

#### R-4 優先度ラベル更新

確定した変更内容を確認してから実行:

```
以下のラベルを更新します:
- Issue #21: （なし） → high
- Issue #42: （なし） → low

続けてよいですか？ [y/N]
```

承認後:
```bash
gh issue edit {番号} --add-label "priority:{値}" --remove-label "priority:{旧値}" --repo yukkie/AgentVillage
```

完了後にサマリーを表示する。

#### R-5 コミット & PR 作成

`doc/Ideas.md` や `doc/project-discipline.md` に変更があった場合、以下の手順でコミット・PR を作成する。

**ブランチ名の形式**:

```
docs/backlog-refinement-#{セッション番号}
```

- セッション番号は 1 から始め、毎回の `idd refine` 実行で +1 する
- 現在のセッション番号は `git branch -a | grep backlog-refinement` で確認する

**手順**:
```bash
git checkout -b "docs/backlog-refinement-#{N}"
git add doc/Ideas.md doc/project-discipline.md
git commit -m "docs: backlog refinement #{N} — {変更内容の要約}"
git push -u origin "docs/backlog-refinement-#{N}"
gh pr create --title "docs: backlog refinement #{N}" --body "..." --base master
```

PR 作成後に URL を表示して終了。

---

## 通常フロー

Issue選択 → ブランチ作成 → ドキュメント確認 → 設計承認 → ドキュメント更新 → 実装 → PR作成 の順に進み、**フェーズが変わるたびにユーザーの確認を取る**。

## フェーズ概要

```
[1] Issue 選択
[2] ブランチ作成          ← 確認
[3] ドキュメント確認（読む）
[4] 設計提示              ← 確認
[5] ドキュメント更新（書く）
[6] 実装 + テスト
[7] PR 作成               ← 確認
```

---

## Phase 1 — Issue 選択

### 番号が指定された場合（例: `/idd 42`）
そのまま Phase 2 へ進む。

### 番号が指定されていない場合
`doc/Ideas.md` を読み込み、未実装 Issue の一覧を表示する。

表示フォーマット:
```
## 取り組む Issue を選んでください

### 未実装タスク
| # | タイトル | 内容 |
|---|---|---|
| 21 | Day 2+ pre-night judgment phase | 昼開始前の判断フェーズを Day 2+ にも拡張 |
...

### 技術的負債 (tech-debt)
| # | 優先度 | タイトル |
|---|---|---|
| 37 | 🟡 | `build_system_prompt` のパラメータ過多 |
...

番号を入力してください（例: 42）:
```

ユーザーが番号を入力するまで待つ。

> **注意**: Ideas.md に載っている Issue が GitHub 上ですでに CLOSED になっている場合は、一覧表示後に「#XX は GitHub 上でクローズ済みです。Ideas.md から削除しますか？」と確認し、承認されたら `docs/cleanup-ideas` ブランチを作成して削除・コミットし、PR を作成する。

---

## Phase 2 — ブランチ作成

### ブランチ名の決め方

Issue のラベルに応じてプレフィックスを使い分ける:

| ラベル | プレフィックス |
|---|---|
| `enhancement` / その他 | `feature/` |
| `bug` | `bugfix/` |
| `tech-debt` | `refactor/` |

形式: `{prefix}issue-{番号}-{Issue タイトルを kebab-case に変換した短縮形}`

例:
- Issue #37「`build_system_prompt` のパラメータ過多」（tech-debt）→ `refactor/issue-37-build-system-prompt-params`
- Issue #24「Role class refactoring」（enhancement）→ `feature/issue-24-role-class-refactoring`

タイトルが長い場合は 4〜5 単語に収める。

### 確認プロンプト
```
ブランチを作成します:
  git checkout -b {prefix}issue-{番号}-{名前}

現在のブランチ: {現在のブランチ}
続けてよいですか？ [y/N]
```

承認後:
```bash
git checkout -b {prefix}issue-{番号}-{名前}
```

---

## Phase 3 — ドキュメント確認（読む）

Issue 詳細と以下のドキュメントを読み込み、現状を把握する:
```bash
gh issue view {番号} --repo yukkie/AgentVillage
```
- `doc/Spec.md` — 何を作るか（ゲームルール・機能要件）
- `doc/Architecture.md` — どう作るか（コンポーネント設計）
- `doc/DetailDesign.md` — どう実装するか（モジュール・クラス詳細）

関連する実装ファイルも読んでおく（`src/` 以下）。
この段階では何も変更しない。次の設計提示のインプットとして使う。

---

## Phase 4 — 設計フェーズ

Phase 3 で読んだ内容をもとに設計を整理して提示する:

```
## Issue #{番号}: {タイトル}

### 変更対象ファイル
- `src/xxx/yyy.py` — 〇〇を変更
- `tests/test_yyy.py` — テストを追加

### 変更内容
1. ...
2. ...

### 設計上の判断ポイント
- **判断1**: ...（選択肢A vs 選択肢B → Aを選ぶ理由）
- **判断2**: ...

### 影響範囲
- ...

この設計で実装を進めてよいですか？ [y/N / 修正コメント]
```

ユーザーが承認するまで待つ。修正コメントがあれば設計を更新して再提示する。

---

## Phase 5 — ドキュメント更新（書く）

設計承認後、以下のドキュメントに今回の変更を反映する:
- `doc/Spec.md` — 機能要件の変更があれば更新
- `doc/Architecture.md` — コンポーネント設計の変更があれば更新
- `doc/DetailDesign.md` — モジュール・クラス詳細を更新

**更新内容をユーザーに確認してから実装へ進む。**
変更がなければ「ドキュメントは最新です。実装に進みます。」と伝えて次へ。

---

## Phase 6 — 実装

### コーディングルール（CLAUDE.md より）
- インポートは絶対インポート: `from src.xxx import yyy`
- LLM に真実（役職・夜の結果）を持たせない
- LLM 出力は必ず JSON で受け取る（`speech`・`thought`・`intent`・`memory_update`）
- `thought`（腹の中）と `speech`（表の言葉）は別フィールドで管理

### 実装完了後のチェック
```bash
ruff check .
pytest
```

エラーがあれば修正してから次のフェーズへ進む。

コミットは実装完了・テスト通過後に行う:
```bash
git add {変更ファイルを個別に指定}
git commit -m "{コミットメッセージ}"
```

コミットメッセージの形式: `{type}: {変更内容の要約} (closes #{番号})`
例: `feat: add pre-night judgment phase for day 2+ (closes #21)`

---

## Phase 7 — PR 作成

PR の内容を以下のフォーマットで提示し、確認を取る:

```
## PR を作成します

タイトル: {PR タイトル（50文字以内）}

本文:
---
## Summary
- {変更点1}
- {変更点2}

## Test plan
- [ ] `ruff check .` パス
- [ ] `pytest` パス
- [ ] {機能固有のテスト観点}

Closes #{番号}

🤖 Generated with [Claude Code](https://claude.com/claude-code)
---

このPRを作成してよいですか？ [y/N]
```

承認後:
```bash
gh pr create \
  --title "{タイトル}" \
  --body "..." \
  --base master
```

PR URL を表示する。

### Ideas.md の更新

PR 作成後、`doc/Ideas.md` の該当 Issue 行を削除する。
この変更は現在の feature ブランチ上でコミットする（masterへの直接pushは禁止のため）:
```bash
git add doc/Ideas.md
git commit -m "docs: remove issue #{番号} from Ideas.md (completed)"
git push
```

完了。

---

## エラー処理

| 状況 | 対応 |
|---|---|
| `gh issue view` が失敗 | Issue番号を確認してユーザーに報告。`doc/Ideas.md` の情報だけで設計を続けるか確認する |
| `ruff check .` でエラー | エラーを修正してから次に進む（ユーザーに報告して一緒に直す） |
| `pytest` が失敗 | 失敗したテストの原因を調査して修正する |
| ブランチがすでに存在する | 既存ブランチを使うか新しい名前にするかユーザーに確認 |
