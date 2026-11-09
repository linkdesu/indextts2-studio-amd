# 第三方许可与署名声明

本文件列出本仓库涉及的全部第三方内容的许可与署名要求。条目以 `vendor/lfwb` 内的实际文件为准；各条目的依据文件均标注于表内，逐字出处见对应文件。

## 总览

| # | 条目 | 是否随本仓库分发 | 许可 | 署名要求 | 依据文件 |
|---|------|------------------|------|----------|----------|
| 1 | 长篇工作台代码（`vendor/lfwb`，含 `docs/`、`packaging/`） | 是（subtree 快照） | MIT | 保留版权行与许可全文 | `vendor/lfwb/LICENSE` |
| 2 | KEMAR HRIR 数据（`vendor/lfwb/assets/hrir/MIT_KEMAR_normal_pinna.sofa`） | 是 | 无使用限制（文件内 `License` 属性声明） | 要求引用 Gardner & Martin (1995) | `vendor/lfwb/assets/hrir/README.md`、`CREDITS.md`、文件内 `License` 属性 |
| 3 | KU100 近场 HRIR 数据（`vendor/lfwb/assets/hrir/KU100_near.npz`、`KU100_near_circ.npz`） | 是 | CC BY-SA 3.0（以下载包内 `License` 属性为准） | 署名 + 相同方式共享；修改/再分发 IR 文件须同协议共享 | `vendor/lfwb/assets/hrir/README.md`、`CREDITS.md` |
| 4 | Demucs 预训练权重（`htdemucs`） | **否**（仓库内无权重；`vendor2/` 不存在） | 代码 MIT；权重许可以官方仓库说明为准 | 按官方说明 | `vendor/lfwb/CREDITS.md` §3、`vendor/lfwb/LICENSE` 第 10 行 |
| 5 | FFmpeg | **否**（仓库内无二进制，仅下载脚本 `tools/fetch_ffmpeg.ps1`） | LGPL/GPL（取决于编译选项） | 分发二进制时须附带其许可文本与源码获取方式 | `vendor/lfwb/CREDITS.md` §5、`vendor/lfwb/LICENSE` 第 13 行 |
| 6 | IndexTTS2 模型与推理代码 | **否**（不在本仓库 vendor 范围内） | 以原项目仓库 LICENSE 为准 | 按原项目要求 | `vendor/lfwb/CREDITS.md` §2、`vendor/lfwb/LICENSE` 第 8 行 |
| 7 | 「IndexTTS2.0 超级优化整合包 V3」 | **否**（不在本仓库 vendor 范围内） | 版权归 B 站 UP 主「十一君Jun」；未见开源许可 | 按作者发布页要求；本仓库不转存、不二次分发 | `vendor/lfwb/CREDITS.md` §1、`vendor/lfwb/LICENSE` 第 9 行 |

## 1. `vendor/lfwb` 代码（MIT）

- 版权行（逐字，`vendor/lfwb/LICENSE` 第 3 行）：

  > Copyright (c) 2026 全能音声工作台 contributors

- Pin 版本：**v0.33**，上游提交 **4743f18166f45468ed6bdf8cf59fe83b09a7fbf8**（`main` 分支，`git subtree add --squash` 引入；pin 记录见 `vendor/LFWB_UPSTREAM.md`）。
- 许可范围：上游 `LICENSE` 自述其「仅覆盖本仓库中由本项目作者编写的源代码（Python / JavaScript / HTML / CSS / 安装脚本 / 文档）」，并明确排除本文件第 2–7 条目所列内容。据此，`vendor/lfwb` 顶层的源码与文档——`hrir.py`、`lf_import.py`、`lf_roles.py`、`lf_static.py`、`longform_api.py`、`timeline_api.py`、`rooms.py`、`web/`、**`docs/`（工作台文档）**、**`packaging/`（`install.py`、`安装.bat`、`说明.md`）**、`tools/`、`README.md`、`CHANGELOG.md`、`CREDITS.md`——均在 MIT 覆盖范围内（排除项除外）。
- 再分发本仓库（含 `vendor/lfwb` 的副本）时，须保留上述版权行与 MIT 许可全文（`LICENSE` 第 23–24 行要求）。

## 2. KEMAR HRIR 数据

- 文件：`vendor/lfwb/assets/hrir/MIT_KEMAR_normal_pinna.sofa`（MIT Media Lab，Gardner & Martin, 1995，经 SOFA 数据库分发）。
- 文件内 `License` 属性原文（经 `README.md` 摘录，与文件内文本一致）：

  > This HRTF data is provided without any usage restrictions. It is requested that you cite Gardner and Martin (1995) when using this data for research or commercial applications.

