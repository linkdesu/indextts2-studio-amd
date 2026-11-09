#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""契约检查（票 #5）：工作台（vendor/lfwb）依赖的引擎契约是否仍被本仓库满足。

可重复执行的静态/半静态检查，三项各一条结论，全过退出码 0，任一失败退出码 1
并打印具体不满足的项（例如「infer 不接受 max_mel_tokens」）。

检查项
------
1. 宿主引擎能力：ast 静态解析 server.py，确认 LazyTTS 有
   state / ensure_loaded / normalize_emo_vec / infer 四个方法，模块里有
   _INFER_LOCK 赋值。**绝不 import server.py** —— 它 import 期会清理旧
   outputs、解析 argv，全是副作用。
2. 生成参数契约：longform_api._engine_kwargs(默认参数) 产出的每个键，都必须
   被 IndexTTS2.infer 显式接收（显式形参）或被 infer_generator 从
   **generation_kwargs 里 pop 出来（pop 出来的键）。两边任意一侧改名即破坏
   契约，这里第一时间报出具体键名。
3. 网页与接口：最小 FastAPI app + 假 tts（不加载模型、不推理）跑一遍
   lf_integration.register，断言 /longform /timeline /sfxbench /guide
   /api/v1/lf/manifest 都注册上了。不依赖 TestClient（本机缺 httpx）。

用法
----
    .venv314/bin/python scripts/amd7900/check_lf_contract.py [--selftest]
    .venv314/bin/python scripts/amd7900/check_lf_contract.py --server /tmp/broken.py

--selftest 注入两种坏情况（假引擎缺 normalize_emo_vec；allowed 集合删掉
max_mel_tokens）并断言检查确实报错 —— 自测不过同样退出码 1。

