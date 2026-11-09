#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# 票 #7：长篇工作台（vendor/lfwb，git subtree）的可重复、可审计上游同步。
#
# 用法:
#   scripts/amd7900/lfwb_sync.sh --check    只报告：当前 pin / 上游 head / 是否落后，不动工作区
#   scripts/amd7900/lfwb_sync.sh            同步：subtree pull --squash + 契约检查 + 更新 pin 并提交
#
# 退出码:
#   0  --check 完成（无论是否落后），或同步成功
#   1  参数/环境/文档错误，或 vendor/lfwb 工作区不干净
#   2  fetch 失败，或同步后契约检查未通过（脚本会打印回滚命令）
#
# 约定见 vendor/LFWB_UPSTREAM.md 与 patches/README.md：
# vendor/lfwb 禁止手改；临时补丁走 patches/，同步后重放。
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

PREFIX="vendor/lfwb"
UPSTREAM_URL="https://github.com/Mars-1438/indextts2-longform-workbench"
UPSTREAM_BRANCH="main"
PIN_DOC="vendor/LFWB_UPSTREAM.md"
CONTRACT_CHECK="scripts/amd7900/check_lf_contract.py"
PY="${INDEXTTS_VENV:-$REPO_ROOT/.venv314}/bin/python"

die() { echo "[错误] $1" >&2; exit "${2:-1}"; }
info() { echo "[信息] $*"; }

[ -d "$REPO_ROOT/.git" ] || die "不在 git 仓库根: $REPO_ROOT"
[ -f "$PIN_DOC" ] || die "缺少 $PIN_DOC，无法确定当前 pin"
git rev-parse --git-dir >/dev/null 2>&1 || die "git 不可用"

read_pin() {
  # 从 LFWB_UPSTREAM.md 的「Pin 的提交: <sha>」行提取完整 sha
  sed -n 's/^- *Pin 的提交:[[:space:]]*\([0-9a-f]\{7,40\}\).*/\1/p' "$PIN_DOC" | head -1
}

get_version() {
  # 版本号提取：README 的「当前版本 vX.Y」是正式发布口径，优先；
  # 退化到 CHANGELOG 首个 vX.Y 标题（可能标着「开发中」）；都没有则 unknown。
  local v=""
  [ -f "$PREFIX/README.md" ] && v="$(sed -n 's/.*当前版本[[:space:]]*\(v[0-9][0-9.]*\).*/\1/p' "$PREFIX/README.md" 2>/dev/null | head -1)" || true
  if [ -z "$v" ] && [ -f "$PREFIX/CHANGELOG.md" ]; then
    v="$(sed -n 's/^##[[:space:]]\+\(v[0-9][0-9.]*\).*/\1/p' "$PREFIX/CHANGELOG.md" 2>/dev/null | head -1)" || true
  fi
  echo "${v:-unknown}"
}

update_pin_doc() {
  # 更新 LFWB_UPSTREAM.md：pin 提交 + 版本 + 最近同步日期（幂等）
  local sha="$1" ver="$2" date="$3"
  "$PY" - "$PIN_DOC" "$sha" "$ver" "$date" <<'PYEOF'
import re, sys
path, sha, ver, date = sys.argv[1:5]
text = open(path, encoding="utf-8").read()
text, n = re.subn(r"(?m)^(- *Pin 的提交:).*$",
                  lambda m: f"{m.group(1)} {sha} ({ver})", text, count=1)
assert n == 1, "LFWB_UPSTREAM.md 里找不到「Pin 的提交:」行，请手动更新"
if re.search(r"(?m)^-? *最近同步:", text):
    text = re.sub(r"(?m)^(-? *最近同步:).*$",
                  lambda m: f"{m.group(1)} {date}", text, count=1)
else:
    text = re.sub(r"(?m)^(- *Pin 的提交:.*)$",
                  rf"\1\n- 最近同步: {date}（由 scripts/amd7900/lfwb_sync.sh 写入）",
                  text, count=1)
open(path, "w", encoding="utf-8").write(text)
PYEOF
}

MODE="sync"
case "${1:-}" in
  --check) MODE="check" ;;
  "") ;;
  -h|--help) sed -n '2,15p' "${BASH_SOURCE[0]}"; exit 0 ;;
  *) die "未知参数: $1（支持 --check / --help）" ;;
esac

PIN="$(read_pin || true)"
[ -n "$PIN" ] || die "无法从 $PIN_DOC 解析 pin（找「Pin 的提交: <sha>」行）"

info "fetch 上游 $UPSTREAM_URL ($UPSTREAM_BRANCH) …"
git fetch --no-tags "$UPSTREAM_URL" "$UPSTREAM_BRANCH" \
  || die "fetch 上游失败（网络/权限？）" 2
HEAD_SHA="$(git rev-parse FETCH_HEAD)"
HEAD_SHORT="${HEAD_SHA:0:7}"
SHORT_PIN="${PIN:0:7}"

