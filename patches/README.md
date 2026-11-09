# patches/ — vendor/lfwb 临时补丁登记处

`vendor/lfwb` 是上游长篇工作台的 subtree 快照，**禁止直接编辑**（约定见
`vendor/LFWB_UPSTREAM.md`）。调试中确实需要就地手改时，用本目录把改动
固化成补丁，保证同步可重复、问题可归属。

## 原则：先上游化，再补丁

vendor 里的缺陷先向 [上游仓库](https://github.com/Mars-1438/indextts2-longform-workbench)
提 issue / PR；上游修了就走正常同步。**补丁是等不起上游时的临时桥**，
不是长期方案：每多一个补丁，下次同步的冲突面和归属模糊就多一份。
适配宿主引擎的逻辑一律写在根目录 `lf_integration.py`，不算补丁。

## 生成补丁（临时手改之后）

```bash
# 1) 在 vendor/lfwb 里手改（只为复现/绕过，改完立刻转补丁）
# 2) 编号取本目录现有最大号 +1，四位数
git diff -- vendor/lfwb > patches/0001-简短描述.patch
# 3) 恢复快照，保持 vendor 干净（同步脚本会拒绝脏工作区）
git checkout -- vendor/lfwb
```

补丁文件名 `NNNN-描述.patch`：`NNNN` 四位递增；描述里带上游 issue 号（如有），
例如 `0002-issues-12-timeline-crash.patch`。

## 同步后重放

`scripts/amd7900/lfwb_sync.sh` 同步完成后，逐个重放：

```bash
for p in patches/*.patch; do
  git apply --check "$p" && git apply "$p" && echo "OK  $p" || echo "CONFLICT  $p"
done
```

- `git apply --check` 通过 → `git apply`，随后按需 `git add vendor/lfwb` 提交，
  commit 信息注明补丁号与原因。
- **补丁不再适用（apply 冲突）→ 先怀疑上游已修复**：看上游 CHANGELOG、
  对照 issue 状态；已修复就删掉补丁，未修复就带着「补丁失效」的信息去上游
  催 issue / 提 PR。只有在「上游明确拒修 且 影响本机可用」时才重写补丁
  使其适配新代码，并在补丁头注释里写明理由与失效风险。
- 重放后必须跑 `scripts/amd7900/check_lf_contract.py`，rc=0 才算同步完成。

## 登记要求

每个补丁在本目录留下 `.patch` 文件本身即可（git 跟踪），补丁头注释建议包含：
症状一句话、对应上游 issue/PR 号（或「待提」）、生成日期、失效条件。
上游修复合入同步后，删除对应补丁文件并提交删除。