本脚本不写任何文件、不启动服务、不加载模型。
"""

import argparse
import ast
import inspect
import logging
import os
import sys
import tempfile
import textwrap
import threading

# 仓库根：本脚本在 scripts/amd7900/ 下，上跳两级。
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LAZY_METHODS = ("state", "ensure_loaded", "normalize_emo_vec", "infer")
REQUIRED_PATHS = ("/longform", "/timeline", "/sfxbench", "/guide",
                  "/api/v1/lf/manifest")


def _ok(msg):
    print(f"[通过] {msg}", flush=True)


def _fail(msg):
    print(f"[失败] {msg}", flush=True)


# ---- 检查 1：宿主引擎能力（纯 ast，禁止 import server.py） ---------------------

def check_engine_caps(source, label):
    """返回 (errors, info)。errors 空 = 通过。"""
    try:
        tree = ast.parse(source, filename=label)
    except SyntaxError as e:
        return [f"{label}: ast 解析失败：{e.msg}（第 {e.lineno} 行）"], ""
    lazy = None
    infer_lock = False
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "LazyTTS":
            lazy = node
        elif isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "_INFER_LOCK" for t in node.targets):
            infer_lock = True
    if lazy is None:
        return [f"{label}: 未找到 class LazyTTS"], ""
    have = {n.name for n in lazy.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    missing = [m for m in LAZY_METHODS if m not in have]
    errors = []
    if missing:
        errors.append(f"{label}: LazyTTS 缺少方法 {', '.join(missing)}")
    if not infer_lock:
        errors.append(f"{label}: 模块级未找到 _INFER_LOCK 赋值")
    info = (f"LazyTTS 四方法齐备（{'/'.join(LAZY_METHODS)}），_INFER_LOCK 已定义"
            if not errors else "")
    return errors, info


# ---- 检查 2：生成参数契约 -------------------------------------------------------

def _popped_keys(fn):
    """解析 fn 源码里所有 `generation_kwargs.pop("名字", ...)`，返回键集合。"""
    tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
    fdef = next(n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
    kwname = fdef.args.kwarg.arg  # **generation_kwargs 的名字
    keys = set()
    for node in ast.walk(fdef):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "pop"
                and isinstance(node.func.value, ast.Name) and node.func.value.id == kwname
                and node.args and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)):
            keys.add(node.args[0].value)
    return keys


def collect_engine_contract(vendor_dir, repo_root):
    """跑 _engine_kwargs(默认参数)，并从 infer_v2 收集 infer 接受的键。"""
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    if vendor_dir not in sys.path:
        sys.path.append(vendor_dir)  # 与 lf_integration 一致：追加在末尾，避免遮蔽
    import longform_api
    kwargs = longform_api._engine_kwargs(
        dict(longform_api._DEFAULT_PARAMS), dict(longform_api._DEFAULT_SAMPLING),
        "ref.wav", None, None)
    from indextts.infer_v2 import IndexTTS2
    sig = inspect.signature(IndexTTS2.infer)
    explicit = {n for n, p in sig.parameters.items()
                if n != "self" and p.kind is not inspect.Parameter.VAR_KEYWORD}
    popped = _popped_keys(IndexTTS2.infer_generator)
    return kwargs, explicit | popped, explicit, popped


def validate_kwargs(kwargs, allowed):
    """_engine_kwargs 的每个键都必须被 infer 接受。返回逐键的失败描述。"""
    return [f"infer 不接受 {k}（既不是显式形参，infer_generator 也没 pop 它）"
            for k in sorted(kwargs) if k not in allowed]


# ---- 检查 3：网页与接口（注册冒烟，不 import server.py） ------------------------

class _FakeTTS:
    """只提供工作台契约要求的四个入口；任何真调用都直接抛（本检查绝不加载模型）。"""

    def state(self):
        return {"loaded": False}

    def ensure_loaded(self):
        raise RuntimeError("契约检查禁止加载模型")

    def normalize_emo_vec(self, values, apply_bias=True):
        return list(values)

    def infer(self, *args, **kwargs):
        raise RuntimeError("契约检查禁止推理")


def check_routes(repo_root, vendor_dir):
    from fastapi import APIRouter, FastAPI
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    import lf_integration

    app = FastAPI()
    api = APIRouter(prefix="/api/v1")
    # project_dir 指到临时目录：register 时工作台的 _lf_root() 等助手会
    # makedirs（longform/refs、scripts 等），本脚本承诺不写任何文件，不能让
    # 它在仓库根里建目录。路由表只取决于代码本身，与 project_dir 无关。
    with tempfile.TemporaryDirectory(prefix="lf-contract-") as tmp:
        deps = {
            "tts": _FakeTTS(),
            "infer_lock": threading.Lock(),
            "logger": logging.getLogger("lf-contract"),
            "project_dir": tmp,
            "web_dir": os.path.join(vendor_dir, "web"),
            "verbose": False,
        }
        lf_integration.register(app, api, deps)
    paths = {getattr(r, "path", None) for r in app.routes}
    # 页面路由 include_in_schema=False，openapi() 里没有；manifest 有 —— 两者取并集。
    paths |= set(app.openapi()["paths"])
    missing = [p for p in REQUIRED_PATHS if p not in paths]
    errors = [f"路由缺失：{p}（register 后 app 上找不到）" for p in missing]
    info = f"register 成功，{len(REQUIRED_PATHS)} 条必需路由全部在位" if not errors else ""
    return errors, info


# ---- --selftest：注入坏情况，断言检查确实能报错 ----------------------------------

def run_selftest(server_source, server_label, kwargs, allowed):
    ok = True

    # 坏情况 1：假引擎缺 normalize_emo_vec（从 AST 里删掉该方法再跑检查 1）
    tree = ast.parse(server_source, filename=server_label)
    lazy = next(n for n in tree.body
                if isinstance(n, ast.ClassDef) and n.name == "LazyTTS")
    lazy.body = [n for n in lazy.body
                 if not (isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                         and n.name == "normalize_emo_vec")]
    bad_src = ast.unparse(tree)
    errors, _ = check_engine_caps(bad_src, server_label + "(selftest)")
    captured = [e for e in errors if "normalize_emo_vec" in e]
    if captured:
        _ok(f"selftest-1 引擎缺方法被捕获：{captured[0]}")
    else:
        ok = False
        _fail(f"selftest-1 未捕获「LazyTTS 缺 normalize_emo_vec」，实际报错：{errors}")

    # 坏情况 2：allowed 集合删掉一个真实用到的键（max_mel_tokens）
    bad_allowed = set(allowed) - {"max_mel_tokens"}
    errors = validate_kwargs(kwargs, bad_allowed)
    captured = [e for e in errors if "max_mel_tokens" in e]
    if captured:
        _ok(f"selftest-2 参数越界被捕获：{captured[0]}")
    else:
        ok = False
        _fail(f"selftest-2 未捕获「allowed 删掉 max_mel_tokens」，实际报错：{errors}")

    return ok


# ---- 主流程 ---------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="工作台 × 宿主引擎 契约检查")
    ap.add_argument("--server", default=os.path.join(REPO_ROOT, "server.py"),
                    help="server.py 路径（默认仓库根）")
    ap.add_argument("--vendor", default=os.path.join(REPO_ROOT, "vendor", "lfwb"),
                    help="vendor/lfwb 路径（默认仓库内）")
    ap.add_argument("--selftest", action="store_true",
                    help="注入坏情况，验证检查本身能报错")
    args = ap.parse_args()

    print(f"契约检查 · {REPO_ROOT}")
    print(f"  server = {args.server}")
    print(f"  vendor = {args.vendor}")
    ok = True
    server_source = None
    contract = None

    # 1. 宿主引擎能力（ast 静态解析，不 import）
    try:
        with open(args.server, encoding="utf-8") as f:
            server_source = f.read()
        errors, info = check_engine_caps(server_source, os.path.basename(args.server))
    except OSError as e:
        errors, info = [f"读取 {args.server} 失败：{e}"], ""
    if errors:
        ok = False
        for e in errors:
            _fail(f"1 宿主引擎能力：{e}")
    else:
        _ok(f"1 宿主引擎能力：{info}")

    # 2. 生成参数契约（import longform_api + infer_v2；torch 已装，不加载模型）
    try:
        kwargs, allowed, explicit, popped = collect_engine_contract(args.vendor, REPO_ROOT)
        contract = (kwargs, allowed)
        errors = validate_kwargs(kwargs, allowed)
        info = (f"_engine_kwargs 的 {len(kwargs)} 键 ⊆ 显式形参 {len(explicit)} "
                f"∪ pop {len(popped)}")
    except Exception as e:
        errors, info = [f"{type(e).__name__}: {e}"], ""
    if errors:
        ok = False
        for e in errors:
            _fail(f"2 生成参数契约：{e}")
    else:
        _ok(f"2 生成参数契约：{info}")

    # 3. 网页与接口（register 冒烟）
    try:
        errors, info = check_routes(REPO_ROOT, args.vendor)
    except Exception as e:
        errors, info = [f"{type(e).__name__}: {e}"], ""
    if errors:
        ok = False
        for e in errors:
            _fail(f"3 网页与接口：{e}")
    else:
        _ok(f"3 网页与接口：{info}")

    # selftest 依赖检查 1/2 的输入，两者任一没跑成就直接算失败
    if args.selftest:
        if server_source is None or contract is None:
            ok = False
            _fail("selftest 跳过：检查 1/2 未跑成，负向用例无法注入")
        elif not run_selftest(server_source, os.path.basename(args.server), *contract):
            ok = False

    print("结果：" + ("全部通过" if ok else "存在失败项"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
