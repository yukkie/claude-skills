# IDD フロー — Python 実装の言語固有差分（Phase 3〜6）

Python 側（`src/` 配下）の実装 Issue に適用する。Phase 3〜6 の**共通骨格は `SKILL.md`** にある。本ファイルは骨格の各「→ 言語別」マーカーに差し込む **Python 固有の差分のみ**を定義する。

---

## Phase 3 読むドキュメント

対象 Issue を読んだ後、以下を順に読む:

- `doc/Spec.md` — 何を作るか（ゲームルール・機能要件）
- `doc/DataSpec.md` — データ契約の SSOT（EventType 一覧・可視性ルール・ログ／エージェント JSON スキーマ）。`LogEvent` / `EventType` / エージェント JSON を扱う Issue では必ず参照する
- `doc/Architecture.md` — どう作るか（コンポーネント設計）
- `doc/DetailDesign.md` — どう実装するか（モジュール・クラス詳細）
- Issue に関連する `src/` 配下の実装ファイル

現状報告の「既存実装」は `src/` から要点を挙げる。

---

## Phase 5 更新するドキュメント

- `doc/Spec.md` — 機能要件の変更があれば更新
- `doc/Architecture.md` — コンポーネント設計の変更があれば更新
- `doc/DetailDesign.md` — モジュール・クラス詳細を更新

---

## Phase 6 コーディングルール（CLAUDE.md より）

- インポートは絶対インポート: `from src.xxx import yyy`
- LLM に真実（役職・夜の結果）を持たせない
- LLM 出力は必ず JSON で受け取る（`speech`・`thought`・`intent`・`memory_update`）
- `thought`（腹の中）と `speech`（表の言葉）は別フィールドで管理
- **実運用での再現が難しいパス（エラーハンドリング・エッジケース・レアケース）は、優先度に関わらず単体テストを必ずセットで実装する（`⚠️unit test mandatory`）**
- テストの書き方・docstring 規約・テストレベル定義は [`tests/TestStrategy.md`](../../../../tests/TestStrategy.md) に従う

---

## Phase 6 Contract テスト TDD — 構文エラー RED の前処理

SKILL.md の TDD ルールに加え、Python では**コンパイルエラーレベルの RED を先に解消する**:

1. contract テストを書く
2. **構文・名前解決エラーの RED を解消する**: ImportError / AttributeError など構文・名前解決エラーで RED になっている場合は、先に空の関数・クラス・フィールドを作って解消する。コンパイルエラーの RED は false positive でアサートの正しさを検証できない。
3. `pytest` で **アサートレベルの RED を確認する**（SKILL.md の核心ゲート）
4. 実装する → GREEN を確認する → カバレッジ確認へ

テスト実行コマンド: `pytest`

---

## Phase 6 テスト docstring 記法

```python
"""
SUT: {テスト対象の関数・クラス・メソッド名}
Mock: {使用するMock/monkeypatchとその目的。なければ「なし」}
Level: unit / integration / e2e
Objective: このテストが何を検証するかを1文で記述する
"""
```

---

## Phase 6 実装後チェック

```bash
ruff check .
pytest --cov=src --cov-report=term-missing
```

エラーがあれば修正してから次へ。

### カバレッジ突合せ（coverage_diff.py）

`pytest` 通過後、カバレッジレポートの `Missing` 行と今回の変更差分を突合せる。補助スクリプト `~/.claude/skills/idd/scripts/coverage_diff.py` が表を自動生成する:

```bash
SCRIPT="$HOME/.claude/skills/idd/scripts/coverage_diff.py"

# coverage.json を生成（まだなければ）
pytest --cov=src --cov-report=json -q

# stage 前（未コミットの変更を確認）
python "$SCRIPT" --unstaged

# stage 後 / コミット後（master との差分を確認）
python "$SCRIPT"
```

スクリプトは git diff の各追加行（`+` で始まる）にカバレッジマーカーを付けて出力する:

| マーカー | 意味 |
|---|---|
| `[o]` | カバー済み（テスト不要） |
| `[x]` | Missing（テスト追加が必要） |
| `[ ]` | 計測対象外（コメント・空行・型アノテーション等） |

`[x]` が付いた追加行（`+` で始まる実装行）が残っていないか確認する。残っていればテストを追加して再チェック。その後、SKILL.md の「カバレッジ確認結果（共通の必須ゲート）」の表をユーザーに提示して承認を得る。
