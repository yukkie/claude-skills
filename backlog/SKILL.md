---
name: backlog
description: >
  バックログ運営（backlog refinement）スキル for AgentVillage。バックログ全体を定期的に棚卸しする独立セッション専用。
  Use this skill when the user wants to run a backlog refinement / grooming session, triage the issue backlog, estimate story points, update priorities, or promote Ideas.md items to Issues — or invokes "/backlog" or says "バックログを整理したい", "リファインメントやって", "優先度を見直したい", "SP を見積もって" など。
  個別の Issue を1件作る・直すだけなら `/issue`（create/revise/import）。Issue を実装に落とすのは `/idd <番号>`。本スキルはバックログ「全体」を対象にする点が両者と異なる。
---

# バックログ運営（refinement）

AgentVillage のバックログを定期的に棚卸しする独立セッション。**バックログ全体**を対象に、昇格・SP 見積もり・優先度を一括で整える。個別 Issue の生成は `/issue`、実装は `/idd`。

## プロジェクト規律ファイル: `doc/project-discipline.md`

本スキルが参照するプロジェクト固有の価値観・優先度方針ファイル。
リポジトリに置くことでプロジェクトと一緒に管理・バージョン管理できる。

### ファイル形式

```markdown
# Project Discipline

## Sprint Goal
<!-- 現在のゴール。backlog refinement 実行時に更新する -->
ゴール: {例: ゲームが1ラウンド最後まで回ること}

## 優先度の価値観
<!-- 相対的な優先度判断の軸。考え方が変わったときだけ更新する -->
- リファクタリング vs 新機能: {例: 新機能優先 / バランス / リファクタリング優先}
- tech-debt の姿勢: {例: 積極的に返す / 詰まったら返す / 後回し}
- 安定性 vs 速度: {例: 安定性重視 / スピード重視 / バランス}
- その他: {プロジェクト固有の判断軸があれば}
```

---

## フロー

引数なしの `/backlog` で起動する。定期的なバックログ整理セッションとして、以下をまとめて行う:
1. **昇格レビュー** — Ideas.md の未実装アイデアを GitHub Issue に昇格できるか判断する
2. **優先度メンテ** — 既存 Issue のバックログを整理し、優先度ラベルを最新化する

Issue は作成/更新の直前に必ず確認を取る。

```
[R-RECON] Ideas.md ↔ Issue リスト 齟齬チェック ← 確認
[R-0]  project-discipline.md の確認・更新
[R-SP] Story Point 見積もり           ← 確認
[R-1]  Ideas.md 昇格候補レビュー      ← 確認
[R-2]  選択候補を Issue 化（必要に応じてヒアリング）
[R-3]  Issue バックログ優先度サジェスト ← 確認
[R-4]  優先度ラベル更新
[R-4b] Ideas.md 優先度同期・並び替え
[R-5]  コミット & PR 作成
```

#### R-RECON Ideas.md ↔ Issue リスト 齟齬チェック

後続フェーズが「Ideas.md の表」と「実 Issue」のどちらを参照しても破綻しないよう、**最初に両者を一致させる**。

**GitHub を SSOT とする。** 齟齬は原則 `doc/Ideas.md` 側を書き換えて解消し、GitHub の Issue 本文・ラベルはこのフェーズでは変更しない。

open / closed の両方を取得して突き合わせる:
```bash
gh issue list --repo yukkie/AgentVillage --state all --json number,title,state,labels --limit 200
```

`doc/Ideas.md` の「GitHub Issues（未実装タスク）」表の各行（`yukkie/AgentVillage#NNN`）と照合し、以下の齟齬を検出する:

| 種類 | 検出条件 | 修正方針（Ideas.md 側） |
|---|---|---|
| 🗑 Closed残存 | Ideas.md にあるが GitHub では `closed` | 行を**削除**する |
| ➕ 未記載 | GitHub に `open` なのに Ideas.md に行が無い | 適切なセクションに**行を追加**する |
| ✏️ メタ不一致 | title / 優先度ラベル / `sp:X` / 種別ラベルが食い違う | **GitHub を正**として Ideas.md を書き換える |
| ❓ 番号未確定 | Ideas.md が `❌`（番号なし）だが対応する実 Issue がある | 実 Issue 番号に紐付ける |

> 未記載 Issue のセクション配置（Milestone 2 / ゲームロジック系 / 将来フェーズ）は内容から推定する。判断が曖昧なものだけ確認する。

検出結果を提示する:

