# IDD フロー — JS/フロントエンド実装の言語固有差分（Phase 3〜6）

JS 側（`frontend/` 配下）の実装 Issue に適用する。Phase 3〜6 の**共通骨格は `SKILL.md`** にある。本ファイルは骨格の各「→ 言語別」マーカーに差し込む **JS 固有の差分のみ**を定義する。

---

## Phase 3 読むドキュメント

対象 Issue を読んだ後、以下を順に読む:

- `doc/Spec.md` — 何を作るか（ゲームルール・機能要件）
- `doc/DataSpec.md` — データ契約の SSOT（EventType 一覧・可視性ルール・ログ／エージェント JSON スキーマ）。どのイベントを public モードで非表示にするか・viewerMode 別の文面択一などはここを必ず参照する
- `doc/FrontendDesign.md` — フロントエンド設計（コンポーネント・CSS方針・スタブ差し替え計画）
- Issue に関連する `frontend/src/` 配下の実装ファイル

現状報告の「既存実装」は `frontend/src/` から要点を挙げる。

---

## Phase 4 暗黙の挙動・スタイル変更

HTML のルート要素・主要コンテナ・インタラクティブ要素を別のネイティブ要素へ変更する場合は、設計提示の「設計上の判断ポイント」に続けて、要素種別に由来して変わる以下の点を明示する:

- 既定のキーボード操作・フォーカス挙動（例: `button` の Enter/Space 発火）
- 暗黙の ARIA role / accessible name / スクリーンリーダー上の扱い
- フォーム挙動（例: `button` の既定 `type`）
- ブラウザ既定スタイル（UA stylesheet）と、それを打ち消す CSS reset
- 既存の JS ハンドラを削除・追加する理由（例: 手動 `onKeyDown` の削除）

---

## Phase 5 更新するドキュメント

- `doc/Spec.md` — 機能要件の変更があれば更新
- `doc/FrontendDesign.md` — コンポーネント設計・スタブ差し替え状況を更新

### `doc/GameData.md` の更新基準

フロントエンド実装 Issue では、実装中に発覚した以下の2種類のギャップを `doc/GameData.md` に記録する（Phase 6 実装後、コミット前に追記する）:

**1. データギャップ** — フロントエンドが必要だがログ（`public_log.jsonl` / `agents/*.json`）に存在しないフィールド

| 記録すべき内容 | 例 |
|---|---|
| フィールド名・用途・現状（❌ ログにない等）・対応方針 | `votes`: 観戦upvote数、ログにない、スタブ固定 |

**2. スタブUI** — データとは無関係に、機能が未実装のまま表示されている UI 要素

| 記録すべき内容 | 例 |
|---|---|
| UI要素・現状・対応方針 | ▲▼ upvote ボタン: アクションなし、仕様未定 |

> **判断基準**: 「このUIをユーザーがクリックしたとき何も起きない」「この値は常にスタブ固定」であれば記録対象。
> Playwright でブラウザ確認した際に目視でスタブ UI を洗い出し、漏れなく記録すること。

---

## Phase 6 コーディングルール

- **バックエンドの不具合はバックエンドで直す**: フロントエンドの表示が乱れる原因がバックエンドの誤出力（例: `day` フィールドが正しくない値を返す）の場合、まずバックエンド側で修正できないかを先に検討する。致命的でなければフロントを現状のままにし、バックエンドの修正を別 Issue で追跡する。フロント側にガード条件を足して回避するのは最終手段
- **フロントエンドのフィールド名はバックエンドのログ仕様に合わせる**: `ev.xxx` のフィールド名を新設するときは必ず `state/spectator_log.jsonl`（または `doc/GameData.md`）の実フィールド名を確認してから命名する。独自名をつけると後続の実装者（人間・AI問わず）がそのまま踏襲してバグが連鎖する
- **データアクセス境界**: fetch URL は専用モジュール（例: `archiveLoader.js`）に集約する。将来 FastAPI エンドポイントへの差し替えがそのファイルの1行変更で済むように設計する
- **Legacy-Adapter**: アーカイブデータの形式互換は `frontend/src/legacy/` に隔離する（Python 側の `src/legacy/` と同じ方針）。`Legacy-Adapter` コメントマーカーを付ける
- **Vite dev server での静的配信**: `state_archive/` などリポジトリルート配下のファイルを配信する場合、`fs.allow` だけでなく `configureServer` ミドルウェアで明示的にルーティングする（`fs.allow` のみでは `index.html` が返されることがある）

