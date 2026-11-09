"""torchaudio load/save 的 soundfile 垫片（torchaudio >= 2.9 / Python 3.14 专用）。

torchaudio 2.9 起把 load/save 全部委托给 TorchCodec，未安装 torchcodec 时报
`ImportError: TorchCodec is required for load_with_torchcodec`。本项目用
torchaudio.load 读参考音频（indextts/utils/common.py、utils.py）、用 torchaudio.save
出片（indextts/infer_v2.py），所以这里把两个入口换回 soundfile，不依赖 FFmpeg 共享库。

安装方式由 setup.sh 完成：本文件被复制进 venv 的 site-packages，并写一个同名 .pth
（内容 `import zz_torchaudio_sf_shim`）让解释器启动时自动打补丁。不改仓库里的业务代码。
"""
import numpy as np
import soundfile as sf
import torch
import torchaudio


def _load(filepath, frame_offset=0, num_frames=-1, normalize=True,
          channels_first=True, **kwargs):
    frames = -1 if num_frames is None or num_frames < 0 else int(num_frames)
    data, sr = sf.read(str(filepath), dtype="float32", always_2d=True,
                       start=int(frame_offset or 0), frames=frames)
    wav = torch.from_numpy(np.ascontiguousarray(data.T))
    if not channels_first:
        wav = wav.transpose(0, 1)
    return wav, sr


def _save(filepath, src, sample_rate, precision=16, channels_first=True, **kwargs):
    if isinstance(src, torch.Tensor):
        arr = src.detach().cpu()
        if not channels_first:
            arr = arr.transpose(0, 1)
        arr = arr.numpy()
    else:
        arr = np.asarray(src)
        if arr.ndim == 1:
            arr = arr[None, :]
    # 项目里传的是 int16 张量（infer_v2 出片处），直接按 PCM_16 写
    if arr.dtype == np.int16:
        sf.write(str(filepath), arr.T, int(sample_rate), subtype="PCM_16")
    else:
        subtype = {16: "PCM_16", 24: "PCM_24", 32: "FLOAT"}.get(int(precision), "PCM_16")
        sf.write(str(filepath), arr.T.astype("float32"), int(sample_rate), subtype=subtype)


def _info(filepath, **kwargs):
    i = sf.info(str(filepath))
    return torchaudio.backend.common.AudioMetaData(
        sample_rate=i.samplerate, num_frames=i.frames,
        num_channels=i.channels, bits_per_sample=16, encoding="PCM_S",
    )


def patch():
    torchaudio.load = _load
    torchaudio.save = _save
    try:
        torchaudio.info = _info
    except Exception:
        pass


# 2.9 之后才需要；2.8 及更早自带 soundfile/ffmpeg 后端，不用管
if torchaudio.__version__.startswith(("2.9", "2.1", "2.2")):
    patch()