```
## Ideas.md ↔ Issue リスト 齟齬チェック

GitHub を正として Ideas.md を以下のように修正します:

| 種類 | # | 内容 | Ideas.md への操作 |
|---|---|---|---|
| 🗑 Closed残存 | #305 | GitHub で closed 済み | 行を削除 |
| ➕ 未記載 | #430 | open だが表に無い | ゲームロジック系に追加 |
| ✏️ メタ不一致 | #347 | 優先度ラベル high / 表は 🟡 | 🟡 → 🔴 |
| ❓ 番号未確定 | #424 | 表は ❌ だが実体あり | 行頭を ❌ → #424 相当に修正 |

齟齬なしの場合は「齟齬は見つかりませんでした」と表示する。

この内容で Ideas.md を修正しますか？個別に除外する場合は番号を指定してください。
例: "そのまま" / "skip #347" / "skip"
```

承認後、`doc/Ideas.md` を一括修正する（修正は R-5 のコミットに含める）。齟齬が無い／`skip` の場合は何も変更せず R-0 へ進む。

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

**⚠️ 要詳細化の場合**: 不足している情報だけヒアリングする（「何を・なぜ・受け入れ条件」の3点を揃える）。
- 何が不明かを明示してから質問する（例：「スコープが不明です。どの画面/フェーズが対象ですか？」）
- 3点が揃ったら Issue ドラフトを生成する

いずれの場合もドラフトのフォーマットは **`/issue` の C-2 と同じ**（Background / Requirements / Acceptance Criteria + ラベル）。
承認後に `mcp__gh-mcp__gh_issue_create` ツールで作成する（手順は `/issue` の C-3 と同じ。Ideas.md への追記・自動クローズ防止の注意も同様）。

#### R-3 Issue バックログ優先度サジェスト

オープンな Issue 一覧を取得する:
```bash
gh issue list --repo yukkie/AgentVillage --state open --json number,title,labels,body
```

`doc/project-discipline.md` の Sprint Goal・価値観と Issue 間の依存関係・工数感を踏まえて優先度をサジェストする。

また、エラーハンドリング・エッジケース・レアケースの Issue については、以下を確認する:
- 「実運用での再現が難しいか」を判断する
- 難しい場合、Issue 本文の Acceptance Criteria に `⚠️unit test mandatory` が記載されているかチェックする
- 記載がなければ、優先度更新と同時に Issue 本文に追記する（`mcp__gh-mcp__gh_issue_edit(repo="yukkie/AgentVillage", number={番号}, body="...")`。body 全体を置き換えるため、既存本文＋追記分をまとめて渡す）

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

#### R-4b Ideas.md 優先度同期

優先度ラベル更新後、`doc/Ideas.md` の優先度表記を GitHub ラベルに合わせて同期する。

- 絵文字マッピング: `priority:high` → 🔴 / `priority:medium` → 🟡 / `priority:low` → 🟢
- 優先度順（🔴 → 🟡 → 🟢）に行を並び替える
- 同一優先度内の順序は変更しない

#### R-5 コミット & PR 作成

`doc/Ideas.md` や `doc/project-discipline.md` に変更があった場合、以下の手順でコミット・PR を作成する。

**ブランチ名の形式**:

```
docs/backlog-refinement-#{セッション番号}
```

- セッション番号は 1 から始め、毎回の `/backlog` 実行で +1 する
- 現在のセッション番号は `git branch -a | grep backlog-refinement` で確認する

**手順**:
```bash
git checkout -b "docs/backlog-refinement-#{N}"
git add doc/Ideas.md doc/project-discipline.md
git commit -m "docs: backlog refinement #{N} — {変更内容の要約}"
git push -u origin "docs/backlog-refinement-#{N}"
```
push 後、PR は `mcp__gh-mcp__gh_pr_create` ツールで作成する:
```
mcp__gh-mcp__gh_pr_create(
  base="master",
  title="docs: backlog refinement #{N}",
  body="...",   # Closes #XX は書かない（自動クローズ防止）
)
```

> backlog refinement PR の本文・コミットには `Closes #XX` を**書かない**（自動クローズ防止）。

PR 作成後に URL を表示して終了。

---

## エラー処理

| 状況 | 対応 |
|---|---|
| `gh issue list` が失敗 | リポジトリ指定を確認してユーザーに報告 |
| `gh issue edit` が失敗 | ラベル名（`sp:` / `priority:`）が存在するか確認して再試行 |
| R-RECON で齟齬が大量（10件超） | 種類ごとにまとめて提示し、種類単位で承認を取る（全件個別確認は避ける） |
