# S-DD1

S-DD1 是两款 Super Nintendo 游戏中的算术解压芯片，本仓库用 Python 实现它，并以 snes9x 1.63 解码器在 6,652 个流上的结果和两盒零售版卡带为准进行校验，全程不依赖模拟器。

[English](README.md) &nbsp;|&nbsp; [日本語](README.ja.md) &nbsp;|&nbsp; 简体中文 &nbsp;|&nbsp; [繁體中文（香港）](README.zh-HK.md)

[![CI](https://github.com/gufranco/snes-sdd1-python/actions/workflows/ci.yml/badge.svg)](https://github.com/gufranco/snes-sdd1-python/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/gufranco/snes-sdd1-python)](https://github.com/gufranco/snes-sdd1-python/releases)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

**4,000** 个噪声流和 **2,652** 个卡带形态的流与 snes9x 1.63 对比，**0** 失败，覆盖**全部 16** 种头部形态，长度最多 **65,536** 字节，形态取自 **11,306** 个流的普查，**601** 个测试，**100%** 语句和分支覆盖率，无依赖

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

同样的 63 字节噪声分别接在四个不同的头部字节之后。头部的最高两位决定输出交织多少个位平面，接下来两位决定用每个平面历史中的哪些位来选择上下文。每个流请求 8 字节输出，读取 7 字节输入，`end` 是它没有读取的第一个字节的偏移量。

## 安装

| 要求 | 版本 |
|:--|:--|
| Python | 3.12 或更新 |
| git | 任意 |

```bash
git clone https://github.com/gufranco/snes-sdd1-python.git
cd snes-sdd1-python
python3 sdd1/doctor.py
```

本包只导入标准库中的内容。诊断脚本以文件方式运行，因此即使包无法导入，它也仍会输出报告。它检查本机环境，构建芯片，给解码器输入一个空流，并读取随附的两个语料库及其 SHA-256 摘要。提交任何 bug 报告时，请粘贴它的完整输出。在状态正常的检出上，它以下面这一行结束并以 0 退出；任一检查失败则以 1 退出。

```
  6 checks, nothing to report
```

在检出目录中执行 `pip install .`，还会把同一份报告安装为 `sdd1-doctor` 命令。

版本发布遵循 [Semantic Versioning](https://semver.org/)，由 semantic-release 根据提交历史生成。每个版本都打了标签，并列在[发布页面](https://github.com/gufranco/snes-sdd1-python/releases)上。

## 接口

`sdd1.Chip(model)` 构建一个芯片。`model` 是必需的：省略它会抛出 `UnknownModelError`，并列出现有的名称。匹配名称时忽略大小写、连字符和下划线。

| 型号 | 别名 | 位平面 | 上下文 |
|:--|:--|:--|:--|
| `sdd1` | `s-dd1`, `sdd-1`, `sdd`, `nintendosdd1` | 最多 8 | 32 |

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

### 调用

| 调用 | 作用 |
|:--|:--|
| `Chip.decompress(rom, offset, length)` | 解码头部字节位于 `rom[offset]` 的流，返回 `length` 字节的 `Stream`。`length` 为 0 表示 65,536 |
| `Chip.reset()` | 不做任何事，返回芯片本身。流与流之间不保留任何状态，所以没有需要清除的内容 |
| `sdd1.decompress(rom, offset, length)` | 同样的解码，无需先构建芯片 |
| `sdd1.bitplane_count(kind)` | 头部最高两位所指定的位平面数：类型 0 到 3 分别为 2、4、4 或 8 |

`Chip.model` 保存规范的型号名称。`rom` 可以是任意 `bytes` 或 `bytearray`。流从它的两个头部字节开始往后读取，`rom[offset]` 之前的内容不会被触及。

### 返回值

`Stream` 是一个有四个字段的命名元组。

| 字段 | 含义 |
|:--|:--|
| `data` | 解码出的字节，类型为 `bytes`，恰好 `length` 个 |
| `end` | 解码器没有读取的第一个输入字节的偏移量 |
| `bitplanes` | 2、4 或 8，取自头部最高两位 |
| `context` | 0 到 3，头部接下来的两位，用于选择 `CONTEXT_MASKS` 的行 |

### 错误

| 错误 | 抛出时机 |
|:--|:--|
| `UnknownModelError` | 给 `Chip` 的型号为空，或者名称不对应任何型号。消息中列出现有的型号 |
| `TruncatedStream` | `offset` 为负，从 `offset` 起剩余不足 2 字节，或者在解码出 `length` 字节之前输入就已耗尽。异常携带 `offset` |

过短的流会抛出异常，而不是返回较少的字节，这样调用方永远不会把不完整的块误当作完整的块。

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

### 模块内容

| 名称 | 内容 |
|:--|:--|
| `sdd1.MODELS` | `Model` 记录，以规范名称为键 |
| `sdd1.Model` | 一条记录：`name`、`summary`、`planes`、`contexts`、`aliases` |
| `sdd1.BITPLANE_COUNTS` | `(2, 4, 4, 8)`，四种平面类型各自的平面数 |
| `sdd1.HEADER_BYTES` | 2，流开头的字节数 |
| `sdd1.PLANE_COUNT` | 8，一个流最多交织的平面数 |
| `sdd1.CONTEXT_COUNT` | 32，编码器维护的上下文数 |
| `sdd1.MAX_LENGTH` | 65,536，一个流最多解码的字节数，也是 `length` 为 0 时请求的长度 |
| `sdd1.EVOLUTION` | 33 状态的状态机：每个状态的码长，以及每种结果之后的下一状态 |
| `sdd1.RUN_TABLE` | 128 个游程长度，是 1 到 128 的一个排列，以 7 位码字为索引 |
| `sdd1.CONTEXT_MASKS` | 作用于平面 10 位历史的四对掩码，每种上下文类型一对 |
| `sdd1.UnknownModelError`、`sdd1.TruncatedStream` | 调用方可以捕获的全部异常 |
| `sdd1.__version__` | 已安装的版本 |

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

### 命令行工具

除诊断脚本以文件方式运行外，每个工具都在仓库根目录下以模块方式运行。

| 命令 | 作用 | 退出码 |
|:--|:--|:--|
| `python3 sdd1/doctor.py` | 报告本机环境、芯片和两个语料库的状态 | 0 正常，1 有检查失败 |
| `python3 -m conformance.vectors [file]` | 解码每个噪声向量并比较摘要。`file` 默认为 [`conformance/vectors.json`](conformance/vectors.json) | 0 全部一致，1 有不一致，2 没有文件 |
| `python3 -m conformance.corpus [file]` | 对卡带形态语料库做同样的事，默认为 [`conformance/corpus.json`](conformance/corpus.json) | 0 全部一致，1 有不一致，2 没有文件 |
| `python3 -m conformance.extract <rom> <shapes out> [table]` | 从你拥有的卡带中写出头部字节和长度的普查。`table` 是由偏移量和长度对组成的 JSON 列表，或者是带有 `SDD1` 标记的构建 | 0 已写出，1 未找到流，2 参数错误或没有 ROM |
| `python3 -m conformance.against_cartridges <cartridge> <expanded> <out.json> [lo] [hi]` | 在 `lo` 和 `hi` 之间扫描卡带，统计前 64 个解码字节出现在扩展镜像中、且不出现在卡带任何位置的流 | 0 已写出，1 没有得到确认的流，2 参数错误或缺少文件 |
| `python3 -m conformance.speed` | 将 2,000 字节解码 5 次，并把速率中位数与每秒 70,000 字节的下限比较 | 0 高于下限，1 低于下限 |
| `python3 -m conformance.package <wheel>` | 检查构建出的 wheel 包含每个模块且不含测试文件 | 0 正常，1 有问题或没有 wheel，2 没有参数 |
| `python3 -m conformance.links` | 请求本文件中的每个地址并输出 JSON 报告 | 0 每个地址仍然存在，1 至少一个返回状态 404 或 410 |

```bash
python3 -m conformance.vectors conformance/vectors.json
```

```
  4000 cases from conformance/vectors.json, against snes9x 1.63
  4000 agreed, 0 did not
```

## 用噪声而不是美术素材

从卡带中取出的流就是游戏的图形，只是经过了压缩。把这样的流作为测试数据随仓库发布，就等于分发游戏，所以本解码器的证据是用不含任何卡带内容的流构建的。

解码器并不知道它的输入是否真的被压缩过。它对收到的任何字节运行状态机，并产生一个确定的结果。[`conformance/vectors.json`](conformance/vectors.json) 包含由种子 1996 生成的 16,384 个伪随机字节及其 SHA-256，以及在这些字节内部不同偏移量和长度上的 4,000 个用例。每个用例都带有 snes9x 1.63 在该处解码结果的 SHA-256。这些用例覆盖全部 16 种头部形态和 13 种输出长度，从 1 字节到 2,048 字节。

美术素材只会沿着某一张图片所走的路径驱动概率模型，因此一组真实的流可能处处一致，而状态表的一部分却从未运行过。一款游戏只用到美术人员需要的形态；噪声集覆盖全部 16 种。

## 解码器的工作原理

32 个上下文中的每一个都保存一个游程长度，而不是一个概率。解码器读取一个码字时，得知可能性较大的符号重复多少次，就把它输出那么多次，然后才再次读取。`EVOLUTION` 规定每个状态读取的码长，以及每种结果之后上下文转移到哪里。

每一位都属于一个位平面，每个平面维护自己的 10 位历史。这段历史经过头部所选的 `CONTEXT_MASKS` 那一行掩码后，选出上下文。同一个输入字节的解码结果，取决于它在该平面中之前出现过什么。

| 平面类型，头部第 7 位和第 6 位 | 交织的平面数 | 平面如何轮换 |
|:--|:--|:--|
| `0` | 2 | 不轮换 |
| `1` | 4 | 每 16 个输出字节，平面对前移 2，到 8 回绕 |
| `2` | 4 | 每 16 个输出字节，平面对在平面 0 和 1 与平面 2 和 3 之间切换 |
| `3` | 8 | 每个输出字节从 8 个平面中各取一位 |

类型 1 和类型 2 在第二次轮换之前，即 32 字节之前，结果一致：

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

## 型号

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

只有一个型号。搭载这颗芯片的两款游戏使用同一个解压器。它们的卡带在把存储体映射到地址空间的方式上有所不同，这属于卡带而不属于解压器，本仓库没有对这种映射建模。

## 它是否正确

没有人公开过这颗芯片的数据手册，所以权威阶梯的最高一级是空的。[`conformance/hardware.json`](conformance/hardware.json) 记录了这一点，把每个常量标记为 `"verified": false`，并写明替代它的证据以及能确定每一项的依据。

| 见证 | 记录 | 结果 |
|:--|:--|:--|
| snes9x 1.63 处理噪声 | [`conformance/vectors.json`](conformance/vectors.json) | 4,000 个用例，0 失败 |
| snes9x 1.63 处理卡带形态 | [`conformance/corpus.json`](conformance/corpus.json) | 2,652 个用例，0 失败 |
| 零售版卡带对照他人制作的扩展版，不使用模拟器 | [`conformance/cartridges.json`](conformance/cartridges.json) | 在 Star Ocean（日本版）中确认了 55,023 个流，覆盖全部 16 种形态；在另一款游戏上的对照运行为 1,306 个 |
| 第三方的编码器 | [`conformance/independent.json`](conformance/independent.json) | 20 对：18 对完全相同，2 对在作者导出所含的每个字节上一致、但少了 64 字节，0 对不同 |
| 压缩之前的一个 Capcom 原型 | [`conformance/prototype.json`](conformance/prototype.json) | 2,852 个解码流中有 242 个原样出现在其中，共 311,264 字节 |
| 源码中的表 | [`conformance/carried.json`](conformance/carried.json) | `EVOLUTION`、`RUN_TABLE` 和 `CONTEXT_MASKS` 由其值的 SHA-256 固定 |

测试套件还检查：`RUN_TABLE` 是一个排列，`EVOLUTION` 中的每条链在两种结果下都会收敛，没有哪对掩码重复选择同一位，以及在同一偏移量上较短的读取是较长读取的前缀。

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

### 卡带形态语料库

噪声向量不超过 2,048 字节。[`conformance/corpus.json`](conformance/corpus.json) 覆盖一个完整的 65,536 字节块。它的 2,652 个用例使用 68 个不同的头部字节和 39 种长度，放在由种子 20260818 生成的 131,072 字节数据体中，预期输出来自 snes9x 1.63 的 `sdd1emu.cpp`。头部字节和长度是芯片的接口，也是一项测量结果。文件中不含任何来自卡带的压缩字节。

这些形态来自对 11,306 个流的普查，涉及 16 种类型中的 14 种。文件没有记录这次普查的来源，也无法从四盒零售版卡带中复现它。[`conformance/divergences.json`](conformance/divergences.json) 记载了这一发现及其背后的测量。普查决定语料库测试哪些形态，而不决定解码器如何处理其中任何一种，并且噪声集覆盖全部 16 种形态。

```bash
python3 -m conformance.corpus conformance/corpus.json
```

```
  2652 cases from conformance/corpus.json, against snes9x 1.63 sdd1emu.cpp
  shapes measured from 11306 real streams, 14 of 16 kinds
  2652 agreed, 0 did not
```

### 测量你自己的卡带

```bash
python3 -m conformance.extract cartridge.sfc shapes.json table.json
python3 -m conformance.against_cartridges cartridge.sfc expanded.sfc found.json
```

`extract` 写出头部字节、长度和计数，从不写出压缩字节。`against_cartridges` 写出计数、头部字节以及每个镜像的四个摘要。两者的输出都可以分享；镜像留在你自己的机器上。

### 尚未解决的问题

[OPEN-QUESTIONS.md](OPEN-QUESTIONS.md) 列出每个未解决的问题，以及能解决它的测量。每个输出值都依据现有实现，而不是来自真实芯片的录制。遇到格式错误的流时的行为是推测。第二个头部字节除形态之外的含义未知。[`conformance/divergences.json`](conformance/divergences.json) 记录了每一处来源比表面看起来更薄弱的地方。

## 参与开发

| 需要 | 位置 |
|:--|:--|
| 每一项门禁检查及其运行顺序 | [CONTRIBUTING.md](CONTRIBUTING.md) |
| 供编码代理使用的同一份材料 | [AGENTS.md](AGENTS.md) |
| 本仓库与同系列其他仓库共享的标准 | [FAMILY.md](FAMILY.md) |
| Bug 报告 | [GitHub Issues](https://github.com/gufranco/snes-sdd1-python/issues) |
| 安全报告 | [SECURITY.md](SECURITY.md) |

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

每个模块旁边都有一个以它命名的测试文件，每个测试文件都能单独运行。覆盖率是硬性门禁检查，要求 100% 语句和分支覆盖率。吞吐量下限在覆盖率步骤之外运行。

切勿在 issue 中附加卡带镜像或链接到卡带镜像。摘要可以标识一个文件而不携带它。

## 参考资料

- snes9x 1.63，`sdd1emu.cpp`，https://github.com/snes9xgit/snes9x ，它是生成 [`conformance/vectors.json`](conformance/vectors.json) 和 [`conformance/corpus.json`](conformance/corpus.json) 中每个预期输出的解码器。只取事实，不取任何代码。
- 目前没有已知的 Ricoh 或 Nintendo 关于 S-DD1 的文档。[`conformance/hardware.json`](conformance/hardware.json) 记录了检索过程，并把 `documents` 列为空。
- 记录中提到的每个卡带、扩展版和原型镜像都在那里以大小和四个摘要标识。本仓库不携带其中任何一个。

## 引用本项目

[CITATION.cff](CITATION.cff) 会在每次发布时由写入包版本号的脚本更新。

## 许可证

MIT。参见 [LICENSE](LICENSE)。
