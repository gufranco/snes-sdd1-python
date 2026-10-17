# S-DD1

S-DD1は、スーパーファミコンの2本のゲームに搭載された算術符号の展開チップです。これをPythonで実装し、6,652本のストリームでsnes9x 1.63のデコーダと、エミュレータを介さずに2本の市販カートリッジと突き合わせています。

[English](README.md) | 日本語 | [简体中文](README.zh-Hans.md) | [繁體中文（香港）](README.zh-HK.md)

[![CI](https://github.com/gufranco/snes-sdd1-python/actions/workflows/ci.yml/badge.svg)](https://github.com/gufranco/snes-sdd1-python/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/gufranco/snes-sdd1-python)](https://github.com/gufranco/snes-sdd1-python/releases)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

ノイズのストリーム**4,000**本とカートリッジ形状のストリーム**2,652**本をsnes9x 1.63と比較して失敗**0**件、ヘッダ形状は**全16**種、長さは最大**65,536**バイト、形状は**11,306**本のストリームの全数調査から取得、テスト**603**件、ステートメントとブランチのカバレッジ**100%**、依存パッケージなし

```python
import random

import sdd1

noise = random.Random(1996).randbytes(64)
part = sdd1.Chip("sdd1")

for header in (0x00, 0x50, 0xA0, 0xF0):
    stream = part.decompress(bytes([header]) + noise[1:], 0, 8)
    print(f"{header:#04x}", stream.bitplanes, stream.context, stream.end, stream.data.hex())
```

```
0x00 2 0 7 00000100e204f604
0x50 4 1 7 00000100e104bd72
0xa0 4 2 7 00000100e204e008
0xf0 8 3 7 00000040040d4d2d
```

同じ63バイトのノイズの前に、4種類の異なるヘッダバイトを置いています。ヘッダの上位2ビットは出力が何枚のビットプレーンをインターリーブするかを選び、その次の2ビットは各プレーンの履歴のどのビットでコンテキストを選ぶかを決めます。各ストリームは8バイトの出力を要求し、7バイトの入力を読みます。`end`は読まなかった最初のバイトのオフセットです。

## インストール

| 要件 | バージョン |
|:--|:--|
| Python | 3.12以降 |
| git | 任意 |

```bash
git clone https://github.com/gufranco/snes-sdd1-python.git
cd snes-sdd1-python
python3 sdd1/doctor.py
```

このパッケージは標準ライブラリ以外を何もインポートしません。ドクターはファイルとして実行されるため、パッケージがインポートできないときでもレポートを出力します。マシンを確認し、チップを構築し、デコーダに空のストリームを与え、同梱の2つのコーパスをSHA-256ダイジェストとともに読み込みます。バグ報告には出力全体を貼り付けてください。正常なチェックアウトでは次の行で終わり、終了コード0を返します。チェックが失敗すると終了コード1を返します。

```
  6 checks, nothing to report
```

チェックアウトから`pip install .`を実行すると、同じレポートが`sdd1-doctor`コマンドとしてもインストールされます。

リリースは[セマンティックバージョニング](https://semver.org/)に従い、semantic-releaseがコミット履歴から作成します。すべてのリリースにはタグが付き、[リリースページ](https://github.com/gufranco/snes-sdd1-python/releases)に掲載されます。

## インターフェース

`sdd1.Chip(model)`はチップを1つ構築します。`model`は必須です。省略すると`UnknownModelError`が発生し、存在する名前が列挙されます。名前の照合では、大文字と小文字、ハイフン、アンダースコアを区別しません。

| モデル | 別名 | ビットプレーン | コンテキスト |
|:--|:--|:--|:--|
| `sdd1` | `s-dd1`, `sdd-1`, `sdd`, `nintendosdd1` | 最大8 | 32 |

```python
import sdd1

for name in ("sdd1", "s-dd1", "sdd-1", "sdd", "nintendosdd1", "S_DD1"):
    print(name, sdd1.Chip(name).model)

for asked in (None, "s-dd2"):
    try:
        sdd1.Chip(asked)
    except sdd1.UnknownModelError as refused:
        print(refused)
```

```
sdd1 sdd1
s-dd1 sdd1
sdd-1 sdd1
sdd sdd1
nintendosdd1 sdd1
S_DD1 sdd1
no model was named, and this package will not choose one for you. Name one of: sdd1
s-dd2 is not a model this package covers; it has sdd1
```

### 呼び出し

| 呼び出し | 効果 |
|:--|:--|
| `Chip.decompress(rom, offset, length)` | ヘッダバイトが`rom[offset]`にあるストリームをデコードし、`length`バイトの`Stream`を返します。`length`が0の場合は65,536を意味します |
| `Chip.reset()` | 何もせず、チップを返します。ストリーム間で引き継がれる状態はないため、消去するものがありません |
| `sdd1.decompress(rom, offset, length)` | 先にチップを構築せずに同じデコードを行います |
| `sdd1.bitplane_count(kind)` | ヘッダの上位2ビットが示すビットプレーン数です。種類0から3に対して2、4、4、8です |

`Chip.model`は正規のモデル名を保持します。`rom`には任意の`bytes`または`bytearray`を渡せます。ストリームは2バイトのヘッダから先が読まれ、`rom[offset]`より前には触れません。

### 戻り値

`Stream`は4つのフィールドを持つ名前付きタプルです。

| フィールド | 意味 |
|:--|:--|
| `data` | デコードされたバイト列です。`bytes`で、ちょうど`length`バイトです |
| `end` | デコーダが読まなかった最初の入力バイトのオフセットです |
| `bitplanes` | 2、4、8のいずれかで、ヘッダの上位2ビットから決まります |
| `context` | 0から3で、ヘッダの次の2ビットです。`CONTEXT_MASKS`の行を選びます |

### エラー

| エラー | 発生条件 |
|:--|:--|
| `UnknownModelError` | `Chip`にモデルが渡されないか、どのモデルにも該当しない名前が渡されたとき。メッセージには存在するモデルが列挙されます |
| `TruncatedStream` | `offset`が負のとき、`offset`以降に残るバイトが2未満のとき、または`length`バイトをデコードする前に入力が尽きたとき。例外は`offset`を保持します |

短いストリームは少ないバイトを返すのではなく例外を発生させます。そのため、呼び出し側が部分的なブロックを完全なブロックと取り違えることはありません。

```python
import random

import sdd1

noise = random.Random(1996).randbytes(64)

print(sdd1.decompress(noise, 10, 8))
print(len(sdd1.decompress(bytes(4096), 0, 0).data))

for offset, length in ((-1, 4), (63, 4), (0, 4096)):
    try:
        sdd1.decompress(noise, offset, length)
    except sdd1.TruncatedStream as refused:
        print("TruncatedStream at", refused)
```

```
Stream(data=b'u\xb3\x94\xe8\xff\x9e\x04\xe1', end=19, bitplanes=8, context=3)
65536
TruncatedStream at -1
TruncatedStream at 63
TruncatedStream at 0
```

### モジュールの内容

| 名前 | 内容 |
|:--|:--|
| `sdd1.MODELS` | `Model`レコードです。正規名をキーとします |
| `sdd1.Model` | 1件のレコードです。`name`、`summary`、`planes`、`contexts`、`aliases` |
| `sdd1.BITPLANE_COUNTS` | `(2, 4, 4, 8)`です。4種類のプレーン種別それぞれのプレーン数です |
| `sdd1.HEADER_BYTES` | 2です。ストリームの先頭のバイト数です |
| `sdd1.PLANE_COUNT` | 8です。ストリームがインターリーブする最大のプレーン数です |
| `sdd1.CONTEXT_COUNT` | 32です。コーダが保持するコンテキストの数です |
| `sdd1.MAX_LENGTH` | 65,536です。ストリームがデコードする最大量で、`length`が0のときに要求される量です |
| `sdd1.EVOLUTION` | 33状態のステートマシンです。各状態について、符号サイズと各結果の後の次の状態を持ちます |
| `sdd1.RUN_TABLE` | 128個のラン長です。1から128の置換で、7ビットの符号語で索引されます |
| `sdd1.CONTEXT_MASKS` | プレーンの10ビットの履歴に対する4組のマスクです。コンテキスト種別ごとに1組です |
| `sdd1.UnknownModelError`, `sdd1.TruncatedStream` | 呼び出し側が捕捉できるすべての例外です |
| `sdd1.__version__` | インストールされているバージョンです |

```python
import sdd1

print(sdd1.BITPLANE_COUNTS, [sdd1.bitplane_count(kind) for kind in range(4)])
print(sdd1.HEADER_BYTES, sdd1.PLANE_COUNT, sdd1.CONTEXT_COUNT, sdd1.MAX_LENGTH)
print(len(sdd1.EVOLUTION), sdd1.EVOLUTION[0], sdd1.EVOLUTION[25])
print(len(sdd1.RUN_TABLE), sorted(sdd1.RUN_TABLE) == list(range(1, 129)))
print([(hex(high), hex(low)) for high, low in sdd1.CONTEXT_MASKS])
```

```
(2, 4, 4, 8) [2, 4, 4, 8]
2 8 32 65536
33 (0, 25, 25) (0, 26, 1)
128 True
[('0x1c0', '0x1'), ('0x180', '0x1'), ('0xc0', '0x1'), ('0x180', '0x3')]
```

### コマンドラインツール

ドクターはファイルとして実行しますが、それ以外のツールはすべてリポジトリのルートからモジュールとして実行します。

| コマンド | 動作 | 終了コード |
|:--|:--|:--|
| `python3 sdd1/doctor.py` | マシン、チップ、2つのコーパスについて報告します | 0は正常、1はチェックの失敗 |
| `python3 -m conformance.vectors [file]` | すべてのノイズベクタをデコードしてダイジェストを比較します。`file`の既定値は[`conformance/vectors.json`](conformance/vectors.json)です | 0はすべて一致、1は不一致あり、2はファイルなし |
| `python3 -m conformance.corpus [file]` | カートリッジ形状のコーパスについて同じことを行います。既定値は[`conformance/corpus.json`](conformance/corpus.json)です | 0はすべて一致、1は不一致あり、2はファイルなし |
| `python3 -m conformance.extract <rom> <shapes out> [table]` | 所有するカートリッジから、ヘッダバイトと長さの全数調査を書き出します。`table`はオフセットと長さの組のJSONリスト、または`SDD1`タグを含むビルドです | 0は書き出し完了、1はストリームが見つからない、2は引数の誤りまたはROMなし |
| `python3 -m conformance.against_cartridges <cartridge> <expanded> <out.json> [lo] [hi]` | カートリッジの`lo`から`hi`までを走査し、デコードした先頭64バイトが展開済みイメージに現れ、カートリッジのどこにも現れないストリームを数えます | 0は書き出し完了、1は確認できたものなし、2は引数の誤りまたはファイルの欠落 |
| `python3 -m conformance.speed` | 2,000バイトを5回デコードし、速度の中央値を毎秒70,000バイトの下限と比較します | 0は下限以上、1は下限未満 |
| `python3 -m conformance.package <wheel>` | ビルドしたwheelがすべてのモジュールを含み、テストファイルを含まないことを確認します | 0は正常、1は不具合またはwheelなし、2は引数なし |
| `python3 -m conformance.links` | このファイル内のすべてのアドレスにリクエストを送り、JSONレポートを出力します | 0はすべてのアドレスが存在、1は少なくとも1つがステータス404または410 |

```bash
python3 -m conformance.vectors conformance/vectors.json
```

```
  4000 cases from conformance/vectors.json, against snes9x 1.63
  4000 agreed, 0 did not
```

## アートワークではなくノイズ

カートリッジから取り出したストリームは、ゲームのグラフィックスを圧縮したものです。そのようなストリームをテストデータとして同梱するリポジトリはゲームを配布することになります。そのため、このデコーダの根拠は、どのカートリッジの内容も含まないストリームから構築しています。

デコーダは、入力がかつて圧縮されたものかどうかを知りません。届いたバイトが何であれステートマシンを進め、決定的な結果を1つ出力します。[`conformance/vectors.json`](conformance/vectors.json)は、シード1996から生成した16,384バイトの擬似乱数とそのSHA-256、そしてその内部のオフセットと長さに対する4,000件のケースです。各ケースは、snes9x 1.63がその位置でデコードした結果のSHA-256を持ちます。これらのケースは16種のヘッダ形状すべてと、1バイトから2,048バイトまでの13種の出力長に及びます。

アートワークは、1枚の絵がたどる経路に沿って確率モデルを進めます。そのため、実際のストリームの集合はどこでも一致しながら、状態表の一部が一度も実行されないことがあります。ゲームはアーティストが必要とした形状を使います。ノイズの集合は16種すべてを網羅します。

## デコーダの仕組み

32個のコンテキストはそれぞれ、確率ではなくラン長を保持します。デコーダは符号語を読むと、出現しやすいシンボルが何回繰り返されるかを知り、その回数だけ出力してから次を読みます。`EVOLUTION`は、各状態がどの符号サイズを読み、各結果の後にコンテキストがどこへ移るかを示します。

各ビットはいずれかのビットプレーンに属し、各プレーンは自身の10ビットの履歴を保持します。その履歴を、ヘッダが選んだ`CONTEXT_MASKS`の行でマスクしたものがコンテキストを選びます。同じ入力バイトでも、そのプレーンでそれより前に何があったかによってデコード結果が変わります。

| プレーン種別、ヘッダのビット7と6 | インターリーブされるプレーン | プレーンの切り替わり方 |
|:--|:--|:--|
| `0` | 2 | 切り替わりません |
| `1` | 4 | 出力16バイトごとに組が2つ進み、8で折り返します |
| `2` | 4 | 出力16バイトごとに、組がプレーン0と1、プレーン2と3の間で交互に切り替わります |
| `3` | 8 | 各出力バイトは8枚のプレーンそれぞれから1ビットずつ取ります |

種別1と2は、2回目の切り替わりである32バイト目までは一致します。

```python
import random

import sdd1

noise = random.Random(1996).randbytes(64)
one = sdd1.decompress(bytes([0x40]) + noise[1:], 0, 48).data
two = sdd1.decompress(bytes([0x80]) + noise[1:], 0, 48).data

print(one[:32] == two[:32], next(at for at in range(48) if one[at] != two[at]))
```

```
True 32
```

## モデル

```python
import sdd1

model = sdd1.MODELS["sdd1"]
print(model)
print(model.name, model.planes, model.contexts, model.aliases)

part = sdd1.Chip("sdd1")
print(part.model, part.reset() is part)
```

```
<Model sdd1, up to 8 bit planes>
sdd1 8 32 ('s-dd1', 'sdd-1', 'sdd', 'nintendosdd1')
sdd1 True
```

モデルは1つです。このチップを搭載する2本のゲームは、同じ展開器を使います。両者のカートリッジはバンクをアドレス空間に割り当てる方法が異なりますが、これは展開器ではなくカートリッジに属するもので、ここではそのマッピングをモデル化していません。

## 正しいか

このチップのデータシートは公開されていないため、根拠の階層の最上段は空です。[`conformance/hardware.json`](conformance/hardware.json)はそのことを記録し、すべての定数に`"verified": false`を付け、代わりとなる根拠と、それぞれを確定させるものを示しています。

| 証拠 | 記録 | 結果 |
|:--|:--|:--|
| ノイズに対するsnes9x 1.63 | [`conformance/vectors.json`](conformance/vectors.json) | 4,000件、失敗0件 |
| カートリッジ形状に対するsnes9x 1.63 | [`conformance/corpus.json`](conformance/corpus.json) | 2,652件、失敗0件 |
| 市販カートリッジと、他者が作成したその展開版との比較、エミュレータなし | [`conformance/cartridges.json`](conformance/cartridges.json) | スターオーシャン（日本版）で16種の形状すべてにわたり55,023本のストリームを確認、別のゲームでの対照実験では1,306本 |
| 第三者のエンコーダ | [`conformance/independent.json`](conformance/independent.json) | 20組。18組は同一、2組は作者のエクスポートが持つすべてのバイトで一致し64バイト手前で終わる、相違0組 |
| 圧縮導入前のCapcomのプロトタイプ | [`conformance/prototype.json`](conformance/prototype.json) | デコードした2,852本のストリームのうち242本がそのまま現れ、311,264バイト |
| ソース内の表 | [`conformance/carried.json`](conformance/carried.json) | `EVOLUTION`、`RUN_TABLE`、`CONTEXT_MASKS`を値のSHA-256で固定 |

テストスイートは、`RUN_TABLE`が置換であること、`EVOLUTION`をたどるすべての連鎖がどちらの結果でも収束すること、どのマスクの組も同じビットを2回選ばないこと、同じオフセットでの短い読み取りが長い読み取りの接頭辞であることも確認します。

```python
import json
from pathlib import Path

from conformance import vectors


def record(name):
    return json.loads(Path(f"conformance/{name}.json").read_text())


passed, failed, _ = vectors.run(vectors.load())
print("noise", passed, failed)

found = record("cartridges")
print("cartridge", found["confirmed"], len(found["kinds"]), found["control"]["confirmed"])

held = record("independent")
print("encoder", len(held["pairs"]), held["reproduced"], held["shortByAuthor"], held["differs"])

proto = record("prototype")
print("prototype", proto["decoded"], proto["matchedInFull"], proto["bytesConfirmed"])
```

```
noise 4000 0
cartridge 55023 16 1306
encoder 20 18 2 0
prototype 2852 242 311264
```

### カートリッジ形状のコーパス

ノイズベクタは2,048バイト以下にとどまります。[`conformance/corpus.json`](conformance/corpus.json)は65,536バイトのブロック全体に達します。その2,652件のケースは、39種の長さで68種の異なるヘッダバイトを使い、シード20260818から生成した131,072バイトの本体に配置され、期待される出力はsnes9x 1.63の`sdd1emu.cpp`から得ています。ヘッダバイトと長さはチップのインターフェースであり、測定値です。カートリッジ由来の圧縮済みバイトはファイルに含まれません。

形状は、16種のうち14種にわたる11,306本のストリームの全数調査から取得しています。ファイルにはその全数調査の出典が記録されておらず、4本の市販カートリッジからは再現できません。[`conformance/divergences.json`](conformance/divergences.json)にその所見と根拠となる測定を記録しています。全数調査が決めるのはコーパスがどの形状を試すかであり、デコーダがそれらをどう扱うかではありません。また、ノイズの集合は16種の形状すべてに及びます。

```bash
python3 -m conformance.corpus conformance/corpus.json
```

```
  2652 cases from conformance/corpus.json, against snes9x 1.63 sdd1emu.cpp
  shapes measured from 11306 real streams, 14 of 16 kinds
  2652 agreed, 0 did not
```

### 手持ちのカートリッジを測定する

```bash
python3 -m conformance.extract cartridge.sfc shapes.json table.json
python3 -m conformance.against_cartridges cartridge.sfc expanded.sfc found.json
```

`extract`はヘッダバイト、長さ、件数を書き出し、圧縮済みのバイトは一切書き出しません。`against_cartridges`は件数、ヘッダバイト、各イメージの4種のダイジェストを書き出します。どちらの出力も共有できます。イメージはお使いのマシンにとどまります。

### 未解決の事項

[OPEN-QUESTIONS.md](OPEN-QUESTIONS.md)は、未解決の問題をそれぞれ、それを解決する測定とともに列挙しています。すべての出力値は、実機からの記録ではなく実装に依拠しています。不正なストリームに対する挙動は推測です。形状以外の2番目のヘッダバイトの意味は不明です。[`conformance/divergences.json`](conformance/divergences.json)は、出典が見かけより弱い箇所をそれぞれ記録しています。

## 開発に参加する

| 必要なもの | 場所 |
|:--|:--|
| すべてのゲートと実行順序 | [CONTRIBUTING.md](CONTRIBUTING.md) |
| コーディングエージェント向けの同じ内容 | [AGENTS.md](AGENTS.md) |
| このリポジトリがファミリーの他のリポジトリと共有する標準 | [FAMILY.md](FAMILY.md) |
| バグ報告 | [GitHub Issues](https://github.com/gufranco/snes-sdd1-python/issues) |
| セキュリティ報告 | [SECURITY.md](SECURITY.md) |

```bash
uvx ruff@0.16.3 format --check .
uvx ruff@0.16.3 check .
uvx --python 3.12 mypy==1.14.1
python3 -m coverage erase
for file in $(find sdd1 conformance -name '*.test.py' | sort); do
  python3 -m coverage run -a "$file"
done
python3 -m coverage report
python3 -m conformance.speed
```

各モジュールには、その名前を冠したテストファイルが隣にあり、それぞれ単独で実行できます。カバレッジはステートメントとブランチの100%を必須とするゲートです。スループットの下限チェックはカバレッジのステップとは別に実行します。

カートリッジのイメージをissueに添付したり、リンクしたりしないでください。ダイジェストはファイルを含まずにファイルを識別します。

## 参考資料

- snes9x 1.63、`sdd1emu.cpp`、https://github.com/snes9xgit/snes9x 。[`conformance/vectors.json`](conformance/vectors.json)と[`conformance/corpus.json`](conformance/corpus.json)のすべての期待出力を生成したデコーダです。事実のみを用いており、コードは取り込んでいません。
- S-DD1についてのRicohまたはNintendoの文書は知られていません。[`conformance/hardware.json`](conformance/hardware.json)はその調査を記録し、`documents`を空として列挙しています。
- 記録が言及するすべてのカートリッジ、展開版、プロトタイプのイメージは、そこでサイズと4種のダイジェストによって識別されています。ここにはいずれも含まれていません。

## 引用

[CITATION.cff](CITATION.cff)は、パッケージのバージョンを刻むスクリプトによってリリースごとに更新されます。

## ライセンス

MIT。[LICENSE](LICENSE)を参照してください。