---

## Phase 6 Contract テスト TDD — テスト実行コマンド

テスト実行コマンド: `npm test`（vitest run）。

JS では構文・名前解決エラーの前処理は Python ほど明示的に要らないことが多いが、SKILL.md の核心（**アサートレベルの RED を確認**してから実装）は同じく必須。RED にならない場合はアサートが甘い。

---

## Phase 6 テスト docstring 記法

```js
/*
SUT: {テスト対象の関数・クラス・メソッド名}
Mock: {使用するMock/vi.fnとその目的。なければ「なし」}
Level: unit / integration / e2e
Objective: このテストが何を検証するかを1文で記述する
*/
```

---

## Phase 6 実装後チェック

```bash
npm test          # vitest run
npm run test:coverage
```

エラーがあれば修正してから次へ。

### Playwright によるブラウザ動作確認（必須ゲート）

テスト通過後、**コミット前に必ず** Playwright でブラウザを起動して golden path を目視確認する。コンポーネントの onClick・state 変化・レンダリングは純粋関数テストでは検証できないため、この確認がブラウザ/JS 境界の唯一の品質ゲートになる。

> **注意**: 新規 `import` を追加したファイルは HMR が効かないことがある。確認前にブラウザをリロードする。

#### DOM 要素の探し方（必ず守る）

CSS Modules のクラス名はビルドごとにハッシュ化される。**大まかなクラス名マッチ（`[class*="xxx"]`）はハッシュ部分が合わないと空振りする**。以下の優先順で要素を特定すること:

1. **`doc/FrontendDesign.md` を先に読む** — 画面遷移・コンポーネント構造・クリック先の仕様が書いてある。実装コードも合わせて読み、実際のクラス名・イベントハンドラを把握してから操作する
2. **テキスト・ラベルで探す** — ボタンやリンクのラベルが分かっているなら `Array.from(document.querySelectorAll('button')).find(el => el.textContent.trim() === 'xxx')` が確実
3. **`browser_snapshot` で構造を確認してから操作する** — 探す前にスナップショットを取り、実際の ref や要素構造を把握する
4. **CSS Modules クラスを使う場合は `evaluate` で実際のクラス名を確認してから** — `document.querySelector('[class*="cardBody"]').className` で確認後、一致するクラスをそのまま使う
5. **`closest()` で親要素に遡る** — テキストノードの `parentElement` や `closest('div')` でクリッカブルな親を探す

❌ **やってはいけない**: `[class*="phaseItem"]` や `[class*="gcard"]` などで要素を「なんとなく」マッチさせる → ハッシュが変わると空振りする

確認後、以下の形式でユーザーに報告し、**ユーザーにも動作確認を求める**:

```
## Playwright 動作確認

| 確認項目 | 結果 |
|---|---|
| {AC に対応する操作} | ✅ 正常 / ❌ 異常（詳細） |

ブラウザで動作を確認していただけますか？（localhost:{port}）
気になる挙動があれば教えてください。
```

ユーザーから問題なしの確認が取れたら次へ進む。

Python 側に変更がある場合は合わせて確認:
```bash
ruff check .
pytest --cov=src --cov-report=term-missing
```

### カバレッジ確認（vitest）

JS のカバレッジは vitest で計測する（`@vitest/coverage-v8` 導入済みの場合）:

```bash
npm run test:coverage   # vitest run --coverage
```

`npm test` だけでは JS のカバレッジは計測されない。Issue が JS 実装行を追加・変更する場合は `npm run test:coverage` を必ず実行する。

追加した実装行に対してテストが存在するか確認したのち、SKILL.md の「カバレッジ確認結果（共通の必須ゲート）」の表をユーザーに提示して承認を得る。
