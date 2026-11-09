# -*- coding: utf-8 -*-
"""长篇工作台（vendor/lfwb）的宿主适配层。

server.py 的扩展缝（_register_optional_extensions）在启动时 import 本模块并
调用 register(app, api, deps)。本文件是宿主与上游之间唯一的接触面，
上游代码一行不改 —— 所有适配都在这里完成。

为什么 web_dir 要覆盖：
    宿主传入的 web_dir 指向宿主自己的 web/（IndexTTS Studio 的前端资源），
    而工作台的页面（longform.html / guide.html / sfxbench.html / timeline.html）
    和脚本住在 vendor/lfwb/web/。工作台按 web_dir 找页面与静态资源，
    不覆盖就会去宿主目录里找 longform.html，结果是 404。

为什么 vendor 里的文件不能手改：
    vendor/lfwb 是 git subtree 引入的上游固定快照（见 vendor/LFWB_UPSTREAM.md）。
    任何就地修改都会在下次 subtree pull 时产生冲突，而且会让「问题出在谁头上」
    无法判定。需要的适配一律写在本适配层里；上游该修的，去上游提 issue。

project_dir 不改：工作台把运行数据写在 <project_dir>/longform/ 下，参考音频
相对 <project_dir>/prompts/ 与 <project_dir>/examples/ 解析 —— 这些都应当
落在宿主根目录，与宿主共享同一份数据。
"""

import os
import sys

_VENDOR_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "vendor", "lfwb")


def register(app, api, deps):
    """把工作台的 longform 与 timeline 两组路由挂到宿主 app 上。

    约定：本函数不做任何异常兜底。宿主扩展缝已负责记录导入/注册失败，
    这里吞异常只会把问题藏起来；出错就让它带着堆栈抛给宿主记日志。
    """
    # sys.path 注入（幂等）：工作台的 7 个模块（longform_api / timeline_api /
    # lf_static / hrir / rooms 等）互相按顶层模块名 import，必须让整个
    # vendor/lfwb 作为目录出现在搜索路径里。追加在末尾，避免 vendor 内的
    # tools/ 等目录遮蔽宿主或第三方同名包。
    if _VENDOR_DIR not in sys.path:
        sys.path.append(_VENDOR_DIR)

    from longform_api import register_longform
    from timeline_api import register_timeline

    deps = dict(deps or {})
    # 页面与静态资源指向上游快照自带的 web/；其余依赖原样透传。
    deps["web_dir"] = os.path.join(_VENDOR_DIR, "web")
    # project_dir 用宿主根目录：运行数据 longform/、prompts/、examples/ 都在它下面。
    deps["project_dir"] = deps.get("project_dir") or os.path.dirname(os.path.abspath(__file__))

    # 顺序有依赖：timeline_api 复用 longform_api 已注册的 router 与工程状态，
    # 必须先 longform 后 timeline。
    register_longform(app, api, deps=deps)
    register_timeline(app, deps=deps)
