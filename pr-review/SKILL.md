---
name: pr-review
description: >
  AgentVillage の PR を、その PR が閉じる GitHub Issue の要件・受け入れ条件(AC)に照らしてレビューするスキル。
  ユーザーが「この PR をレビューして」「PR #123 見て」「レビューして頂戴」などと PR レビューを依頼したとき、
  または `/pr-review` を起動したときに必ず使う。このプロジェクトでは Issue に要件・仕様・AC が書かれており、
  それが検証の正本(SSOT)である。PR の diff と本文だけを見てレビューするのは不十分なので、
  必ず `closes #N` / `fixes #N` から Issue を引いて AC を1項目ずつ照合すること。
  コードの correctness は組み込みの `/code-review` に委譲し、このスキルは「仕様を満たしているか」に専念する。
---

# PR レビュー（Issue 照合型）

AgentVillage の PR レビューをガイドするスキル。

## このスキルの責務分担

このプロジェクトのレビューには2つの軸があり、担当を分ける:

| 軸 | 問い | 担当 |
|---|---|---|
| **仕様充足** | Issue の要件・AC を満たしているか | **このスキル**（Issue が SSOT） |
| **コード正当性** | correctness・簡素化・効率 | 組み込み `/code-review`（このスキルが内部で呼ぶ） |

なぜ分けるか: 「仕様を満たしているか」は Issue 本文・`doc/` の契約ドキュメント（[DataSpec.md](doc/DataSpec.md) など）を読まないと判断できない、プロジェクト固有の検証。一方 correctness は汎用問題なので車輪の再発明をせず組み込みに任せる。

## なぜ Issue を必ず読むのか

このプロジェクトでは Issue に「背景・要件・受け入れ条件(Acceptance Criteria)」まで書く運用をしている。PR の diff と本文だけ見てレビューすると、**せっかく書いた AC を照合せずに見落とす**。Issue が要求仕様の正本(SSOT)なので、PR が「コードとして妥当か」だけでなく「**約束した AC を実際に満たしたか**」を確認するのがこのプロジェクトのレビューの肝。

## フロー

### Phase 1: PR と Issue の特定

1. 引数から PR 番号を取得する。番号が無く現在ブランチに紐づく PR を見たい場合は `mcp__plugin_github_github__list_pull_requests(owner="yukkie", repo="AgentVillage", state="open")` で解決する。
2. PR のメタデータと diff を取得する:
   ```
   mcp__plugin_github_github__pull_request_read(method="get", owner="yukkie", repo="AgentVillage", pullNumber=<N>)
   mcp__plugin_github_github__pull_request_read(method="get_diff", owner="yukkie", repo="AgentVillage", pullNumber=<N>)
   ```
3. PR 本文から閉じる Issue 番号を**すべて**抽出する。`closes #N` / `fixes #N` / `resolves #N`（大文字小文字問わず）を対象とし、複数ある場合は全部拾う（1つの PR が複数 Issue を閉じることがある）。

> **Issue 参照が無い場合**: PR 本文に Issue 番号が見つからなければ、その旨を**警告として明示**し、ユーザーに確認する（「この PR は Issue を参照していません。仕様照合の正本がありません。PR 単体でレビューを続けますか? それとも対象 Issue を教えてもらえますか?」）。無自覚に PR 単体レビューへ陥らないことが重要。

### Phase 2: Issue の要件・AC を読む

抽出した各 Issue について本文を取得する:
```
mcp__plugin_github_github__issue_read(method="get", owner="yukkie", repo="AgentVillage", issue_number=<N>)
```

各 Issue から以下を**表に起こす**:
- 要件(Requirements)
- 受け入れ条件(Acceptance Criteria) — チェックボックス1個ずつ
- 設計候補が複数提示されている場合、PR がどれを採用したか（あるいは Issue にない第三の道を採ったか）

### Phase 3: AC 照合

各 AC 項目を、PR の diff・テスト・ドキュメントに照合し、判定を付ける:

| 判定 | 意味 |
|---|---|
| ✅ | 満たしている。**根拠となるファイル:行**を必ず示す |
| ❌ | 満たしていない／不足 |
| ⚠️ 未確認 | 自分では検証できていない（CI 実走結果待ち等）。何が未確認かを明記 |

照合は「それっぽい」で済ませず、AC が「テストが通る」なら該当テストの追加を、「DataSpec に明記」なら実際の追記行を、それぞれ diff 内で指さして確認する。

### Phase 4: 契約ドキュメントとの整合確認

AgentVillage はデータ契約を `doc/` の SSOT ドキュメントで管理している。PR がスキーマ・イベント・可視性ルールに触れる場合、対応ドキュメントとの整合を確認する:

- [doc/DataSpec.md](doc/DataSpec.md) — EventType 一覧・可視性ルール・ログ／エージェント JSON スキーマの SSOT
- [doc/Spec.md](doc/Spec.md) — ゲームルール・機能要件
- [doc/Architecture.md](doc/Architecture.md) — 設計方針・ADR

コードを変えたのに契約ドキュメントが古いまま、あるいは逆に乖離していないかを見る。

### Phase 5: コード正当性は `/code-review` に委譲

correctness・簡素化・効率の指摘は、組み込みの `/code-review` を呼んで取得する。このスキルでそれを再実装しない。`/code-review` の結果を受け取り、Phase 3-4 の仕様照合結果と**統合して1つのレビューにまとめる**。

> `/code-review` は現在の diff を対象にする。レビュー対象の PR ブランチをチェックアウトした状態で呼ぶか、対象を明示すること。

### Phase 6: レビュー出力

以下の構成でまとめる:

```
## レビュー結果: PR #<N> <title>

### Issue #<M> (<Issue title>) — ✅/⚠️/❌ 満たしている/一部/未達
| Acceptance Criteria | 判定 | 根拠 |
|---|---|---|
| ... | ✅ | file:line |

（複数 Issue があれば Issue ごとに繰り返す）

### 設計上の良い点
（あれば。責務分離・単純化など）

### 気になった点（ブロッカー / 非ブロッカーを区別）
（correctness は /code-review 由来、仕様面はこのスキル由来。出所が分かるように）

### 確認できていない点
（⚠️ 未確認の項目。自分が実走で確かめていないもの）

### 総評
（マージ可否の所感。LGTM / 軽微なコメント推奨 / 要修正 のいずれか）
```

## 検証の前提（このプロジェクト固有）

- **pre-commit が品質ゲート**: コミットが成功している変更は、pre-commit フックの `ruff`/`pytest` を通過している。「テスト未確認」と書かず、検証済みとして扱う。
- **CI(GitHub Actions)は回っていない**: CI 確認は不要。検証の正本は pre-commit。
- 「未確認」と書くのは、自分が実際に確認していない事項に限る（PR 本文のチェックボックスは作者の申告であって自分の確認ではない、等）。
