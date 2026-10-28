#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成存储罗盘站点首页 index.html + 更新 README 文章目录。
用法:  python tools/build_site.py   （在 storage-compass 仓库根目录运行）
"""
import os, re, glob, html, subprocess

PUB = 'content/published'
INDEX_MD = 'content/100-questions/README.md'
REPO = 'https://github.com/zlj123455/storage-compass'
BLOB = REPO + '/blob/main/content/published/'
SITE = 'https://zlj123455.github.io/storage-compass'

AI_SERIES = [
    ('第1讲', '模型为什么不能直接给答案？', '一次推理请求的完整旅程',
     'https://mp.weixin.qq.com/s/IUrhhro7XZYgFW6R-T7RBg'),
    ('第2讲', 'KV Cache 到底缓存了什么？', 'K/V 张量为何随序列线性膨胀',
     'https://mp.weixin.qq.com/s/FvR--NyGDy0eMbFVmLFlaQ'),
    ('第3讲', '装不下了，延迟和显存为何同时告急', '显存不足如何传导为并发下降',
     'https://mp.weixin.qq.com/s/iweY7rpUYspn1GGxjUVURg'),
    ('第4讲', '不够用了，究竟有几类解决办法', '驱逐/量化/共享/下沉的代价',
     'https://mp.weixin.qq.com/s/ZxsIfohvzl8w7VxxIaPDMw'),
    ('第5讲', '能不能放到 SSD，答案不在 SSD 有多快', '落盘瓶颈在访问模式',
     'https://mp.weixin.qq.com/s/0FGCsdislK28xeRNQYtjhA'),
    ('第6讲', '先做 PD 分离，再做存算分离', '企业级推理架构的落地顺序',
     'https://mp.weixin.qq.com/s/Swm9M_wLfoYLKK9FVFX75A'),
]


def git_time(f):
    try:
        return int(subprocess.check_output(
            ['git', 'log', '-1', '--format=%at', '--', f], text=True).strip() or 0)
    except Exception:
        return 0


def load_chapters():
    """从 100 问目录解析 {编号: (章序, 章名)} 与章节顺序。"""
    if not os.path.exists(INDEX_MD):
        return {}, []
    text = open(INDEX_MD, encoding='utf-8').read()
    order, mapping, cur = [], {}, None
    for line in text.splitlines():
        m = re.match(r'^##\s+第([一二三四五六七八九十]+)章[:：]\s*(.+)$', line.strip())
        if m:
            cur = (m.group(1), m.group(2).strip())
            order.append(cur)
            continue
        if line.startswith('## ') and cur:
            cur = None
        if cur:
            qm = re.match(r'^\|\s*Q(\d+)\s*\|', line.strip())
            if qm:
                mapping[int(qm.group(1))] = cur
    return mapping, order


def collect_questions():
    arts = {}
    for f in glob.glob(PUB + '/*.md'):
        b = os.path.basename(f)
        if b.lower() == 'readme.md':
            continue
        m = re.match(r'Q(\d+)-.*\.md$', b)
        if not m:
            continue
        num = int(m.group(1))
        text = open(f, encoding='utf-8', errors='ignore').read()
        tm = re.search(r'^#\s+(.+)$', text, re.M)
        title = re.sub(r'[*_`]', '', tm.group(1).strip()) if tm else 'Q%03d' % num
        title = re.sub(r'^Q\d{3}[：:]\s*', '', title)
        stamp = git_time(f)
        if num not in arts or stamp > arts[num][0]:
            arts[num] = (stamp, b, title)
    return arts


def build():
    qs = collect_questions()
    chap_map, chap_order = load_chapters()

    groups = {}
    for n, (stamp, b, t) in qs.items():
        ch = chap_map.get(n)
        groups.setdefault(ch, []).append((n, b, t))
    groups = {k: sorted(v) for k, v in groups.items()}

    # 章节导航 + 分章卡片
    chips, sections = [], []
    seq = 0
    for i, ch in enumerate(chap_order):
        items = groups.get(ch, [])
        if not items:
            continue
        seq += 1
        anchor = 'ch%d' % seq
        cn = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十'][i] if i < 10 else str(i + 1)
        chips.append('<a class="chip" href="#%s">第%s章 · %s</a>' % (anchor, cn, html.escape(ch[1])))
        cards = '\n'.join(
            '<li class="item" data-k="q%03d %s"><a href="%s%s" target="_blank" rel="noopener">'
            '<span class="qno">Q%03d</span><span class="qt">%s</span></a></li>'
            % (n, html.escape(t.lower()), BLOB, b, n, html.escape(t)) for n, b, t in items)
        sections.append('''  <section class="chapter" id="%s">
    <div class="ch-head">
      <span class="ch-num">%02d</span>
      <div class="ch-title"><h2>%s</h2><p>%d 篇</p></div>
    </div>
    <ul class="grid">
%s
    </ul>
  </section>''' % (anchor, seq, html.escape(ch[1]), len(items), cards))

    extras = groups.get(None, [])
    if extras:
        cards = '\n'.join(
            '<li class="item" data-k="q%03d %s"><a href="%s%s" target="_blank" rel="noopener">'
            '<span class="qno">Q%03d</span><span class="qt">%s</span></a></li>'
            % (n, html.escape(t.lower()), BLOB, b, n, html.escape(t)) for n, b, t in extras)
        chips.append('<a class="chip" href="#chx">其他</a>')
        sections.append('''  <section class="chapter" id="chx">
    <div class="ch-head"><span class="ch-num">+</span>
      <div class="ch-title"><h2>其他主题</h2><p>%d 篇</p></div></div>
    <ul class="grid">
%s
    </ul>
  </section>''' % (len(extras), cards))

    ai_cards = '\n'.join(
        '      <li class="ai-card item" data-k="%s %s %s"><a href="%s" target="_blank" rel="noopener">'
        '<span class="lect">%s</span><b>%s</b><i>%s</i></a></li>'
        % (k.lower(), html.escape(t.lower()), html.escape(s.lower()), u, k, html.escape(t), html.escape(s))
        for k, t, s, u in AI_SERIES)

    total = sum(len(v) for v in groups.values())
    page = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>存储罗盘 · 企业存储与 AI 基础设施知识库</title>
<meta name="description" content="面向企业架构师、IT 负责人与存储选型团队的公开知识库：企业存储架构、可靠性、性能、选型判断，以及 AI 推理对存储的需求。">
<style>
* { margin:0; padding:0; box-sizing:border-box; }
:root { --red:#B01F24; --ink:#22221F; --muted:#77756E; --line:#E9E5DC; --paper:#FCFBF8; }
body { font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei","Segoe UI",sans-serif;
  background:var(--paper); color:var(--ink); line-height:1.65; -webkit-font-smoothing:antialiased; }
.wrap { max-width:1040px; margin:0 auto; padding:0 24px; }

.hero { padding:72px 0 32px; border-bottom:1px solid var(--line); }
.kicker { display:inline-block; font-size:12px; letter-spacing:.18em; color:var(--red);
  border:1px solid #E7C9C9; padding:4px 10px; border-radius:999px; background:#FDF6F5; }
h1 { font-size:38px; font-weight:500; letter-spacing:-.5px; margin:18px 0 10px; }
h1 span { color:#B9B5AA; font-size:20px; letter-spacing:0; margin-left:10px; }
.lede { color:#5F5D57; font-size:15.5px; max-width:640px; }
.stats { display:flex; gap:34px; margin:26px 0 0; flex-wrap:wrap; }
.stat b { font-size:26px; font-weight:500; color:var(--red); margin-right:6px; }
.stat { font-size:13px; color:var(--muted); }

.toolbar { position:sticky; top:0; z-index:9; background:rgba(252,251,248,.94);
  backdrop-filter:blur(8px); border-bottom:1px solid var(--line); padding:12px 0; margin-bottom:8px; }
.toolbar .wrap { display:flex; gap:14px; align-items:center; flex-wrap:wrap; }
#q { flex:1 1 240px; min-width:200px; border:1px solid var(--line); background:#fff; border-radius:10px;
  padding:9px 14px; font-size:14px; color:var(--ink); outline:none; }
#q:focus { border-color:#D9A9A9; box-shadow:0 0 0 3px #F7EDEC; }
.chips { display:flex; gap:8px; overflow-x:auto; padding-bottom:2px; }
.chip { white-space:nowrap; font-size:12.5px; color:#5F5D57; border:1px solid var(--line); background:#fff;
  padding:6px 11px; border-radius:999px; text-decoration:none; }
.chip:hover { border-color:#D9A9A9; color:var(--red); }

.chapter { padding:34px 0 6px; }
.ch-head { display:flex; align-items:baseline; gap:14px; margin-bottom:16px; }
.ch-num { font-size:13px; font-weight:500; color:var(--red); border:1px solid #E7C9C9; background:#FDF6F5;
  border-radius:6px; padding:2px 7px; }
.ch-title h2 { font-size:19px; font-weight:500; letter-spacing:.2px; }
.ch-title p { font-size:12.5px; color:#B4B0A5; margin-top:2px; }

.grid { list-style:none; display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:10px; }
.item a { display:flex; gap:12px; align-items:baseline; background:#fff; border:1px solid var(--line);
  border-radius:10px; padding:13px 15px; text-decoration:none; color:var(--ink); height:100%;
  transition:border-color .15s, transform .15s; }
.item a:hover { border-color:#DCC5C4; transform:translateY(-1px); }
.qno { font-size:12px; color:#A8A399; font-variant-numeric:tabular-nums; min-width:38px; }
.qt { font-size:14px; line-height:1.55; }

.ai-grid { list-style:none; display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:10px; }
.ai-card a { display:flex; flex-direction:column; gap:6px; background:linear-gradient(180deg,#fff,#FDFAF7);
  border:1px solid var(--line); border-left:3px solid var(--red); border-radius:10px; padding:16px 18px;
  text-decoration:none; color:var(--ink); height:100%; }
.ai-card a:hover { border-color:#DCC5C4; border-left-color:var(--red); }
.lect { font-size:11.5px; color:var(--red); letter-spacing:.1em; }
.ai-card b { font-size:14.5px; font-weight:500; line-height:1.5; }
.ai-card i { font-size:12.5px; color:#8B877D; font-style:normal; }

.cta { margin:44px 0 0; padding:26px 28px; background:#fff; border:1px solid var(--line); border-radius:14px;
  display:flex; justify-content:space-between; align-items:center; gap:18px; flex-wrap:wrap; }
.cta h3 { font-size:16px; font-weight:500; }
.cta p { font-size:13.5px; color:#77756E; margin-top:4px; }
.btn { display:inline-block; background:var(--red); color:#fff; text-decoration:none; font-size:14px;
  padding:10px 20px; border-radius:9px; }
.btn:hover { background:#96191D; }
.foot { color:#B4B0A5; font-size:12.5px; text-align:center; padding:36px 0 50px; }
.empty { display:none; text-align:center; color:#A8A399; font-size:14px; padding:40px 0; }

@media (max-width:640px) {
  .hero { padding:44px 0 26px; }
  h1 { font-size:28px; } h1 span { font-size:15px; display:block; margin:8px 0 0; }
  .stats { gap:20px; } .stat b { font-size:21px; }
  .grid, .ai-grid { grid-template-columns:1fr; }
  .cta { flex-direction:column; align-items:flex-start; }
}
</style>
</head>
<body>
<header class="hero">
  <div class="wrap">
    <span class="kicker">公开知识库</span>
    <h1>存储罗盘<span>storage-compass</span></h1>
    <p class="lede">面向企业架构师、IT 负责人与存储选型团队的公开知识库。只做一件事：把企业存储的架构、可靠性、性能与选型判断，讲成能直接用来做决策的话。</p>
    <div class="stats">
      <span class="stat"><b>{{QN}}</b>篇问答</span>
      <span class="stat"><b>{{CH}}</b>个章节</span>
      <span class="stat"><b>{{AIN}}</b>讲 AI 系列</span>
    </div>
  </div>
</header>

<div class="toolbar">
  <div class="wrap">
    <input id="q" type="search" placeholder="搜索编号或关键词：Q019 / NVMe / 灾备 / 全闪">
    <nav class="chips">{{CHIPS}}</nav>
  </div>
</div>

<main class="wrap">
{{SECTIONS}}

  <section class="chapter" id="ai">
    <div class="ch-head"><span class="ch-num">AI</span>
      <div class="ch-title"><h2>AI 推理与存储 · KV Cache 六讲</h2><p>正文发布于公众号「存储罗盘」</p></div>
    </div>
    <ul class="ai-grid">
{{AICARDS}}
    </ul>
  </section>

  <p class="empty" id="empty">没有匹配的条目，换个关键词试试。</p>

  <section class="cta">
    <div><h3>存储选型、架构讨论、同行交流</h3>
      <p>全闪阵列、SAN / 灾备、信创存储的一线信息，随时聊。</p></div>
    <a class="btn" href="card/">联系方式 →</a>
  </section>

  <p class="foot">© 2026 赵龙杰 · 中科曙光 FlashNexus · 公众号「存储罗盘」同步连载</p>
</main>

<script>
(function(){
  var q = document.getElementById('q');
  var items = Array.prototype.slice.call(document.querySelectorAll('.item'));
  var empty = document.getElementById('empty');
  var chapters = Array.prototype.slice.call(document.querySelectorAll('.chapter'));
  q.addEventListener('input', function(){
    var v = q.value.trim().toLowerCase();
    var shown = 0;
    items.forEach(function(it){
      var hit = !v || (it.getAttribute('data-k') || '').indexOf(v) >= 0;
      it.style.display = hit ? '' : 'none';
      if (hit) shown++;
    });
    chapters.forEach(function(sec){
      var any = Array.prototype.some.call(sec.querySelectorAll('.item'), function(it){ return it.style.display !== 'none'; });
      sec.style.display = (any || !v) ? '' : 'none';
    });
    empty.style.display = (v && shown === 0) ? 'block' : 'none';
  });
})();
</script>
</body>
</html>
'''
    page = (page.replace('{{QN}}', str(total)).replace('{{AIN}}', str(len(AI_SERIES)))
                .replace('{{CH}}', str(sum(1 for s in sections)))
                .replace('{{CHIPS}}', '\n      '.join(chips))
                .replace('{{SECTIONS}}', '\n\n'.join(sections))
                .replace('{{AICARDS}}', ai_cards))
    open('index.html', 'w', encoding='utf-8').write(page)

    # README 同步
    readme_list = '\n'.join('- [Q%03d：%s](%s)' % (n, t, b) for n, (st, b, t) in sorted(qs.items()))
    ai_md = '\n'.join('- [%s %s](%s)' % (k, t, u) for k, t, s, u in AI_SERIES)
    new_section = '''## 快速入口

- [在线阅读版](%s/)
- [联系方式 / 交流](%s/card/)
- [企业存储架构师 100 问](content/100-questions/README.md)

### 企业存储架构师 100 问（已发布 %d 篇）

%s

### AI 推理与存储 · KV Cache 六讲（%d 篇，正文见公众号）

%s
''' % (SITE, SITE, total, readme_list, len(AI_SERIES), ai_md)
    old = open('README.md', encoding='utf-8').read()
    start, end = old.find('## 快速入口'), old.find('## 仓库结构')
    if start >= 0 and end > start:
        open('README.md', 'w', encoding='utf-8').write(old[:start] + new_section + '\n' + old[end:])

    print('index.html: %d 篇 / %d 章 / %d 讲；README 已同步' % (total, len(sections), len(AI_SERIES)))


if __name__ == '__main__':
    build()
