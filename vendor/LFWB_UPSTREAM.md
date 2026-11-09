# vendor/lfwb — 上游固定快照

- 上游仓库: https://github.com/Mars-1438/indextts2-longform-workbench
- 分支: main
- Pin 的提交: 4743f18166f45468ed6bdf8cf59fe83b09a7fbf8 (v0.33)
- 引入方式: git subtree，`git subtree add --prefix vendor/lfwb <url> main --squash`

## 同步方式

升级用 `git subtree pull --prefix vendor/lfwb <url> main --squash`；
同步后更新本文件的 pin 提交与版本号。

## 约定

**禁止直接编辑 vendor/lfwb 内的任何文件。** 本目录是上游快照，就地修改会在
下次 subtree pull 时冲突，且无法判定问题归属。需要的适配一律写在根目录的
适配层 `lf_integration.py` 里；属于上游的缺陷请向上游仓库反馈。
