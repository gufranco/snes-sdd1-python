# S-DD1

以 Python 實現的 S-DD1，即兩款 Super Nintendo 遊戲所用的算術解壓器。它在 6,652 條數據流上與 snes9x 1.63 的解碼器逐一比對，並在不經任何模擬器的情況下以兩盒零售版卡帶驗證。

[English](README.md) | [日本語](README.ja.md) | [简体中文](README.zh-Hans.md) | 繁體中文（香港）

[![CI](https://github.com/gufranco/snes-sdd1-python/actions/workflows/ci.yml/badge.svg)](https://github.com/gufranco/snes-sdd1-python/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/gufranco/snes-sdd1-python)](https://github.com/gufranco/snes-sdd1-python/releases)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

**4,000** 條雜訊數據流與 **2,652** 條卡帶形態的數據流與 snes9x 1.63 比對，**0** 個失敗，涵蓋**全部 16** 種標頭形態，長度最高 **65,536** 位元組，形態取自 **11,306** 條數據流的普查，**688** 個測試，**100%** 語句及分支覆蓋率，無任何依賴

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

同樣的 63 位元組雜訊分別接在四個不同的標頭位元組之後。標頭最高兩位決定輸出交錯多少個位元平面，其後兩位決定以每個平面歷史中的哪些位元選取上下文。每條數據流要求 8 位元組輸出，讀取 7 位元組輸入，`end` 是它未讀取的第一個位元組的偏移量。

## 安裝

| 要求   | 版本        |
| :----- | :---------- |
| Python | 3.12 或更新 |
| git    | 任何版本    |

```bash
git clone https://github.com/gufranco/snes-sdd1-python.git
cd snes-sdd1-python
python3 sdd1/doctor.py
```

本套件只匯入標準程式庫的內容。診斷腳本以檔案形式執行，因此即使套件無法匯入，它仍會輸出報告。它檢查本機、建立晶片、向解碼器輸入一條空數據流，並以 SHA-256 摘要讀取隨附的兩個語料庫。提交任何錯誤報告時，請貼上它的完整輸出。在狀態正常的檢出副本上，它以下面這一行結束並以 0 退出；任何檢查失敗都會令它以 1 退出。

```
  6 checks, nothing to report
```

在檢出副本中執行 `pip install .` 亦會把同一份報告安裝為 `sdd1-doctor` 指令。

版本發佈遵循 [Semantic Versioning](https://semver.org/)，並由 semantic-release 根據提交歷史產生。每個版本都會加上標籤，並列於[發佈頁面](https://github.com/gufranco/snes-sdd1-python/releases)。

## 介面

`sdd1.Chip(model)` 建立一個晶片。`model` 為必填：省略它會引發 `UnknownModelError`，並列出可用的名稱。比對名稱時忽略大小寫、連字號及底線。

| 型號   | 別名                                    | 位元平面  | 上下文 |
| :----- | :-------------------------------------- | :-------- | :----- |
| `sdd1` | `s-dd1`, `sdd-1`, `sdd`, `nintendosdd1` | 最多 8 個 | 32     |

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

### 呼叫

| 呼叫                                   | 作用                                                                                                          |
| :------------------------------------- | :------------------------------------------------------------------------------------------------------------ |
| `Chip.decompress(rom, offset, length)` | 解碼標頭位元組位於 `rom[offset]` 的數據流，並傳回長度為 `length` 位元組的 `Stream`。`length` 為 0 代表 65,536 |
| `Chip.reset()`                         | 設定重設所定義的值，並傳回晶片本身。它設定的暫存器列於卡帶匯流排上的晶片一節                                  |
| `sdd1.decompress(rom, offset, length)` | 不必先建立晶片的同一解碼                                                                                      |
| `sdd1.bitplane_count(kind)`            | 標頭最高兩位所指定的位元平面數目：種類 0 至 3 分別為 2、4、4 或 8                                             |

`Chip.model` 保存標準型號名稱。`rom` 可以是任何 `bytes` 或 `bytearray`。數據流從其兩個標頭位元組開始讀取，`rom[offset]` 之前的內容一概不會觸及。

### 傳回內容

`Stream` 是一個有四個欄位的具名元組。

| 欄位        | 含義                                                      |
| :---------- | :-------------------------------------------------------- |
| `data`      | 解碼後的位元組，類型為 `bytes`，恰好 `length` 個          |
| `end`       | 解碼器未讀取的第一個輸入位元組的偏移量                    |
| `bitplanes` | 2、4 或 8，取自標頭最高兩位                               |
| `context`   | 0 至 3，即標頭其後兩位，用以選取 `CONTEXT_MASKS` 中的一行 |

### 錯誤

| 錯誤                | 引發條件                                                                                                        |
| :------------------ | :-------------------------------------------------------------------------------------------------------------- |
| `UnknownModelError` | `Chip` 沒有獲得型號，或獲得的名稱不對應任何型號。訊息會列出可用的型號                                           |
| `TruncatedStream`   | `offset` 為負數、從 `offset` 起剩餘不足 2 個位元組，或在解碼出 `length` 位元組之前輸入已耗盡。例外帶有 `offset` |
| `OutOfRange`        | `read` 或 `write` 給出的位址不是晶片會解碼的位址。訊息會列出該位址                                              |
| `EmptyRom`          | `Chip` 獲得的 ROM 沒有任何位元組                                                                                |

過短的數據流會引發例外，而不是傳回較少的位元組，因此呼叫者永遠不會把部分區塊誤當作完整區塊。

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

### 卡帶匯流排上的晶片

`sdd1.Chip(model, rom=None, seed=...)` 亦會建立主機實際與之通訊的晶片。`rom` 是卡帶的 ROM，類型為 `bytes` 或 `bytearray`；省略時晶片會以 `seed` 產生一個 4 MiB 的 ROM。建立完成時，每個暫存器都與開機時一樣，保存着從 `seed` 取得的值，只有 `reset()` 會為它們定下確定的值。

| 呼叫或屬性              | 效果                                                                                                                                                                                                                                  |
| :---------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `read(address)`         | 從一個 24 位元主機位址讀取一個位元組：`$00-3f,$80-bf:4800-480f` 的暫存器、`$00-3f,$80-bf:8000-ffff` 以 32 KiB 為一頁的程式，以及 `$c0-ff:0000-ffff` 的四個 1 MiB 視窗。讀取某條通道正在等候的視窗位址，會傳回該通道的下一個解壓位元組 |
| `write(address, value)` | 寫入 `$4800`、`$4801` 及 `$4804` 至 `$4807`，並監察 `$43x2` 至 `$43x6`，主機在這裡為每條 DMA 通道設定來源位址及位元組數目。寫入 ROM 不會改變任何東西                                                                                  |
| `reset()`               | 清除 `$4800` 及 `$4801`，令四個視窗指向首四個 megabyte，並忘記所有受監察的通道。傳回晶片本身                                                                                                                                          |
| `rom`                   | 晶片讀取的 ROM，類型為 `bytes`。讀取超出末端時會由頭重複                                                                                                                                                                              |

| 暫存器             | 內容                                                                                                                                                                                      |
| :----------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `$4800`            | 每條 DMA 通道一個位元：容許解壓                                                                                                                                                           |
| `$4801`            | 每條 DMA 通道一個位元：等候解壓。通道的位元組數目用完時，其位元會被清除，數目為 0 代表 65,536                                                                                             |
| `$4804` 至 `$4807` | 第 0 至 3 位元選擇在 `$c0-cf`、`$d0-df`、`$e0-ef` 及 `$f0-ff` 顯示的 ROM megabyte。`$4805` 的第 7 位元在程式區把 `$20-3f` 摺疊到 `$00-1f`，`$4807` 的第 7 位元把 `$a0-bf` 摺疊到 `$80-9f` |

在匯流排上，解碼器經由視窗讀取數據流，所以數據流永遠不會耗盡，而是繼續讀取 ROM 接下來的內容。`TruncatedStream` 只屬於對緩衝區呼叫的 `decompress`。每項暫存器事實都來自 ares 及 snes9x 兩個實作，兩者不一致的五處記錄在 [`conformance/divergences.json`](conformance/divergences.json)。

```python
import random

import sdd1

noise = random.Random(1996).randbytes(64)
rom = bytearray(0x200000)
rom[0x100000 : 0x100000 + 64] = bytes([0x50]) + noise[1:]
part = sdd1.Chip("sdd1", rom)
print(part)
print(part.reset())

for register, value in ((0x4302, 0x00), (0x4303, 0x00), (0x4304, 0xD0), (0x4305, 8), (0x4306, 0)):
    part.write(register, value)
part.write(0x4800, 0x01)
part.write(0x4801, 0x01)

print(bytes(part.read(0xD00000) for _ in range(8)).hex(), part.read(0x4801))
print(sdd1.decompress(rom, 0x100000, 8).data.hex(), hex(part.read(0xD00000)))

for address in (0x7E0000, 0x002000):
    try:
        part.read(address)
    except sdd1.OutOfRange as refused:
        print(refused)
```

```
<Chip sdd1 enable 5f/0b banks 09 89 04 81>
<Chip sdd1 enable 00/00 banks 00 01 02 03>
00000100e104bd72 0
00000100e104bd72 0x50
0x7e0000 is not an address this chip answers
0x002000 is not an address this chip answers
```

### 模組內容

| 名稱                                             | 內容                                                                |
| :----------------------------------------------- | :------------------------------------------------------------------ |
| `sdd1.MODELS`                                    | 各 `Model` 記錄，以標準名稱為鍵                                     |
| `sdd1.Model`                                     | 一筆記錄：`name`、`summary`、`planes`、`contexts`、`aliases`        |
| `sdd1.BITPLANE_COUNTS`                           | `(2, 4, 4, 8)`，四種平面種類各自的平面數目                          |
| `sdd1.HEADER_BYTES`                              | 2，數據流開頭的位元組數                                             |
| `sdd1.PLANE_COUNT`                               | 8，一條數據流最多交錯的平面數                                       |
| `sdd1.CONTEXT_COUNT`                             | 32，編碼器保存的上下文數目                                          |
| `sdd1.MAX_LENGTH`                                | 65,536，一條數據流最多解碼的長度，亦即 `length` 為 0 時要求的長度   |
| `sdd1.EVOLUTION`                                 | 33 個狀態的狀態機：每個狀態的編碼長度，以及每種結果之後的下一個狀態 |
| `sdd1.RUN_TABLE`                                 | 128 個遊程長度，是 1 至 128 的一個排列，以 7 位元碼字為索引         |
| `sdd1.CONTEXT_MASKS`                             | 作用於平面 10 位元歷史的四對遮罩，每種上下文種類一對                |
| `sdd1.UnknownModelError`、`sdd1.TruncatedStream` | 呼叫者可以捕捉的全部例外                                            |
| `sdd1.__version__`                               | 已安裝的版本                                                        |

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

### 命令列工具

除診斷腳本以檔案形式執行外，每個工具都以模組形式在儲存庫根目錄執行。

| 指令                                                                                    | 作用                                                                                                                                                                                                                                              | 退出碼                                                 |
| :-------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :----------------------------------------------------- |
| `python3 sdd1/doctor.py`                                                                | 報告本機、晶片及兩個語料庫的狀況                                                                                                                                                                                                                  | 0 正常，1 有檢查失敗                                   |
| `python3 -m conformance.vectors [file]`                                                 | 解碼每個雜訊向量並比對摘要。`file` 預設為 [`conformance/vectors.json`](conformance/vectors.json)                                                                                                                                                  | 0 全部一致，1 有不一致，2 沒有檔案                     |
| `python3 -m conformance.corpus [file]`                                                  | 對卡帶形態語料庫做同樣的事，預設為 [`conformance/corpus.json`](conformance/corpus.json)                                                                                                                                                           | 0 全部一致，1 有不一致，2 沒有檔案                     |
| `python3 -m conformance.extract <rom> <shapes out> [table]`                             | 從你擁有的卡帶寫出標頭位元組及長度的普查。`table` 是由偏移量與長度配對組成的 JSON 列表，或帶有 `SDD1` 標記的建置                                                                                                                                  | 0 已寫出，1 找不到數據流，2 參數錯誤或沒有 ROM         |
| `python3 -m conformance.against_cartridges <cartridge> <expanded> <out.json> [lo] [hi]` | 在 `lo` 與 `hi` 之間掃描卡帶，並統計前 64 個解碼位元組出現在展開映像檔中、卻不出現在卡帶任何位置的數據流                                                                                                                                          | 0 已寫出，1 沒有任何確認，2 參數錯誤或缺少檔案         |
| `python3 -m conformance.traced <traced> <table> <indexed> <indexing build> <out.json>`  | 根據追蹤所得的數據流表寫出一份卡帶普查。數據流表可以是 JSON 數對，也可以是載有 `STREAMS` 元組的 Python 檔案。它亦會統計有多少條數據流展開後，與一個以 `SDD1` 標籤索引的版本中某條數據流的位元組完全相同，並與把每個起點後移一個位元組的對照組比較 | 0 已寫出，1 數據流表中沒有數據流，2 參數錯誤或缺少檔案 |
| `python3 -m conformance.speed`                                                          | 把 2,000 位元組解碼 5 次，並以中位速率與每秒 70,000 位元組的下限比較                                                                                                                                                                              | 0 高於下限，1 低於下限                                 |
| `python3 -m conformance.package <wheel>`                                                | 檢查已建置的 wheel 是否包含每個模組且不含任何測試檔案                                                                                                                                                                                             | 0 正常，1 有問題或沒有 wheel，2 沒有參數               |
| `python3 -m conformance.links`                                                          | 請求本檔案中的每個網址並輸出 JSON 報告                                                                                                                                                                                                            | 0 每個網址仍然存在，1 至少一個狀態為 404 或 410        |

```bash
python3 -m conformance.vectors conformance/vectors.json
```

```
  4000 cases from conformance/vectors.json, against snes9x 1.63
  4000 agreed, 0 did not
```

## 以雜訊代替美術素材

取自卡帶的數據流就是遊戲經壓縮的圖像。以這類數據流作為測試數據的儲存庫等同散佈遊戲，因此這個解碼器的證據由不含任何卡帶內容的數據流構成。

解碼器並不知道它的輸入是否曾被壓縮。它對收到的任何位元組運行其狀態機，並產生一個確定的結果。[`conformance/vectors.json`](conformance/vectors.json) 包含以種子 1996 產生的 16,384 個偽隨機位元組及其 SHA-256，以及位於其中各偏移量與長度的 4,000 個案例。每個案例帶有 snes9x 1.63 在該處解碼結果的 SHA-256。這些案例涵蓋全部 16 種標頭形態及 13 種輸出長度，由 1 位元組至 2,048 位元組。

美術素材只會沿着一幅圖像所走的路徑推進機率模型，因此一組真實數據流可以處處一致，而狀態表的一部分卻從未執行。一款遊戲只使用其美術人員需要的形態；雜訊集則涵蓋全部 16 種。

## 解碼器的運作方式

32 個上下文各自保存一個遊程長度，而不是機率。解碼器每讀取一個碼字，便得知可能性較高的符號重複多少次，將它輸出那麼多次，然後才再次讀取。`EVOLUTION` 指出每個狀態讀取的編碼長度，以及每種結果之後上下文移往何處。

每個位元都屬於一個位元平面，每個平面各自保存 10 位元的歷史。該歷史經標頭所選的 `CONTEXT_MASKS` 那一行遮罩後，便選出上下文。同一個輸入位元組會因該平面之前的內容不同而解碼為不同結果。

| 平面種類，標頭第 7 及第 6 位 | 交錯的平面數 | 平面如何輪換                                                   |
| :--------------------------- | :----------- | :------------------------------------------------------------- |
| `0`                          | 2            | 不輪換                                                         |
| `1`                          | 4            | 每 16 個輸出位元組，平面對前移 2，到 8 時回繞                  |
| `2`                          | 4            | 每 16 個輸出位元組，平面對在平面 0 及 1 與平面 2 及 3 之間切換 |
| `3`                          | 8            | 每個輸出位元組從 8 個平面各取一位                              |

種類 1 及 2 在第二次輪換之前一致，即 32 個位元組之後才出現分歧：

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

## 型號

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

只有一個型號。載有這枚晶片的兩款遊戲使用同一個解壓器及同一組暫存器。它們的卡帶容量不同，而記憶庫暫存器能涵蓋全部容量。

## 它是否正確

沒有人發表過此晶片的數據手冊，因此權威階梯的最高一級是空的。[`conformance/hardware.json`](conformance/hardware.json) 記錄了這一點，把每個常數標記為 `"verified": false`，並列出替代的證據，以及能確定每個常數的依據。

| 見證                                                  | 記錄                                                           | 結果                                                                                                                                       |
| :---------------------------------------------------- | :------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------- |
| snes9x 1.63，雜訊                                     | [`conformance/vectors.json`](conformance/vectors.json)         | 4,000 個案例，0 個失敗                                                                                                                     |
| snes9x 1.63，卡帶形態                                 | [`conformance/corpus.json`](conformance/corpus.json)           | 2,652 個案例，0 個失敗                                                                                                                     |
| 零售版卡帶對照他人製作的展開版本，不經任何模擬器      | [`conformance/cartridges.json`](conformance/cartridges.json)   | 在 Star Ocean（日本版）中確認 55,023 條數據流，涵蓋全部 16 種形態；在另一款遊戲上的對照運行為 1,306 條                                     |
| 第三方的編碼器                                        | [`conformance/independent.json`](conformance/independent.json) | 20 對：18 對完全相同，2 對在作者匯出的每個位元組上一致但短少 64 位元組，0 對不同                                                           |
| 壓縮之前的一個 Capcom 原型                            | [`conformance/prototype.json`](conformance/prototype.json)     | 2,852 條已解碼數據流中有 242 條原封不動地出現在其中，共 311,264 位元組                                                                     |
| 對第四盒卡帶的 DMA 追蹤，與另一版本的索引普查互相核對 | [`conformance/traced.json`](conformance/traced.json)           | Street Fighter Zero 2（日本版）中追蹤所得的 2,855 條數據流裡，有 2,732 條展開後與美國版數據流表中某條數據流的位元組完全相同，對照組為 0 條 |
| 原始碼中的表格                                        | [`conformance/carried.json`](conformance/carried.json)         | `EVOLUTION`、`RUN_TABLE` 及 `CONTEXT_MASKS` 以其數值的 SHA-256 固定                                                                        |

測試套件亦檢查 `RUN_TABLE` 是一個排列、經 `EVOLUTION` 的每條鏈在兩種結果下都會收斂、沒有任何遮罩對重複選取同一位元，以及在同一偏移量上較短的讀取是較長讀取的前綴。

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

### 卡帶形態語料庫

雜訊向量不超過 2,048 位元組。[`conformance/corpus.json`](conformance/corpus.json) 則涵蓋一整個 65,536 位元組的區塊。它的 2,652 個案例使用 68 個不同的標頭位元組及 39 種長度，放置在以種子 20260818 產生的 131,072 位元組主體中，預期輸出來自 snes9x 1.63 的 `sdd1emu.cpp`。標頭位元組與長度是晶片的介面，也是一項量度。檔案中沒有任何來自卡帶的壓縮位元組。

這些形態取自一次普查，涵蓋 16 種中 14 種的 11,306 條數據流。檔案沒有記錄該普查的來源，而且無法從四盒零售版卡帶重現。[`conformance/divergences.json`](conformance/divergences.json) 載有這項發現及其背後的量度。普查決定語料庫測試哪些形態，而不決定解碼器如何處理其中任何一種；雜訊集則涵蓋全部 16 種形態。

```bash
python3 -m conformance.corpus conformance/corpus.json
```

```
  2652 cases from conformance/corpus.json, against snes9x 1.63 sdd1emu.cpp
  shapes measured from 11306 real streams, 14 of 16 kinds
  2652 agreed, 0 did not
```

### 量度你自己的卡帶

```bash
python3 -m conformance.extract cartridge.sfc shapes.json table.json
python3 -m conformance.against_cartridges cartridge.sfc expanded.sfc found.json
```

`extract` 寫出標頭位元組、長度及計數，從不寫出任何壓縮位元組。`against_cartridges` 寫出計數、標頭位元組及每個映像檔的四個摘要。兩者的輸出都可以分享；映像檔留在你的電腦上。

### 尚未解決的問題

[OPEN-QUESTIONS.md](OPEN-QUESTIONS.md) 列出每個尚未解決的問題，以及能解決它的量度。每個輸出值都建基於其他實現，而不是真實晶片的錄得數據。晶片遇到任何編碼器都不會產生的位元組時會做甚麼仍然未知，而暫存器介面所依據的兩個實現有五處不一致。第二個標頭位元組在形態以外的含義未知。[`conformance/divergences.json`](conformance/divergences.json) 記錄每個來源比表面看來更薄弱之處。

## 參與開發

| 需要                               | 位置                                                                 |
| :--------------------------------- | :------------------------------------------------------------------- |
| 每道關卡檢查及其執行次序           | [CONTRIBUTING.md](CONTRIBUTING.md)                                   |
| 供編程代理使用的同一內容           | [AGENTS.md](AGENTS.md)                                               |
| 本儲存庫與同系列其他專案共用的標準 | [FAMILY.md](FAMILY.md)                                               |
| 錯誤報告                           | [GitHub Issues](https://github.com/gufranco/snes-sdd1-python/issues) |
| 安全報告                           | [SECURITY.md](SECURITY.md)                                           |

```bash
uvx ruff@0.16.3 format --check .
uvx ruff@0.16.3 check .
uvx --python 3.12 --with types-setuptools==84.0.0.20260812 mypy==1.14.1
python3 -m coverage erase
for file in $(find sdd1 conformance -name '*.test.py' | sort); do
  python3 -m coverage run -a "$file"
done
python3 -m coverage report
python3 -m conformance.speed
```

每個模組旁邊都有一個以其命名的測試檔案，而且每個都可以獨立執行。覆蓋率是一道硬性關卡檢查，語句及分支須達 100%。吞吐量下限在覆蓋率步驟以外執行。

切勿在 issue 中附上卡帶映像檔，或連結到映像檔。摘要能識別檔案而不必攜帶檔案本身。

## 參考資料

- snes9x 1.63，`sdd1emu.cpp`，https://github.com/snes9xgit/snes9x ，即產生 [`conformance/vectors.json`](conformance/vectors.json) 及 [`conformance/corpus.json`](conformance/corpus.json) 中每個預期輸出的解碼器。只取用事實，沒有採用任何程式碼。
- ares 提交 `9408cb43d4948fc3ea6e152a307a34348df3fe04` 的 `ares/sfc/coprocessor/sdd1/sdd1.cpp`，https://github.com/ares-emulator/ares ，以及 snes9x 提交 `1bcc369e89f08243e0a462882fb1f3e42e51de3a` 的 `sdd1.cpp`、`ppu.cpp` 及 `dma.cpp`。[`conformance/hardware.json`](conformance/hardware.json) 中每項暫存器事實都讀自這兩個實現。只取用事實，沒有採用任何程式碼。
- 目前未知有任何關於 S-DD1 的 Ricoh 或 Nintendo 文件。[`conformance/hardware.json`](conformance/hardware.json) 記錄了搜尋過程，並把 `documents` 列為空。
- 記錄中提及的每個卡帶、展開版本及原型映像檔，都在該處以大小及四個摘要識別。本專案不攜帶其中任何一個。

## 引用本專案

[CITATION.cff](CITATION.cff) 會在每次發佈時，由標記套件版本的腳本更新。

## 授權

MIT。參見 [LICENSE](LICENSE)。
