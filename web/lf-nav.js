/* lf-nav.js — 工作台入口的运行时注入脚本
 *
 * 为什么在运行时注入、而不是直接改 web/index.html：
 *   index.html 是上游高频改动文件，本分支作为它的下游，每一次模板冲突都要
 *   人工解。宿主服务（server.py）已留好扩展缝：本文件存在时会在首页
 *   </body> 前注入 <script src="/assets/lf-nav.js?v={lf-nav.js}" defer>，
 *   删掉本文件页面即逐字节回到上游形态。头部结构因此只被「读」不被「改」。
 *
 * 注入位置与约束：
 *   - 挂在 .hdr-tools 内、.hdr-links（B 站/GitHub 外链）之前，读作
 *     「站内导航」先于「站外链接」；绝不放进 #tabs——那里的点击处理器把
 *     每个 .tab 的 data-page 传给 switchPage，塞进去会被绑成「切换到 undefined」。
 *   - 因此本脚本的链接不用 class `tab`、不带 data-page，就是两个普通的
 *     <a href>：整页跳转到 /longform、/timeline（工作台是独立页面，不是
 *     首页内的页签），天然键盘可达，title/aria-label 供读屏与悬停提示。
 *   - 样式自带 <style>，只引用宿主 CSS 变量（--surface/--border/--ink 等），
 *     圆角/高度与头部图标按钮（.iconbtn：28px、--r-sm）一致，深浅主题自动跟随。
 */
(function () {
  'use strict';

  var CONTAINER_ID = 'lf-wb-nav';

  function inject() {
    // 幂等：重复执行（如热重载再注入一次）不重复插入。
    if (document.getElementById(CONTAINER_ID)) return;

    var tools = document.querySelector('.hdr-tools');
    if (!tools) return; // 头部结构被上游改掉时安静退出，绝不报错打断页面

    var style = document.createElement('style');
    // 颜色全部走宿主变量，不硬编码；尺寸钉在 .iconbtn 的规格上（28px / --r-sm）。
    style.textContent =
      '#' + CONTAINER_ID + '{display:flex;gap:var(--s1);flex:none}' +
      '#' + CONTAINER_ID + ' a{' +
      'display:inline-flex;align-items:center;gap:var(--s1);' +
      'height:28px;padding:0 var(--s2);' +
      'border:1px solid var(--border);border-radius:var(--r-sm);' +
      'background:var(--surface);color:var(--ink);' +
      'font-family:var(--sans);font-size:var(--fs-13);font-weight:600;line-height:1;' +
      'text-decoration:none;white-space:nowrap;' +
      'transition:background .18s ease,border-color .18s ease}' +
      '#' + CONTAINER_ID + ' a:hover{background:var(--surface-2);' +
      'border-color:color-mix(in srgb, var(--faint) 40%, var(--border))}' +
      '#' + CONTAINER_ID + ' a:focus-visible{outline:2px solid var(--accent);outline-offset:1px}';
    document.head.appendChild(style);

    var box = document.createElement('div');
    box.id = CONTAINER_ID;

    var a1 = document.createElement('a');
    a1.href = '/longform';
    a1.textContent = '台本';
    a1.title = '台本工作台（长文本分镜 / 逐句合成）';
    a1.setAttribute('aria-label', '打开台本工作台');

    var a2 = document.createElement('a');
    a2.href = '/timeline';
    a2.textContent = '时间轴';
    a2.title = '时间轴（跨句排布 / 拼接试听）';
    a2.setAttribute('aria-label', '打开时间轴工作台');

    box.appendChild(a1);
    box.appendChild(a2);

    // 插到外链组之前；外链组不在就直接追加到工具组末尾。
    var links = tools.querySelector('.hdr-links');
    if (links) tools.insertBefore(box, links);
    else tools.appendChild(box);
  }

  // defer 脚本按文档顺序在 DOMContentLoaded 前执行，理论上可直接跑；
  // 仍按 readyState 兜底：宿主若在 </body> 后动态再注入本脚本，readyState
  // 已是 complete，直接执行即可。
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inject, { once: true });
  } else {
    inject();
  }
})();
