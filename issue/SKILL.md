---
name: issue
description: >
  GitHub Issue 生成スキル for AgentVillage。個別の Issue を作る・直す・分割する・取り込むフェーズ専用（実装フローには入らない）。
  Use this skill when the user wants to create a new GitHub Issue, revise an existing Issue's requirements, split an Issue into multiple, or import raw idea notes — or invokes "/issue", "/issue create", "/issue revise <number>", "/issue split <number>", "/issue import <file>", or says "Issue を作りたい", "このIssueを最新化して", "このIssueを分割して", "メモをIdeas.mdに取り込んで" など。
  Subcommands: "issue create" gathers requirements conversationally and creates a GitHub Issue; "issue revise <number>" reconciles an existing Issue with the current state and proposes a body update; "issue split <number>" splits one Issue into multiple and re-wires dependencies in both directions; "issue import <file>" imports raw markdown notes into doc/Ideas.md without creating Issues.
  実装に着手したくなったら本スキルではなく `/idd <番号>`（実装フロー）へ案内する。バックログ全体の棚卸し・優先度づけは `/backlog` を使う。
---

# Issue 生成（create / revise / import）

AgentVillage の GitHub Issue を生成・整備するスキル。**個別の Issue を1件ずつ扱う**フェーズ専用で、実装フロー（branch→設計→実装→PR）には進まない。実装に入りたくなったら `/idd <番号>` を案内する。バックログ全体の棚卸しは `/backlog`。

## 横断ルール: Issue 間の依存を Requirement / AC に書き戻す

Issue 間に依存が生じるとき、その依存を**依存する側の Issue に明示的に配線する**。依存が生じるのは主に次の2パターン:

- **分割**: 共通部品の抽出を別 Issue に切り出す・producer / consumer で割る・先行リファクタを分離する等。
- **フォローアップ／派生**: 実装中の積み残し・後で直す不具合・スコープ拡張ゲートで別 Issue 化した分など、**ある作業（元 Issue・PR）から事後に切り出す** Issue。

この横断ルールは `issue create`（分割・フォローアップの新規起票）と `issue revise`（既存 Issue 群の点検）の両方で適用する。

書き戻す内容は次の4点:

1. **依存元リンク**: 依存する側の Issue の本文冒頭に `依存: #NN（{部品名・成果物名／元作業の内容}）` を書く。依存先（共通部品の producer Issue／フォローアップ元の Issue・PR）への参照リンクを必ず張る。
2. **Requirement への利用義務・前提**: Requirement に依存内容を1行加える。分割 consumer なら「`#NN` で作る {部品名} を使う（独自再実装しない）」、フォローアップなら「`#NN` / PR #MM で入れた {対象} を前提に {積み残し・修正} を行う」。
3. **AC への検証条件**: 可能なら AC にも検証条件を加える（「{部品名} を用いて実装されている」「{元作業}の {挙動} を壊さない」等）。AC は実装の検証正本（SSOT）であり、依存はここに落として初めて担保される。
4. **依存先側の逆リンク（双方向化）**: 依存**先**の Issue（producer・共通部品を作る側）の本文にも `依存される Issue: #NN, #MM` を書く。依存を片方向（依存元→依存先）でしか持たないと、**依存先 Issue を後で分割したとき「この分割で誰の依存リンクを張り替える必要があるか」を機械的に辿れない**（実例: #521 を #521+#526 に分割した際、#521 に依存していた #523 のフィードカード依存を #526 へ張り替え忘れ、#523 の本文・AC が「#521 で共通化したフィードカード」と誤ったまま残った）。逆リンクがあれば分割時に依存元をたどって張り替えられる。

> **核心**: Issue を切り出すのは「作業を分ける」だけでなく「**依存を双方向に配線する**」こと。依存先 Issue 単独で完結させ、依存する側の本文に依存リンク・利用義務が現れなければ、実装者（人間・AI 問わず）は独自実装にドリフトしたり前提を見落とす（実例: #521 で `AgentRosterRow` を共通化したが、それを使う #522 / #523 の本文・AC に依存も利用義務も書かず、#522 実装時に左ペインを独自マークアップで再実装してしまった。レビューで初めて発覚し作り直した）。フォローアップ Issue も同様で、元 Issue・PR へのリンクと前提を書かないと、後から読む人・別セッションが文脈を辿れない。そして逆リンク（依存先→依存元）を欠くと、依存先を分割したときに依存元の張り替えが漏れる。**分割は `issue split` サブコマンドで行い、依存の張り替えを手順として担保する。**

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

