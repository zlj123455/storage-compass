#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成存储罗盘站点首页 index.html + 更新 README 文章目录。
用法:  python tools/build_site.py   （在 storage-compass 仓库根目录运行）
"""
import os, re, glob, html, subprocess

PUB = 'content/published'
REPO = 'https://github.com/zlj123455/storage-compass'
BLOB = REPO + '/blob/main/content/published/'
SITE = 'https://zlj123455.github.io/storage-compass'

# AI / KV Cache 系列（正文在公众号，站内只做目录与跳转）
AI_SERIES = [
    ('第1讲', '模型为什么不能直接给答案？一次推理请求的完整旅程',
     '从 prefill 到 decode，看清一次请求的时间都花在哪', 'https://mp.weixin.qq.com/s/IUrhhro7XZYgFW6R-T7RBg'),
    ('第2讲', 'KV Cache 到底缓存了什么？',
     'K/V 张量是什么、为什么随序列长度线性膨胀', 'https://mp.weixin.qq.com/s/FvR--NyGDy0eMbFVmLFlaQ'),
    ('第3讲', 'KV Cache 装不下了，为什么显存和推理延迟同时告急？',
     '显存不足如何传导为延迟与并发的双杀', 'https://mp.weixin.qq.com/s/iweY7rpUYspn1GGxjUVURg'),
    ('第4讲', 'KV Cache 不够用了，究竟有几类解决办法？',
     '驱逐、量化、共享、下沉：每条路的代价', 'https://mp.weixin.qq.com/s/ZxsIfohvzl8w7VxxIaPDMw'),
    ('第5讲', 'KV Cache 能不能放到 SSD？答案不在 SSD 有多快',
     '落盘的真正瓶颈是带宽之外的访问模式', 'https://mp.weixin.qq.com/s/0FGCsdislK28xeRNQYtjhA'),
    ('第6讲', '企业级推理架构，先做 PD 分离，再做存算分离',
     '两件事的先后顺序与各自的收益边界', 'https://mp.weixin.qq.com/s/Swm9M_wLfoYLKK9FVFX75A'),
]


def git_time(f):
    try:
        return int(subprocess.check_output(
            ['git', 'log', '-1', '--format=%at', '--', f], text=True).strip() or 0)
    except Exception:
        return 0


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
        stamp = git_time(f)
        if num not in arts or stamp > arts[num][0]:
            arts[num] = (stamp, b, title)
    return [(n,) + arts[n][1:] for n in sorted(arts)]


def build():
    qs = collect_questions()
    q_items = '\n'.join(
        '      <li><span class="qno">Q%03d</span><a href="%s%s" target="_blank" rel="noopener">%s</a></li>'
        % (n, BLOB, b, html.escape(t)) for n, b, t in qs)
    ai_items = '\n'.join(
        '      <li><span class="qno">%s</span><a href="%s" target="_blank" rel="noopener">%s</a>'
        '<i class="note">%s</i></li>' % (k, u, html.escape(t), html.escape(s))
        for k, t, s, u in AI_SERIES)

    page = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>存储罗盘 · 企业存储与 AI 基础设施</title>
<meta name="description" content="面向企业架构师、IT 负责人和存储选型团队的公开知识库，聚焦企业存储架构、可靠性、性能与选型判断。">
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:-apple-system,"PingFang SC","Microsoft YaHei","Segoe UI",sans-serif; background:#FAF9F6; color:#2C2C2A; line-height:1.7; padding:40px 20px 60px; }
main { max-width:760px; margin:0 auto; }
h1 { font-size:24px; font-weight:500; }
h1 .en { color:#B01F24; }
.sub { color:#6B6A66; font-size:14px; margin:8px 0 8px; }
.meta { color:#B4B2A9; font-size:12.5px; margin-bottom:22px; }
.card { background:#fff; border:1px solid #E8E5DE; border-radius:12px; padding:20px 22px; margin-bottom:16px; }
.card h2 { font-size:15px; font-weight:500; color:#B01F24; margin-bottom:4px; }
.card .desc { color:#888780; font-size:13px; margin-bottom:10px; }
ol { list-style:none; }
li { padding:6px 0; border-bottom:1px dashed #EFEBE2; font-size:14px; }
li:last-child { border-bottom:none; }
.qno { display:inline-block; min-width:52px; color:#888780; font-size:12.5px; }
.note { display:block; color:#888780; font-size:12.5px; font-style:normal; padding-left:52px; margin-top:2px; }
a { color:#185FA5; text-decoration:none; }
a:hover { text-decoration:underline; }
.foot { color:#B4B2A9; font-size:12.5px; text-align:center; margin-top:24px; }
</style>
</head>
<body>
<main>
  <h1><span class="en">存储罗盘</span> storage-compass</h1>
  <p class="sub">面向企业架构师、IT 负责人和存储选型团队的公开知识库，聚焦企业存储架构、可靠性、性能与选型判断。</p>
  <p class="meta">已发布 {{QN}} 篇 / {{AIN}} 篇 · 持续更新</p>

  <section class="card">
    <h2>企业存储架构师 100 问</h2>
    <p class="desc">从原理到选型判断的连续追问，每篇给结论、机制、取舍与适用边界。</p>
    <ol>
{{QITEMS}}
    </ol>
  </section>

  <section class="card">
    <h2>AI 推理与存储 · KV Cache 六讲</h2>
    <p class="desc">从一次推理请求的旅程讲到企业级推理架构的落地顺序（正文在公众号「存储罗盘」）。</p>
    <ol>
{{AIITEMS}}
    </ol>
  </section>

  <section class="card">
    <h2>交流</h2>
    <p style="font-size:14px">存储选型、架构与同行交流 → <a href="card/">赵龙杰 · 联系方式</a></p>
  </section>

  <p class="foot">© 2026 赵龙杰 · 中科曙光 FlashNexus · 公众号「存储罗盘」同步连载</p>
</main>
</body>
</html>
'''
    page = (page.replace('{{QN}}', str(len(qs))).replace('{{AIN}}', str(len(AI_SERIES)))
                .replace('{{QITEMS}}', q_items).replace('{{AIITEMS}}', ai_items))
    open('index.html', 'w', encoding='utf-8').write(page)

    readme_list = '\n'.join('- [Q%03d：%s](%s)' % (n, t, b) for n, b, t in qs)
    ai_md = '\n'.join('- [%s %s](%s)' % (k, t, u) for k, t, s, u in AI_SERIES)
    new_section = '''## 快速入口

- [在线阅读版](%s/)
- [联系方式 / 交流](%s/card/)
- [企业存储架构师 100 问](content/100-questions/README.md)

### 企业存储架构师 100 问（%d 篇）

%s

### AI 推理与存储 · KV Cache 六讲（%d 篇，正文见公众号）

%s
''' % (SITE, SITE, len(qs), readme_list, len(AI_SERIES), ai_md)

    old = open('README.md', encoding='utf-8').read()
    start, end = old.find('## 快速入口'), old.find('## 仓库结构')
    if start >= 0 and end > start:
        new = old[:start] + new_section + '\n' + old[end:]
        open('README.md', 'w', encoding='utf-8').write(new)

    print('index.html: %d 篇 100 问 + %d 篇 AI 系列；README 已同步' % (len(qs), len(AI_SERIES)))


if __name__ == '__main__':
    build()
