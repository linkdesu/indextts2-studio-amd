#!/usr/bin/env bash
# 前台启动 IndexTTS2 Studio（AMD RDNA3 / ROCm 7.2）
#
# 用法:
#   scripts/amd7900/run.sh                # 0.0.0.0:7860，浏览器开 http://<本机IP>:7860
#   scripts/amd7900/run.sh --port 7861
#   INDEXTTS_HOST=127.0.0.1 scripts/amd7900/run.sh   # 只本机可访问
#
# 这个分支所有 AMD 相关差异都集中在这里，理由：
#   HIP_VISIBLE_DEVICES=0  → bus03 的 7900XTX（无显示器）；核显 gfx1103 不暴露
#   MIOPEN_FIND_MODE=FAST  → 不设的话 MIOpen 对每个新音频长度现场调优，
#                            BigVGAN 单次 25~45s（实测 25.9s → 0.56s）
#   USE_MODELSCOPE=false   → 直连 HuggingFace（本机 15MB/s），不走 ModelScope 分支
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV="${INDEXTTS_VENV:-$ROOT/.venv314}"

if [ ! -x "$VENV/bin/python" ]; then
  echo "找不到 $VENV，先跑 scripts/amd7900/setup.sh" >&2
  exit 1
fi

cd "$ROOT"
exec env \
  HIP_VISIBLE_DEVICES="${HIP_VISIBLE_DEVICES:-0}" \
  MIOPEN_FIND_MODE="${MIOPEN_FIND_MODE:-FAST}" \
  USE_MODELSCOPE="${USE_MODELSCOPE:-false}" \
  "$VENV/bin/python" "$ROOT/server.py" \
  --host "${INDEXTTS_HOST:-0.0.0.0}" "$@"