**他 Issue・PR に依存する起票の場合**（分割 consumer・フォローアップ・派生など）: この Issue が既存／同時起票の別 Issue で作られる共通部品・成果物に依存する、または元 Issue・PR の積み残し／不具合修正である場合、「横断ルール: Issue 間の依存を Requirement / AC に書き戻す」に従い、本文冒頭の `依存: #NN`・Requirement の利用義務／前提・AC の検証条件をドラフトに織り込む。

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
- [ ] AC-1: {完了条件1}
- [ ] AC-2: {完了条件2}
---

**ラベル**: {enhancement / tech-debt / bug から該当するもの}

このIssueを作成してよいですか？ [y/N / 修正コメント]
```

> **AC には通し番号（`AC-1:`, `AC-2:`, …）を付ける**: `/idd` のテスト設計（AC ↔ Contract テスト対応）・AC 対応テストチェック・レビュー指摘が AC を番号で参照できるようにするため。番号は Issue 内で一意な通し番号とし、項目を削除しても番号を使い回さない（欠番のままでよい）。

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
- **依存の AC 反映点検**: この Issue が他の Issue・PR に依存している場合、その依存が本 Issue の本文（依存リンク）・Requirement（利用義務／前提）・AC（検証条件）に落ちているかを点検する。対象は次のいずれか:
  - **分割元・共通部品の producer**: 本文に `#515 §8.3` のような仕分け元への言及・`派生` / `切り出し` 等の語があるか、producer Issue 側が「この成果物を後続が使う」と書いているか。
  - **フォローアップ元**: この Issue が別 Issue・PR の積み残し／不具合修正なら、元 Issue・PR へのリンクと前提が書かれているか。

  落ちていれば「横断ルール: Issue 間の依存を Requirement / AC に書き戻す」に従い revise 案へ反映する。

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