- 即：**无使用限制**（学术与商业均可），仅要求引用 Gardner & Martin (1995)。
- 建议署名（`README.md` / `CREDITS.md` 给出的措辞）：

  > HRTF data: MIT KEMAR (Gardner & Martin, 1995), via the SOFA database.

## 3. KU100 近场 HRIR 数据（CC BY-SA 3.0）

- 文件：`vendor/lfwb/assets/hrir/KU100_near.npz`、`KU100_near_circ.npz`（本项目用 `hrir.pack()` 对 TH Köln「Spherical Near-Field HRIR Compilation of the Neumann KU100」合并重采样而来）。
- 版本口径：原始下载包内 `License` 属性为 **CC BY-SA 3.0**。上游 `assets/hrir/README.md` 明确说明「早前文档里写的 4.0 是论文口径，以下载包里的为准」（该 README 后文一处仍写 4.0，属遗留笔误，以该「为准」条款与 `CREDITS.md`、`docs/技术路线_长篇台本与时间轴.md` 的 3.0 口径为准）。
- 义务（`CREDITS.md` §4）：
  - 仅随软件使用（不修改）→ **署名**即可；
  - **修改 / 再分发这些 IR 文件本身** → 须按 **CC BY-SA** 以相同协议共享；
  - 商用前建议先过法务。若不处理上述约束，删除这两个 `.npz` 即可，空间音频自动回退到 KEMAR 或内置球头模型。
- 这两份数据**不属于**本仓库的 MIT 许可范围（`LICENSE` 第 11–12 行明确排除）。
- 建议署名（`CREDITS.md` 给出的措辞）：

  > Near-field HRIR: Neumann KU100 spherical near-field HRIR compilation, TH Köln (CC BY-SA).

## 4. Demucs 预训练权重（不在仓库中）

- 用途：素材导入的「去伴奏 / 只留人声」（可选功能）。
- 仓库现状：`vendor2/` 在本仓库不存在，仓库内无任何 Demucs 权重文件（`.pth`/`.pt`/`.onnx`/`.safetensors` 等均不在 `vendor/lfwb` 内）。权重仅在可选路径出现：从源码安装时首次运行自动下载，或自行放置到 `vendor2/torch/hub/checkpoints/`（`CREDITS.md` §3）。
- 许可：Demucs 代码为 MIT；**预训练权重许可以 Meta AI Research 官方仓库说明为准**（不同版本可能不同）。
- 署名/义务：按官方权重许可执行；本仓库不分发权重，不产生额外义务。

## 5. FFmpeg（不在仓库中）

- 用途：视频抽音频（可选功能）。
- 仓库现状：不含任何 FFmpeg 二进制；运行时探测系统 `PATH` 中的 FFmpeg、用户放入 `bin\` 的可执行文件，或在导入台里手动指定路径（`CREDITS.md` §5）。仓库内的 `vendor/lfwb/tools/fetch_ffmpeg.ps1` 只是下载脚本，不含二进制。
- 许可：FFmpeg 主体为 **LGPL/GPL**（取决于编译选项）。
- 义务：若你随产品分发 FFmpeg 二进制，须一并提供其许可文本与源码获取方式（`CREDITS.md` §5）；仅依赖用户自备的二进制则义务在用户侧。

## 6. IndexTTS2 模型与推理代码（不在 vendor 范围内）

- 版权归哔哩哔哩（Bilibili）/ 原项目作者（`LICENSE` 第 8 行）；许可**以原项目仓库 LICENSE 为准**。
- 本仓库（`vendor/lfwb` 与适配层）不修改、不重分发其代码与权重（`CREDITS.md` §2）。若原项目限制商用，基于本工作台的工作成果同样不得用于商用场景。

## 7. 「IndexTTS2.0 超级优化整合包 V3」（不在 vendor 范围内）

- 版权归 B 站 UP 主「十一君Jun」（`LICENSE` 第 9 行）。整合包提供 Python 运行时、IndexTTS2 模型、推理接口等；本仓库不包含整合包本体、模型权重、运行时环境，不转存、不二次分发（`CREDITS.md` §1）。
- 下载渠道与条款以作者发布页为准（`CREDITS.md` §1 仅收录作者公开的网盘链接做指路）。

## 附注

- 前端不内嵌任何商业字体或图标库，仅使用系统字体与 emoji（`CREDITS.md` §6）。
- 解析 `.sofa`（HDF5 格式）所需的 `h5py` 为 Python 依赖，随 `requirements.txt` 安装（BSD 类许可，见其官方仓库），不以二进制形式随本仓库 vendor 分发。
- 本文件不修改 `vendor/lfwb` 内任何文件；上游文件为只读快照（约定见 `vendor/LFWB_UPSTREAM.md`）。
