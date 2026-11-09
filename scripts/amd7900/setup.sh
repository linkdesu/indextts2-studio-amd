#!/usr/bin/env bash
# 为 AMD RDNA3 (gfx1100) 建运行时：Python 3.14 + torch 2.14.1+rocm7.2
#
# 用法:
#   scripts/amd7900/setup.sh                 # 建/更新 venv（默认 .venv314）
#   INDEXTTS_VENV=.venv2 scripts/amd7900/setup.sh
#   TORCH_WHEEL_DIR=~/comfyui/_wheels scripts/amd7900/setup.sh   # 指定本地 wheel 目录
#
# torch 优先用本地已缓存的 cp314 wheel（ComfyUI 那套），没有才去 ROCm 索引下载；
# 无论哪条路都不会碰系统 ROCm / 驱动。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV="${INDEXTTS_VENV:-$ROOT/.venv314}"
WHEELS="${TORCH_WHEEL_DIR:-$HOME/comfyui/_wheels}"
TORCH_VER="2.14.1+rocm7.2"
TA_VER="2.11.0+rocm7.2"
TRITON_VER="3.8.0"
IDX="https://download.pytorch.org/whl/rocm7.2"
PY_TAG="cp314-cp314-manylinux_2_28_x86_64"

log() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }

# ---- 1. 解释器 ----
PYBIN=""
for c in /usr/bin/python3.14 python3.14; do
  if command -v "$c" >/dev/null 2>&1; then PYBIN="$(command -v "$c")"; break; fi
done
if [ -z "$PYBIN" ]; then
  log "系统里没有 python3.14（Ubuntu 26.04 自带 /usr/bin/python3.14）"
  exit 1
fi
log "解释器: $PYBIN ($($PYBIN -V 2>&1))"

# ---- 2. venv ----
if [ ! -x "$VENV/bin/python" ]; then
  if command -v uv >/dev/null 2>&1; then
    log "创建 venv: $VENV"
    uv venv --python "$PYBIN" "$VENV"
  else
    log "创建 venv: $VENV（无 uv，用 python -m venv）"
    "$PYBIN" -m venv "$VENV"
  fi
fi
VPY="$VENV/bin/python"

# 装包器：优先 uv（uv 建的 venv 不带 pip），其次 venv 自带 pip
UV=""
for c in "$(command -v uv 2>/dev/null || true)" "$HOME/.local/bin/uv" \
         "$HOME/.local/venvs/uv/bin/uv" /usr/local/bin/uv; do
  if [ -n "$c" ] && [ -x "$c" ]; then UV="$c"; break; fi
done
if [ -n "$UV" ]; then
  run_pip() { "$UV" pip install --python "$VPY" "$@"; }
else
  if ! "$VPY" -m pip --version >/dev/null 2>&1; then
    log "没有 uv，也没有 pip，尝试 ensurepip"
    "$VPY" -m ensurepip --upgrade >/dev/null 2>&1 || {
      echo "既找不到 uv 也装不上 pip；请先安装 uv：https://docs.astral.sh/uv/" >&2; exit 1; }
  fi
  run_pip() { "$VPY" -m pip install "$@"; }
fi

# ---- 3. torch / torchaudio / triton-rocm ----
install_torch() {
  local w_torch="$WHEELS/torch-$TORCH_VER-$PY_TAG.whl"
  local w_ta="$WHEELS/torchaudio-$TA_VER-$PY_TAG.whl"
  local w_tri="$WHEELS/triton_rocm-$TRITON_VER-cp314-cp314-linux_x86_64.whl"
  if [ -f "$w_torch" ] && [ -f "$w_ta" ] && [ -f "$w_tri" ]; then
    log "使用本地 wheel: $WHEELS"
    run_pip --no-deps "$w_torch" "$w_ta" "$w_tri"
  else
    log "本地缺少 wheel，从 $IDX 安装（约 3.6 GB）"
    run_pip --index-url "$IDX" \
      "torch==$TORCH_VER" "torchaudio==$TA_VER" "triton-rocm==$TRITON_VER"
  fi
}
if "$VPY" -c "import torch" 2>/dev/null; then
  log "torch 已存在: $("$VPY" -c 'import torch;print(torch.__version__)')"
else
  install_torch
fi

# ---- 4. 其余依赖 ----
# h5py 随 requirements.txt 一起装：读 vendor/lfwb 的 .sofa HRIR（可选依赖，
# 装失败不影响启动，hrir.py 会降级回球头近似）
log "安装 requirements.txt"
run_pip -r "$ROOT/requirements.txt"

# ---- 5. torchaudio → soundfile 垫片 ----
SP="$("$VPY" -c 'import sysconfig;print(sysconfig.get_paths()["purelib"])')"
log "安装 torchaudio 垫片 -> $SP"
cp "$ROOT/scripts/amd7900/zz_torchaudio_sf_shim.py" "$SP/zz_torchaudio_sf_shim.py"
printf 'import zz_torchaudio_sf_shim\n' > "$SP/zz_torchaudio_sf_shim.pth"

# ---- 6. 冒烟 ----
log "冒烟检查"
HIP_VISIBLE_DEVICES="${HIP_VISIBLE_DEVICES:-0}" "$VPY" - <<'PY'
import torch, torchaudio
print("torch", torch.__version__, "| hip", torch.version.hip,
      "| torchaudio", torchaudio.__version__)
print("devices", torch.cuda.device_count(), torch.cuda.get_device_name(0))
a = torch.randn(1024, 1024, device="cuda:0", dtype=torch.float16)
torch.cuda.synchronize()
print("fp16 matmul ok:", float((a @ a).abs().mean()))
PY
log "完成。启动：scripts/amd7900/run.sh"
