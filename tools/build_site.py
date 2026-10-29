#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成存储罗盘站点首页 index.html + 更新 README 文章目录。

结构：系列（series）→ 章节/专题（chapter）→ 文章（item）
设计定稿（2026-10-29）：
  - 导航统一为「系列 tab + 章节 chips」双层，手机 / 桌面同一套组件，tab 是过滤不是锚点；
  - 手机：顶栏 48（品牌 + 搜索图标 + 联系）、标题区 68（左标题 / 右简介，统计隐藏）、
    横排双码卡 117、导航 62，正文起点约 295px，一屏可见 12+ 条；
  - 桌面：标题区保留统计，左栏双列卡片 + 右栏吸顶联系卡，顶栏常驻搜索框；
  - 联系入口三处：顶栏「联系」按钮 → 抽屉；手机首屏双码卡 / 桌面侧栏双码卡；
  - 公众号素材：assets/wx-qr.jpg；个人微信码：card/qr-wechat.png。
用法:  python tools/build_site.py   （在 storage-compass 仓库根目录运行）
"""
import os, re, glob, html, json, subprocess

PUB = 'content/published'
INDEX_MD = 'content/100-questions/README.md'
MP_LINKS = 'tools/mp-links.json'
REPO = 'https://github.com/zlj123455/storage-compass'
BLOB = REPO + '/blob/main/content/published/'
SITE = 'https://zlj123455.github.io/storage-compass'

QR_PERSONAL = 'card/qr-wechat.png'   # 个人微信二维码（从文章联系方式卡裁出）
QR_WX = 'assets/wx-qr.jpg'           # 公众号二维码（后台下载 258x258）


def load_mp_links():
    """公众号原文链接：{'Q001': url, ...}；缺失的条目回退到 GitHub 正文。"""
    if os.path.exists(MP_LINKS):
        return json.load(open(MP_LINKS, encoding='utf-8'))
    return {}

# ── 系列二：AI 推理与存储（未来可继续加子专题）────────────────────────
AI_GROUPS = [
    ('KV Cache 六讲', '从一次推理请求的旅程，讲到企业级推理架构的落地顺序', [
        ('第1讲', '模型为什么不能直接给答案？', '一次推理请求的完整旅程',
         'https://mp.weixin.qq.com/s/IUrhhro7XZYgFW6R-T7RBg'),
        ('第2讲', 'KV Cache 到底缓存了什么？', 'K/V 张量为何随序列线性膨胀',
         'https://mp.weixin.qq.com/s/FvR--NyGDy0eMbFVmLFlaQ'),
        ('第3讲', '装不下了，延迟和显存为何同时告急', '显存不足如何传导为并发下降',
         'https://mp.weixin.qq.com/s/iweY7rpUYspn1GGxjUVURg'),
        ('第4讲', '不够用了，究竟有几类解决办法', '驱逐 / 量化 / 共享 / 下沉的代价',
         'https://mp.weixin.qq.com/s/ZxsIfohvzl8w7VxxIaPDMw'),
        ('第5讲', '能不能放到 SSD，答案不在 SSD 有多快', '落盘瓶颈在访问模式',
         'https://mp.weixin.qq.com/s/0FGCsdislK28xeRNQYtjhA'),
        ('第6讲', '先做 PD 分离，再做存算分离', '企业级推理架构的落地顺序',
         'https://mp.weixin.qq.com/s/Swm9M_wLfoYLKK9FVFX75A'),
    ]),
]


def git_time(f):
    try:
        return int(subprocess.check_output(
            ['git', 'log', '-1', '--format=%at', '--', f], text=True).strip() or 0)
    except Exception:
        return 0


def load_chapters():
    """解析 100 问目录：({编号: (章序, 章名)}, [(章序, 章名)])"""
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


def item_html(key, no, title, note, href, tag=None):
    note_html = '<em class="note">%s</em>' % html.escape(note) if note else ''
    tag_html = '<span class="tag">%s</span>' % html.escape(tag) if tag else ''
    return ('<li class="item" data-k="%s"><a href="%s" target="_blank" rel="noopener">'
            '<span class="qno">%s</span><span class="qt">%s%s</span>%s</a></li>'
            % (html.escape(key.lower()), href, no, html.escape(title), note_html, tag_html))


def chapter_block(anchor, badge, name, count, cards, desc=None):
    """章节块：details/summary，手机端折叠、桌面端全展开。"""
    desc_html = '<p class="ch-desc">%s</p>' % html.escape(desc) if desc else ''
    return '''      <details class="chapter" id="%s">
        <summary class="ch-head"><span class="ch-num">%s</span>
          <h3>%s</h3><span class="ch-count">%s</span><span class="ch-arrow">›</span></summary>
        <div class="ch-body">%s
          <ul class="grid">
%s
          </ul>
        </div>
      </details>''' % (anchor, badge, html.escape(name), count, desc_html, cards)


def build():
    qs = collect_questions()
    chap_map, chap_order = load_chapters()
    mp = load_mp_links()

    groups = {}
    for n, (stamp, b, t) in qs.items():
        groups.setdefault(chap_map.get(n), []).append((n, b, t))
    groups = {k: sorted(v) for k, v in groups.items()}

    # ── 系列一：100 问 ────────────────────────────────
    chips1, s1_chapters = [], []
    seq = 0
    cn_num = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
    for i, ch in enumerate(chap_order):
        items = groups.get(ch, [])
        if not items:
            continue
        seq += 1
        anchor = 'ch%d' % seq
        badge = '第%s章' % (cn_num[i] if i < 10 else i + 1)
        chips1.append('<a class="chip" href="#%s">%s</a>' % (anchor, badge))
        cards = '\n'.join(item_html('q%03d %s %s' % (n, t, ch[1]), 'Q%03d' % n, t, '',
                                    mp.get('Q%03d' % n, BLOB + b)) for n, b, t in items)
        s1_chapters.append(chapter_block(anchor, badge, ch[1], '%d 篇' % len(items), cards))

    extras = groups.get(None, [])
    if extras:
        cards = '\n'.join(item_html('q%03d %s' % (n, t), 'Q%03d' % n, t, '',
                                    mp.get('Q%03d' % n, BLOB + b)) for n, b, t in extras)
        chips1.append('<a class="chip" href="#chx">其他主题</a>')
        s1_chapters.append(chapter_block('chx', '+', '其他主题', '%d 篇' % len(extras), cards))

    q_total = sum(len(v) for v in groups.values())
    q_chapters = len(s1_chapters)

    series1 = '''  <section class="series" id="s1" data-s="s1">
    <div class="series-head">
      <span class="series-count">%d 篇 · %d 章 · 公众号原文</span>
      <h2>企业存储架构师 100 问</h2>
      <p>从原理到选型判断的连续追问：每篇给结论、机制、取舍与适用边界，编号稳定、可长期引用。</p>
    </div>
    <div class="series-body">
%s
    </div>
  </section>''' % (q_total, q_chapters, '\n'.join(s1_chapters))

    # ── 系列二：AI 推理 ───────────────────────────────
    chips2, ai_total, ai_blocks = [], 0, []
    for gi, (gname, gdesc, items) in enumerate(AI_GROUPS):
        ai_total += len(items)
        anchor = 'ai%d' % (gi + 1)
        chips2.append('<a class="chip" href="#%s">%s</a>' % (anchor, html.escape(gname)))
        cards = '\n'.join(item_html('%s %s %s' % (lab, t, s), lab, t, s, u)
                          for lab, t, s, u in items)
        ai_blocks.append(chapter_block(anchor, 'AI', gname, '%d 讲' % len(items), cards, gdesc))

    series2 = '''  <section class="series" id="s2" data-s="s2" style="display:none">
    <div class="series-head">
      <span class="series-count">%d 讲 · 持续更新 · 公众号原文</span>
      <h2>AI 推理与存储</h2>
      <p>大模型推理把存储重新拉回架构核心：KV Cache 放哪、带宽从哪来、PD 与存算如何分离。</p>
    </div>
    <div class="series-body">
%s
    </div>
  </section>''' % (ai_total, '\n'.join(ai_blocks))

    total_all = q_total + ai_total
    n_series = 2

    page = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>存储罗盘 · 企业存储与 AI 基础设施知识库</title>
<meta name="description" content="面向企业架构师、IT 负责人与存储选型团队的公开知识库：企业存储架构、可靠性、性能、选型判断，以及 AI 推理对存储的需求。">
<style>
* { margin:0; padding:0; box-sizing:border-box; }
:root { --red:#B01F24; --pink:#E6108D; --ink:#22221F; --muted:#77756E; --line:#E9E5DC; --paper:#FCFBF8; }
body { font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei","Segoe UI",sans-serif;
  background:var(--paper); color:var(--ink); line-height:1.6; -webkit-font-smoothing:antialiased; }
.wrap { max-width:1040px; margin:0 auto; padding:0 16px; }
a { -webkit-tap-highlight-color:transparent; }

/* ── 顶栏：品牌 + 搜索 + 联系（吸顶）──────────────── */
.topbar { position:sticky; top:0; z-index:20; background:rgba(252,251,248,.97);
  backdrop-filter:blur(10px); border-bottom:1px solid var(--line); }
.topbar .wrap { display:flex; align-items:center; gap:8px; height:48px; }
.brand { display:flex; align-items:center; gap:8px; font-size:14px; font-weight:600;
  color:var(--ink); text-decoration:none; white-space:nowrap; }
.brand i { width:24px; height:24px; border-radius:6px; background:var(--red); color:#fff;
  font-style:normal; font-size:12px; display:flex; align-items:center; justify-content:center; }
.icon-btn { margin-left:auto; width:34px; height:34px; border:none; background:none;
  display:flex; align-items:center; justify-content:center; color:#5A5952; cursor:pointer; }
.top-cta { background:var(--red); color:#fff; border:none; border-radius:999px;
  padding:7px 16px; font-size:12.5px; cursor:pointer; font-family:inherit; }
.top-cta:active { background:#96191D; }
.top-search { display:none; }

/* 手机搜索层 */
.sp { position:fixed; left:0; right:0; top:48px; z-index:19; background:#fff; display:none;
  border-bottom:1px solid var(--line); padding:10px 0 12px; box-shadow:0 8px 20px rgba(34,34,31,.06); }
.sp.on { display:block; }
.sp-in { display:flex; gap:10px; align-items:center; }
.sp input { flex:1; min-width:0; border:1px solid var(--line); border-radius:10px;
  padding:10px 12px; font-size:16px; font-family:inherit; outline:none; color:var(--ink); }
.sp input:focus { border-color:#D9A9A9; box-shadow:0 0 0 3px #F7EDEC; }
.sp-x { border:none; background:none; color:var(--muted); font-size:13px; font-family:inherit; padding:8px 4px; }

/* ── 标题区：左标题 / 右简介（手机隐藏统计）───────── */
.hero { display:flex; align-items:flex-start; gap:12px; padding:12px 0 10px; }
.hero h1 { font-size:20px; font-weight:700; letter-spacing:-.3px; white-space:nowrap; }
.hero-side { margin-left:auto; text-align:right; flex:1; min-width:0; }
.lede { font-size:11px; line-height:1.5; color:#8A887E; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.stats, .stat-sub { display:none; }

/* ── 手机首屏双码卡（横排一行）；桌面侧栏仅桌面显示 ── */
.side { display:none; }
.contact { padding:0 0 8px; }
.contact-card { display:flex; align-items:center; gap:10px; background:#fff;
  border:1px solid var(--line); border-radius:12px; padding:10px 12px; }
.cc-col { display:flex; align-items:center; gap:8px; flex:1; min-width:0; }
.cc-col img { width:64px; height:64px; border:1px solid var(--line); border-radius:8px; flex:none; }
.cc-txt { display:flex; flex-direction:column; gap:4px; min-width:0; }
.cc-txt b { font-size:11.5px; font-weight:600; white-space:nowrap; }
.cc-hint { font-size:9.5px; color:#9A988F; white-space:nowrap; }
.cc-div { width:1px; align-self:stretch; background:var(--line); flex:none; }
.wx-search { display:inline-flex; align-items:center; gap:6px; background:var(--pink); color:#fff;
  font-size:9.5px; font-weight:500; padding:3px 9px; border-radius:999px; white-space:nowrap; }
.wx-mag { width:8px; height:8px; border:1.5px solid rgba(255,255,255,.95); border-radius:50%;
  position:relative; flex:none; }
.wx-mag::after { content:''; position:absolute; width:4px; height:1.5px; background:rgba(255,255,255,.95);
  transform:rotate(45deg); right:-3px; bottom:-1px; }

/* ── 双层导航：系列 tab + 章节 chips ──────────────── */
.nav { position:sticky; top:48px; z-index:15; background:rgba(252,251,248,.97);
  backdrop-filter:blur(10px); border-bottom:1px solid var(--line); padding:7px 0 6px; margin-bottom:2px; }
.tabs { display:flex; gap:2px; background:#F2EEE5; border-radius:999px; padding:2px;
  width:max-content; margin-bottom:8px; }
.tab { border:none; background:none; font-family:inherit; font-size:12px; color:#8A887E;
  padding:6px 14px; border-radius:999px; cursor:pointer; white-space:nowrap; }
.tab.on { background:#fff; color:var(--red); font-weight:600; box-shadow:0 1px 2px rgba(34,34,31,.07); }
.chip-row { display:none; gap:7px; overflow-x:auto; padding-bottom:2px; scrollbar-width:none; }
.chip-row::-webkit-scrollbar { display:none; }
.chip-row.on { display:flex; }
.chip { white-space:nowrap; font-size:11.5px; color:#5F5D57; border:1px solid var(--line);
  background:#fff; padding:4px 10px; border-radius:999px; text-decoration:none; }
.chip.on { border-color:var(--red); color:var(--red); }

/* ── 系列 / 章节 / 条目 ───────────────────────────── */
.series { padding:10px 0 2px; }
.series-head { display:none; }
details.chapter { padding:2px 0; scroll-margin-top:118px; }
details.chapter + details.chapter { border-top:1px dashed #EFEBE2; }
details.chapter > summary { list-style:none; cursor:pointer; }
details.chapter > summary::-webkit-details-marker { display:none; }
.ch-head { display:flex; align-items:center; gap:8px; padding:7px 0; min-height:40px; }
.ch-num { font-size:10.5px; font-weight:500; color:var(--red); border:1px solid #E7C9C9;
  background:#FDF6F5; border-radius:5px; padding:1px 6px; white-space:nowrap; }
.ch-head h3 { font-size:13.5px; font-weight:600; }
.ch-count { font-size:11px; color:#B4B0A5; margin-left:auto; white-space:nowrap; }
.ch-arrow { color:#C4C0B5; font-size:14px; transition:transform .2s; margin-left:2px; }
details[open] > summary .ch-arrow { transform:rotate(90deg); }
.ch-desc { display:none; }

.grid { list-style:none; display:block; }
.item a { display:flex; gap:9px; align-items:baseline; padding:9px 0; text-decoration:none;
  color:var(--ink); border-bottom:1px solid #F2EEE5; }
.qno { font-size:10.5px; color:#A8A399; font-variant-numeric:tabular-nums; min-width:36px; flex:none; }
.qt { font-size:13px; line-height:1.5; flex:1; }
.note, .tag { display:none; }

/* ── 底部 ─────────────────────────────────────────── */
.cta { margin:24px 0 0; padding:16px 18px; background:#fff; border:1px solid var(--line);
  border-radius:12px; display:flex; justify-content:space-between; align-items:center; gap:14px; flex-wrap:wrap; }
.cta h3 { font-size:14px; font-weight:600; }
.cta p { font-size:12px; color:var(--muted); margin-top:3px; }
.btn { display:inline-block; background:var(--red); color:#fff; text-decoration:none;
  font-size:12.5px; border:none; padding:9px 18px; border-radius:8px; cursor:pointer; font-family:inherit; }
.btn:hover { background:#96191D; }
.foot { color:#B4B0A5; font-size:11.5px; text-align:center; padding:26px 0 40px; }
.empty { display:none; text-align:center; color:#A8A399; font-size:13px; padding:30px 0; }

/* ── 联系抽屉：手机底部弹出，桌面居中 ─────────────── */
.overlay { position:fixed; inset:0; background:rgba(20,20,18,.45); opacity:0; pointer-events:none;
  transition:opacity .2s; z-index:50; }
.overlay.on { opacity:1; pointer-events:auto; }
.sheet { position:fixed; left:50%; bottom:0; transform:translate(-50%,105%); width:min(430px,100%);
  background:#fff; border-radius:18px 18px 0 0; z-index:51; padding:12px 22px 30px;
  transition:transform .25s ease; text-align:center; }
.sheet.on { transform:translate(-50%,0); }
.sheet-grab { width:40px; height:4px; border-radius:2px; background:#D3D1C7; margin:0 auto 10px; }
.sheet-head { display:flex; align-items:center; }
.sheet-head h3 { font-size:17px; font-weight:600; flex:1; text-align:left; }
.sheet-x { border:none; background:none; font-size:22px; color:#888780; cursor:pointer;
  padding:6px 10px; line-height:1; }
.sheet-grid { display:grid; grid-template-columns:1fr 1fr; gap:18px; margin:14px 0 6px; }
.sheet-grid img { width:100%; max-width:150px; border:1px solid var(--line); border-radius:10px; }
.sheet-grid .s-col { display:flex; flex-direction:column; align-items:center; gap:6px; }
.s-label { font-size:13px; font-weight:600; }
.s-sub { font-size:11.5px; color:#A8A399; }
.sheet .wx-search { font-size:12px; padding:6px 12px; margin-top:2px; }
.sheet-note { font-size:12px; color:#77756E; border-top:1px dashed #EFEBE2; margin-top:14px; padding-top:12px; }

/* ── 桌面端 ───────────────────────────────────────── */
@media (min-width:768px) {
  .wrap { padding:0 24px; }
  .topbar .wrap { height:56px; gap:14px; }
  .icon-btn { display:none; }
  .top-search { display:block; flex:1; max-width:320px; margin-left:auto; }
  .top-search input { width:100%; border:1px solid #EBE6DA; background:#F7F4ED; border-radius:999px;
    padding:7px 14px; font-size:13px; font-family:inherit; outline:none; color:var(--ink); }
  .top-search input:focus { border-color:#D9A9A9; background:#fff; box-shadow:0 0 0 3px #F7EDEC; }
  .top-cta { padding:8px 18px; font-size:13px; }
  .sp { display:none !important; }

  .hero { align-items:flex-end; padding:34px 0 20px; }
  .hero h1 { font-size:34px; letter-spacing:-.6px; }
  .hero-side { max-width:560px; }
  .lede { font-size:13.5px; line-height:1.6; color:#5F5D57; margin-bottom:10px; white-space:normal; overflow:visible; }
  .stats { display:flex; gap:22px; justify-content:flex-end; }
  .stat { font-size:12.5px; color:var(--muted); }
  .stat b { font-size:19px; font-weight:600; color:var(--red); margin-right:4px; }
  .stat-sub { display:block; font-size:11.5px; color:#B4B0A5; margin-top:5px; }

  .contact { display:none; }
  .layout { display:grid; grid-template-columns:minmax(0,1fr) 268px; gap:32px; align-items:start; }
  .nav { top:56px; padding:10px 0 8px; }
  .tabs { margin-bottom:9px; }
  .tab { font-size:13px; padding:6px 18px; }
  .chip { font-size:12px; padding:5px 12px; }

  .series { padding:20px 0 6px; }
  .series-head { display:block; margin-bottom:12px; }
  .series-count { display:block; font-size:11.5px; color:#B4B0A5; letter-spacing:.02em; }
  .series-head h2 { font-size:22px; font-weight:600; letter-spacing:-.2px; margin-top:4px; }
  .series-head p { font-size:13px; color:#6B6961; margin-top:5px; max-width:680px; }
  .series-body { border-left:2px solid #F0EBE1; padding-left:18px; }
  details.chapter { padding:6px 0 4px; scroll-margin-top:150px; }
  .ch-head { min-height:44px; padding:8px 0; }
  .ch-head h3 { font-size:15px; }
  .ch-arrow { display:none; }
  .ch-desc { display:block; font-size:12.5px; color:#9A968B; margin:0 0 8px 2px; }
  .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:8px; }
  .item a { border:1px solid var(--line); border-radius:8px; background:#fff; padding:10px 12px;
    transition:border-color .15s, transform .15s, box-shadow .15s; }
  .item a:hover { border-color:#DCC5C4; transform:translateY(-1px); box-shadow:0 2px 10px rgba(34,34,31,.05); }
  .qno { font-size:11.5px; min-width:38px; }
  .qt { font-size:13.5px; }
  .note { display:block; font-size:12px; color:#9A968B; margin-top:2px; font-style:normal; }
  .wx-search { font-size:12.5px; padding:7px 12px; gap:8px; }
  .wx-mag { width:11px; height:11px; border-width:2px; }

  .side { display:block; position:sticky; top:76px; }
  .side-card { background:#fff; border:1px solid var(--line); border-radius:12px; padding:14px; }
  .sc-head { display:flex; justify-content:space-between; align-items:baseline;
    font-size:13px; font-weight:600; color:var(--red); }
  .sc-head span { font-size:10.5px; color:#B4B0A5; font-weight:400; }
  .sc-qrs { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin:12px 0 10px; text-align:center; }
  .sc-qrs img { width:100%; max-width:110px; border:1px solid var(--line); border-radius:8px;
    display:block; margin:0 auto 6px; }
  .sc-qrs b { font-size:11.5px; font-weight:600; }
  .sc-search { text-align:center; margin-top:4px; }
  .sc-note { font-size:11px; color:#88867D; line-height:1.65; border-top:1px dashed #EFEBE2;
    padding-top:10px; margin-top:10px; }
  .side-card .btn { display:block; text-align:center; margin-top:10px; font-size:12.5px; padding:9px 0; }

  .cta { margin:30px 0 0; padding:20px 22px; }
  .cta h3 { font-size:15px; }
  .cta p { font-size:12.5px; }
  .foot { font-size:12px; padding:32px 0 50px; }

  .sheet { bottom:auto; top:50%; transform:translate(-50%,-46%); border-radius:18px; opacity:0;
    pointer-events:none; transition:opacity .2s, transform .2s; }
  .sheet.on { transform:translate(-50%,-50%); opacity:1; pointer-events:auto; }
  .sheet-grab { display:none; }
}
</style>
</head>
<body>
<header class="topbar">
  <div class="wrap">
    <a class="brand" href="./"><i>罗</i>存储罗盘</a>
    <div class="top-search"><input id="q" type="search" placeholder="搜索 Q019 / NVMe / 灾备 / KV Cache" autocomplete="off"></div>
    <button class="icon-btn" id="searchBtn" type="button" aria-label="搜索">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="7"></circle><line x1="16.5" y1="16.5" x2="21" y2="21"></line>
      </svg>
    </button>
    <button class="top-cta" id="contactBtn" type="button">联系</button>
  </div>
</header>

<div class="sp" id="sp">
  <div class="wrap sp-in">
    <input id="qm" type="search" placeholder="搜索编号或关键词：Q019 / KV / 灾备" autocomplete="off">
    <button class="sp-x" id="spX" type="button">取消</button>
  </div>
</div>

<main class="wrap">
  <section class="hero">
    <h1>存储罗盘</h1>
    <div class="hero-side">
      <p class="lede">企业存储与 AI 基础设施的架构与选型判断。</p>
      <div class="stats">
        <span class="stat"><b>{{NS}}</b>系列</span>
        <span class="stat"><b>{{TOTAL}}</b>篇</span>
        <span class="stat"><b>100</b>问连载</span>
      </div>
      <p class="stat-sub">共 {{Q}} 篇 / {{CH}} 章 + {{AI}} 讲</p>
    </div>
  </section>

  <div class="layout">
    <div class="content">

      <!-- 手机首屏：横排双码卡 -->
      <section class="contact">
        <div class="contact-card">
          <div class="cc-col">
            <img src="{{QR_PERSONAL}}" alt="个人微信二维码">
            <div class="cc-txt"><b>加我微信</b><span class="cc-hint">回复「进群」</span></div>
          </div>
          <span class="cc-div"></span>
          <div class="cc-col">
            <img src="{{QR_WX}}" alt="公众号二维码">
            <div class="cc-txt"><b>关注公众号</b>
              <span class="wx-search"><span class="wx-mag"></span>存储罗盘</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 双层导航 -->
      <nav class="nav">
        <div class="tabs" role="tablist">
          <button class="tab on" type="button" role="tab" data-s="s1">企业存储 100 问</button>
          <button class="tab" type="button" role="tab" data-s="s2">AI 推理</button>
        </div>
        <div class="chip-row on" data-for="s1">
      {{CHIPS1}}
        </div>
        <div class="chip-row" data-for="s2">
      {{CHIPS2}}
        </div>
      </nav>

{{SERIES}}

      <p class="empty" id="empty">没有匹配的条目，换个关键词试试。</p>

      <section class="cta">
        <div><h3>存储选型、架构讨论、同行交流</h3>
          <p>全闪阵列、SAN / 灾备、信创存储与 AI 基础设施的一线信息，随时聊。</p></div>
        <button class="btn" id="ctaBtn" type="button">联系方式 →</button>
      </section>

      <p class="foot">© 2026 赵龙杰 · 中科曙光 FlashNexus · 公众号「存储罗盘」同步连载</p>
    </div>

    <!-- 桌面侧栏：吸顶联系卡 -->
    <aside class="side">
      <div class="side-card">
        <div class="sc-head">联系我 <span>滚动跟随</span></div>
        <div class="sc-qrs">
          <div><img src="{{QR_PERSONAL}}" alt="个人微信二维码"><b>加我微信</b></div>
          <div><img src="{{QR_WX}}" alt="公众号二维码"><b>关注公众号</b></div>
        </div>
        <div class="sc-search"><span class="wx-search"><span class="wx-mag"></span>存储罗盘</span></div>
        <p class="sc-note">加我后回复「进群」可入同行群<br>存储选型 / 架构 / 项目合作</p>
        <a class="btn" href="card/">查看完整名片 →</a>
      </div>
    </aside>
  </div>
</main>

<!-- 联系抽屉 -->
<div class="overlay" id="overlay"></div>
<div class="sheet" id="sheet" role="dialog" aria-label="联系方式">
  <div class="sheet-grab"></div>
  <div class="sheet-head"><h3>联系我</h3><button class="sheet-x" id="sheetX" type="button" aria-label="关闭">×</button></div>
  <div class="sheet-grid">
    <div class="s-col">
      <img src="{{QR_PERSONAL}}" alt="个人微信二维码">
      <span class="s-label">加我微信</span>
      <span class="s-sub">微信内长按识别</span>
    </div>
    <div class="s-col">
      <img src="{{QR_WX}}" alt="公众号二维码">
      <span class="s-label">关注公众号</span>
      <span class="wx-search"><span class="wx-mag"></span>存储罗盘</span>
    </div>
  </div>
  <p class="sheet-note">加我后回复「进群」可入同行群 · 公众号：搜一搜「存储罗盘」</p>
</div>

<script>
(function(){
  var tabs = [].slice.call(document.querySelectorAll('.tab'));
  var seriesList = [].slice.call(document.querySelectorAll('section.series'));
  var chipRows = [].slice.call(document.querySelectorAll('.chip-row'));
  var chapters = [].slice.call(document.querySelectorAll('details.chapter'));
  var items = [].slice.call(document.querySelectorAll('.item'));
  var chips = [].slice.call(document.querySelectorAll('.chip'));
  var empty = document.getElementById('empty');
  var sp = document.getElementById('sp');
  var qd = document.getElementById('q');
  var qm = document.getElementById('qm');
  var active = 's1';

  function isMobile(){ return window.innerWidth < 768; }
  function val(){ return (qm && sp.classList.contains('on')) ? qm.value : (qd ? qd.value : ''); }

  function showSeries(s){
    active = s;
    tabs.forEach(function(t){ t.classList.toggle('on', t.getAttribute('data-s') === s); });
    seriesList.forEach(function(el){ el.style.display = el.getAttribute('data-s') === s ? '' : 'none'; });
    chipRows.forEach(function(r){ r.style.display = r.getAttribute('data-for') === s ? '' : 'none'; });
    try { history.replaceState(null, '', s === 's2' ? '#ai' : '#q100'); } catch(e){}
  }
  function activeChapters(){
    var el = document.querySelector('section.series[data-s="' + active + '"]');
    return el ? [].slice.call(el.querySelectorAll('details.chapter')) : [];
  }
  function resetChapters(){
    activeChapters().forEach(function(d, i){ d.open = isMobile() ? i === 0 : true; });
  }

  /* 搜索过滤：跨系列检索，命中自动切 tab */
  function applyFilter(raw){
    var v = (raw || '').trim().toLowerCase();
    var hits = { s1:0, s2:0 };
    items.forEach(function(it){
      var hit = !v || (it.getAttribute('data-k') || '').indexOf(v) >= 0;
      it.style.display = hit ? '' : 'none';
      if (hit) {
        var sec = it.closest('section.series');
        if (sec) hits[sec.getAttribute('data-s')]++;
      }
    });
    if (v && hits[active] === 0) {
      if (hits.s1 > 0) showSeries('s1');
      else if (hits.s2 > 0) showSeries('s2');
    }
    chapters.forEach(function(sec){
      var any = [].some.call(sec.querySelectorAll('.item'), function(x){ return x.style.display !== 'none'; });
      sec.style.display = any ? '' : 'none';
      if (v && any) sec.open = true;
    });
    if (!v) resetChapters();
    empty.style.display = (v && hits.s1 + hits.s2 === 0) ? 'block' : 'none';
  }

  tabs.forEach(function(t){
    t.addEventListener('click', function(){
      showSeries(t.getAttribute('data-s'));
      resetChapters();
      applyFilter(val());
      window.scrollTo({ top:0, behavior:'smooth' });
    });
  });

  chips.forEach(function(c){
    c.addEventListener('click', function(){
      var d = document.getElementById(c.getAttribute('href').slice(1));
      if (d) d.open = true;
      /* 立即点亮所点章节，滚动落定后由 spy 校正 */
      chips.forEach(function(o){
        if (o.offsetParent === null) return;
        o.classList.toggle('on', o === c);
      });
    });
  });

  /* 章节滚动高亮 */
  function spy(){
    var y = 130, cur = null, list = activeChapters();
    list.forEach(function(d){
      if (d.style.display === 'none') return;
      if (d.getBoundingClientRect().top <= y) cur = d.id;
    });
    if (!cur && list.length) cur = list[0].id;
    /* 底部兜底：最后一章滚不到判定线，滚到底时点亮最后一个可见章节 */
    if ((window.innerHeight + window.scrollY) >= document.documentElement.scrollHeight - 2) {
      for (var i = list.length - 1; i >= 0; i--) {
        if (list[i].style.display !== 'none') { cur = list[i].id; break; }
      }
    }
    chips.forEach(function(c){
      if (c.offsetParent === null) return;
      c.classList.toggle('on', c.getAttribute('href') === '#' + cur);
    });
  }
  window.addEventListener('scroll', spy, { passive:true });

  /* 搜索输入（桌面顶栏 / 手机搜索层，双输入同步） */
  [qd, qm].forEach(function(inp){
    if (!inp) return;
    inp.addEventListener('input', function(){
      [qd, qm].forEach(function(o){ if (o && o !== inp) o.value = inp.value; });
      applyFilter(inp.value);
    });
  });

  document.getElementById('searchBtn').addEventListener('click', function(){
    sp.classList.add('on');
    if (qd && qd.value) qm.value = qd.value;
    setTimeout(function(){ qm.focus(); }, 60);
  });
  document.getElementById('spX').addEventListener('click', function(){
    sp.classList.remove('on');
    qm.value = '';
    if (qd) qd.value = '';
    applyFilter('');
  });

  /* 联系抽屉 */
  var overlay = document.getElementById('overlay');
  var sheet = document.getElementById('sheet');
  function openSheet(){ overlay.classList.add('on'); sheet.classList.add('on'); document.body.style.overflow = 'hidden'; }
  function closeSheet(){ overlay.classList.remove('on'); sheet.classList.remove('on'); document.body.style.overflow = ''; }
  document.getElementById('contactBtn').addEventListener('click', openSheet);
  document.getElementById('ctaBtn').addEventListener('click', openSheet);
  document.getElementById('sheetX').addEventListener('click', closeSheet);
  overlay.addEventListener('click', closeSheet);
  document.addEventListener('keydown', function(e){ if (e.key === 'Escape') closeSheet(); });

  /* 初始化：hash → 系列；手机只展开第一章 */
  var h = location.hash;
  if (h === '#ai' || h === '#s2') showSeries('s2');
  resetChapters();
})();
</script>
</body>
</html>
'''
    page = (page.replace('{{NS}}', str(n_series)).replace('{{TOTAL}}', str(total_all))
                .replace('{{Q}}', str(q_total)).replace('{{CH}}', str(q_chapters))
                .replace('{{AI}}', str(ai_total))
                .replace('{{CHIPS1}}', '\n        '.join(chips1))
                .replace('{{CHIPS2}}', '\n        '.join(chips2))
                .replace('{{SERIES}}', series1 + '\n\n' + series2)
                .replace('{{QR_PERSONAL}}', QR_PERSONAL).replace('{{QR_WX}}', QR_WX))
    open('index.html', 'w', encoding='utf-8').write(page)

    # ── README 同步 ──────────────────────────────────
    readme_list = '\n'.join('- [Q%03d：%s](%s)' % (n, t, b) for n, (st, b, t) in sorted(qs.items()))
    ai_md = []
    for gname, gdesc, items_ in AI_GROUPS:
        ai_md.append('#### %s\n' % gname)
        ai_md += ['- [%s %s](%s)' % (lab, t, u) for lab, t, s, u in items_]
    new_section = '''## 快速入口

- [在线阅读版](%s/)
- [联系方式 / 交流](%s/card/)
- [企业存储架构师 100 问](content/100-questions/README.md)

## 系列一 · 企业存储架构师 100 问（已发布 %d 篇）

%s

## 系列二 · AI 推理与存储（%d 讲，正文见公众号）

%s
''' % (SITE, SITE, q_total, readme_list, ai_total, '\n'.join(ai_md))
    old = open('README.md', encoding='utf-8').read()
    start, end = old.find('## 快速入口'), old.find('## 仓库结构')
    if start >= 0 and end > start:
        open('README.md', 'w', encoding='utf-8').write(old[:start] + new_section + '\n' + old[end:])

    print('index.html: %d 系列 / %d 篇内容（100问 %d 篇 %d 章 + AI %d 讲）；README 已同步'
          % (n_series, total_all, q_total, q_chapters, ai_total))


if __name__ == '__main__':
    build()
