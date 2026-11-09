# vendor/lfwb — 上游固定快照

- 上游仓库: https://github.com/Mars-1438/indextts2-longform-workbench
- 分支: main
- Pin 的提交: 4743f18166f45468ed6bdf8cf59fe83b09a7fbf8 (v0.33)
- 引入方式: git subtree，`git subtree add --prefix vendor/lfwb <url> main --squash`

## 同步方式

统一用脚本同步，不要手敲 subtree 命令:

```bash
scripts/amd7900/lfwb_sync.sh --check   # 只报告:当前 pin / 上游 head / 是否落后
scripts/amd7900/lfwb_sync.sh          # 同步 + 契约检查 + 更新本文件 pin 并提交
```

脚本行为:脏工作区拒绝;pin 已最新则不产生提交;同步后跑
`scripts/amd7900/check_lf_contract.py`,失败打印 `git reset --hard` 回滚命令并退出非 0。
底层就是 `git subtree pull --prefix vendor/lfwb <url> main --squash`。

## 约定

**禁止直接编辑 vendor/lfwb 内的任何文件。** 本目录是上游快照，就地修改会在
下次 subtree pull 时冲突，且无法判定问题归属。需要的适配一律写在根目录的
适配层 `lf_integration.py` 里；属于上游的缺陷请向上游仓库反馈。

确需临时手改 vendor 内文件时，转成补丁放 `patches/`（流程见 `patches/README.md`），
原则是**先上游化、再补丁**。