BEHIND="?"
if git cat-file -e "${PIN}^{commit}" 2>/dev/null; then
  BEHIND="$(git rev-list --count "${PIN}..${HEAD_SHA}" 2>/dev/null || echo '?')"
fi

if [ "$MODE" = "check" ]; then
  echo "当前 pin : $PIN ($SHORT_PIN)"
  echo "上游 head: $HEAD_SHA ($HEAD_SHORT)"
  if [ "$PIN" = "$HEAD_SHA" ]; then
    echo "状态     : 已是最新（pin == 上游 head）"
  elif [ "$BEHIND" != "?" ]; then
    echo "状态     : 落后上游 $BEHIND 个提交，可运行 scripts/amd7900/lfwb_sync.sh 同步"
  else
    echo "状态     : 落后上游（pin 不在本地对象库，无法精确计数）"
  fi
  exit 0
fi

# ---- 同步模式 ---------------------------------------------------------------

# -uno：只看已跟踪文件的改动；untracked 运行垃圾（缓存等）由 vendor 自带 .gitignore
# 兜底，不阻塞同步，但会随 pull 留在目录里，建议自行清理。
DIRTY="$(git status --porcelain -uno -- "$PREFIX")"
if [ -n "$DIRTY" ]; then
  echo "[错误] $PREFIX 工作区不干净，拒绝同步。改动清单:" >&2
  printf '%s\n' "$DIRTY" >&2
  cat >&2 <<EOF
怎么处理（三选一）:
  1) 临时手改要保留 → 转成补丁（见 patches/README.md）:
       git diff -- $PREFIX > patches/NNNN-简短描述.patch
       git checkout -- $PREFIX
  2) 改动不要了 → git checkout -- $PREFIX
  3) 是运行垃圾（__pycache__ 等） → 删除，或按 vendor/lfwb/.gitignore 处理
处理完重新运行本脚本。
EOF
  exit 1
fi

if [ "$PIN" = "$HEAD_SHA" ]; then
  echo "已是最新，pin=$PIN（未产生提交）"
  exit 0
fi

# subtree pull 要求整棵工作树干净；任何未提交的已跟踪改动都先挡住，给出明确指引
TREE_DIRTY="$(git status --porcelain -uno)"
if [ -n "$TREE_DIRTY" ]; then
  echo "[错误] 工作树有未提交的已跟踪改动，git subtree 会拒绝执行。清单:" >&2
  printf '%s\n' "$TREE_DIRTY" >&2
  echo "先提交或还原这些改动（vendor/lfwb 内的按上面补丁流程处理），再重跑。" >&2
  exit 1
fi

PRE_SYNC_HEAD="$(git rev-parse HEAD)"
echo "[信息] 同步前 HEAD=$PRE_SYNC_HEAD（回滚锚点，请记下）"
echo "[信息] pin ${SHORT_PIN} → ${HEAD_SHORT}，执行 subtree pull --squash …"
git subtree pull --prefix "$PREFIX" "$UPSTREAM_URL" "$UPSTREAM_BRANCH" --squash \
  || die "subtree pull 失败。工作区可能停在中间状态，回滚: git reset --hard $PRE_SYNC_HEAD" 2

VER="$(get_version)"
DATE="$(date +%F)"
update_pin_doc "$HEAD_SHA" "$VER" "$DATE"
info "pin 已更新: $HEAD_SHA ($VER)，同步日期 $DATE"

if [ ! -x "$PY" ] && [ ! -f "$PY" ]; then
  die "找不到 $PY（可用 INDEXTTS_VENV 指定 venv）。pin 文档已更新，请手动跑契约检查: $CONTRACT_CHECK" 2
fi

info "跑契约检查: $CONTRACT_CHECK"
if ! "$PY" "$CONTRACT_CHECK"; then
  cat >&2 <<EOF
[失败] 同步后契约检查未通过（原因见上方 [失败] 行）。
上游改动与宿主引擎的契约不匹配，不要带着坏状态继续开发。回滚:
  git reset --hard $PRE_SYNC_HEAD
EOF
  exit 2
fi

git add "$PIN_DOC"
git commit -m "chore(vendor): 同步长篇工作台到 ${HEAD_SHORT}（${VER}）" \
  -m "上游: ${UPSTREAM_URL} ${UPSTREAM_BRANCH}
pin: ${PIN} → ${HEAD_SHA}
同步日期: ${DATE}（scripts/amd7900/lfwb_sync.sh，契约检查已通过）" \
  || die "git commit 失败（index.lock？等 1-2 秒重试）"

echo "[完成] 同步成功: ${SHORT_PIN} → ${HEAD_SHORT}（${VER}）"
echo "如本地有补丁，现在重放: git -C $REPO_ROOT apply patches/NNNN-*.patch（逐个，冲突见 patches/README.md）"