### 依存の反映漏れ（分割 Issue 間）
- {共通部品・成果物名（producer #NN）}: {本 Issue の本文（依存リンク）/ Requirement / AC のどこに反映が欠けているか}

### revise 案（更新後の本文）
---
## Background
...
## Requirements
...
## Acceptance Criteria
- [ ] AC-1: ...
---

この内容で Issue を更新しますか？ [y/N / 修正コメント]
```

> revise 後の AC にも通し番号（`AC-1:` 形式）を付与する。未付番の既存 Issue はこの機会に付番する。付番済みの場合は既存番号を維持し、項目を削除しても番号を詰めない（コメント・レビュー指摘からの参照を壊さないため）。

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

## サブコマンド: `issue split <番号>`

引数の先頭語が `split` の場合はこのフローへ進む。続く引数は分割対象 Issue の番号。

### 目的
1つの Issue を複数の子 Issue に分割し、**依存を双方向に再配線する**。単に子 Issue を作るだけでなく、**分割対象に依存していた既存 Issue の依存リンク（依存先・Requirement・AC）を、分割後のどの子 Issue へ張り替えるか**まで担保するのがこのサブコマンドの核心。これを手順化しないと、分割で中身が別 Issue へ移ったときに依存元の張り替えが漏れる（実例: #521 を #521+#526 に分割した際、#521 に依存していた #523 のフィードカード依存を #526 へ張り替え忘れ、#523 が「#521 で共通化したフィードカード」と誤参照したまま残った）。

このサブコマンドは **Issue の整備専用**。分割案 → 依存再配線 → 子 Issue 反映 → 依存元 revise → Ideas.md 同期で完結し、**実装フローには進まない**。

### フロー

```
[SP-1] 分割対象 + その依存元 Issue 群を読む（依存の逆引き）
[SP-2] 分割案を提示（子 Issue への Requirement / AC 振り分け）  ← 確認
[SP-3] 依存の再配線案を提示（子 Issue 間 + 依存元の張り替え）  ← 確認
[SP-4] 子 Issue 作成/更新 + 依存元 Issue の revise + Ideas.md 同期
```

#### SP-1 分割対象 + 依存元の逆引き

- 分割対象 Issue の本文 + 全コメントを読む（`issue_read` の `get` / `get_comments`）。
- **依存元の逆引き（最重要）**: この Issue に依存している Issue を全列挙する。
  - まず本文の「依存される Issue: #NN」逆リンク（横断ルールで張られていれば）を辿る。
  - 逆リンクが無い／信頼できない場合は、`mcp__plugin_github_github__search_issues` 等で `#{番号}` を本文・コメントに含む Issue を検索し、この Issue を依存先として参照している Issue を拾う。
  - 各依存元が「この Issue の**何に**依存しているか」（どの成果物・どの AC）を特定する。分割でその成果物がどの子に移るかを次フェーズで決めるため。

#### SP-2 分割案を提示

分割対象の Requirement / AC を、子 Issue へどう振り分けるかを提示する。**この時点では Issue を作成・編集しない**:

```
## issue split: Issue #{番号} 分割案

### 子 Issue {N} 個への振り分け
- **子A（{タイトル案}）**: {担当する Requirement / AC}
- **子B（{タイトル案}）**: {担当する Requirement / AC}

### 分割の軸
{producer/consumer・言語・レイヤなど、なぜこの切り方か}

この分割でよいですか？ [y/N / 修正コメント]
```

> 分割の軸は AI が勝手に1案に決めず、複数案がありうるなら提示してユーザーに委ねる（`/idd` の事前調査・分割提案と同じ原則）。

#### SP-3 依存の再配線案を提示

SP-1 で洗い出した依存元それぞれについて、**分割後どの子 Issue を指すべきか**の張り替え案を提示する。横断ルールの4点（依存元リンク・Requirement・AC・逆リンク）に沿う:

```
## issue split: 依存の再配線案

### 子 Issue 間の依存
- {子B} は {子A} の {成果物} に依存 → 子B に `依存: {子A}`、子A に `依存される Issue: {子B}`

### 依存元 Issue の張り替え（既存 Issue の revise）
| 依存元 | 現状の依存リンク | 張り替え後 | 直す箇所 |
|---|---|---|---|
| #523 | 依存: #521（フィードカード） | 依存: #526（フィードカード） | 本文・Requirement・AC-5 |

この再配線でよいですか？ [y/N / 修正コメント]
```

> **漏らさない**: SP-1 で挙げた依存元が表に1行も漏れなく載っているか確認する。「この依存元はこの分割の影響を受けない」と判断したものも、影響なしと明記する（黙って落とさない）。

#### SP-4 反映

承認後、順に実行する:

1. **子 Issue の作成/更新**: 分割で新設する子は `issue create` の C-3（`issue_write` method=create + Ideas.md 追記 PR）に従う。元 Issue を子の1つとして残す場合は `issue_write` method=update で Requirement/AC を分割後の内容へ更新する。子 Issue 間の依存（双方向リンク）を本文に書く。
2. **依存元 Issue の revise**: SP-3 の張り替え表に従い、各依存元 Issue を `issue_write` method=update で更新する（依存リンク・Requirement・AC を分割後の子 Issue へ向け直す）。
3. **Ideas.md 同期**: 新設・タイトル変更があれば `docs/split-issue-{番号}` ブランチで Ideas.md を更新し PR を作成する（`Closes #XX` は書かない）。

完了後、作成/更新した Issue 番号と張り替えた依存元を一覧表示する。**ここで終了する**（実装するなら `/idd {番号}`）。

---

## エラー処理

| 状況 | 対応 |
|---|---|
| `issue_read` が失敗 | Issue番号を確認してユーザーに報告。`doc/Ideas.md` の情報だけで続けるか確認する |
| `gh_issue_create` が失敗（`ok=false`） | `stderr` を表示し、ラベル名・リポジトリ指定を確認して再試行 |
