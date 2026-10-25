# Q044：分层存储何时有效，何时只会增加运维负担？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/z6wHftiFuE5f2AIdIKcY2Q
> 发表时间：
> 迁移时间：2026-10-25

假设一个数据库卷位于自动分层池：高速层有空闲，平时延迟也正常。一次批处理改变了工作集，数据库 P99 先升高，系统过了一段时间才把新热点搬到高速层；搬移开始后，后台 I/O 又与业务争抢带宽。

问题不一定是高速介质不够，而可能是策略追不上业务。

分层只有在数据温度可识别、变化速度慢于策略响应、迁移成本低于收益，而且策略可观察、可固定、可回退时才有效。否则，它只会增加延迟波动、后台流量和排障层次。

本文主要讨论块和文件存储中的自动数据放置。对象访问层和归档层可以借鉴同一判断框架，但访问与恢复语义不同。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdXpvIWgfaHEJSJgVlmBX5jvjnsL0Xe39ywUyQCuGyMrGJ3icjC91l0ZXv0IbIXM6vMticqR2v5pp4yZl2Qnibajn5zTJM5N662VtQ/640?wx_fmt=png&from=appmsg)

# 分层不是把快盘和慢盘放进同一个池

SNIA 把自动存储分层定义为：依据策略，在不同存储层之间自动移动数据。层可以位于同一系统，也可以跨系统或云服务。

真正的机制是一个闭环：观察访问，判断冷热，移动数据，再观察结果。只要其中一环不可见，管理员就无法解释“为什么它现在位于这一层”。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdUH4v2U0Rwmv8NUg8Jiajh7sN2hQCn7JHr4dQzftcW80uiciatApzJqQgt2cj8ODPhUmg7saZpHWgfJabxoRsrqnEMicm7L9jiaSz1Q/640?wx_fmt=png&from=appmsg)

# 先区分分层、缓存和归档

分层通常改变数据的主要放置位置；缓存则要回答高速层保存的是副本还是脏数据、未命中时从哪里读取、故障后如何恢复。Linux dm-cache 明确区分 origin、cache 和 metadata，并让策略决定哪些块何时迁移。

归档又不同。某些对象归档层需要先发起恢复并等待，不能当成延迟稍高的在线容量层。名称里都有“层”，SLA 却可能完全不同。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdXiamxDtbjfMVBkTjBGgicpvozjgicFq9KiceCDnjes40D90LV8uUCwdUHswiaaVKicmNiaXFP3u4SUlwjPibIxvEakfBHUFohwicfKzxic8/640?wx_fmt=png&from=appmsg)

# 分层有效，需要四个条件

工作集要相对稳定，让热点在被识别和搬移后仍然保持热；迁移粒度要匹配热点范围，避免只热一小段却搬走更大的数据单元；高速层要有容量，数据面也要留出迁移带宽；策略还要能显示、暂停、固定对象并回退。

这四个条件缺一个，最终命中率看起来不错，也可能只是业务高峰结束后的“正确答案”。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdX5eIYHaHxHeSuzT162z6KkrOALbkLWv6flpzSydmzj1EjgNBqmAOr8IORz3vU1BKfCECDThmuRXaSEMEoXz2JZV1PY8CWED4E/640?wx_fmt=png&from=appmsg)

# 观察窗口和粒度决定能否追上业务

IBM 的 Easy Tier 文档展示了一个典型实现：系统按 extent 收集热度，再形成迁移计划。其特定版本还说明，较大的迁移单位和较长的分析窗口可能把短时热点或局部热点平均掉。

这些数字不是行业标准，但问题具有普遍性：热点持续多久？系统多久识别一次？一次搬多大？如果工作集变化比策略更快，分层永远在追昨天的热点。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdWxc061uHKRx6iaWyIDqI5icwLPJsGcVaqCJkmzCtz23O2GAjibX7iaoGQxUoDuDs3a54pG0fXjBnKMNJ5slz7u8L489kczzG90M8o/640?wx_fmt=png&from=appmsg)

# 后台搬移也会进入资源预算

数据迁移要读旧层、经过控制器或网络，再写入新层。IBM 文档也明确提示，提高自动迁移速度可能让现有工作负载出现更高延迟和更低带宽。

所以我不会只看“多少数据进入高速层”，还会同时看迁移量、队列、控制器与网络占用、前台 P99，以及迁移完成后收益维持了多久。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdUgjEXhqLDCcJCeRZWH6ApQoicNYFZHcPSI6axQyyfcIibmgxvfK86r0agdp9ukT5xHquXf3JRbn8YXNibTjoy5hU5taEwpPKL8EY/640?wx_fmt=png&from=appmsg)

# 策略震荡会把优化变成持续搬家

当数据刚提升就变冷、刚降级又被访问，系统可能反复迁移。成熟实现通常会用冷却期、阈值或滞回减少震荡，但具体规则必须核对产品版本。

关键业务、日志顺序写、备份窗口和月末批处理不一定适合完全自动判断。需要固定到某一层的对象、例外规则和人工干预权限，都应进入设计，而不是等故障时临时寻找开关。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdWmgvsTSV0e3tD64KeSDjIyqon00afZbNxCiaoQddoDazaLvpRQ52qcBYsicFP1MJ2qpICdTwBnVZmWXMiaQhzfPmRib5LzPG8NYOM/640?wx_fmt=png&from=appmsg)

# PoC 要验证策略响应与回退

测试至少覆盖稳定热点、突然改变的工作集、随机与顺序混合、快速层接近满载、业务高峰时迁移、层级设备或路径故障、暂停策略以及恢复自动管理。

每轮记录热点识别时间、迁移量、层级驻留、前台 P99、后台队列、告警和回退结果。对象归档还要单独验证恢复等待；AWS 文档显示，可选归档访问层需要显式恢复并等待，不能套用在线层结论。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdUuAxbGtZjHXoJ3Js4YgicHNCGY1Vgll0ib8zd1okJjDWyicmqzWlbkXkEgQ2098Aicaia9948f3dM6nK9YFrJp4zicRCub1s2orB0TM/640?wx_fmt=png&from=appmsg)

我的验收标准不是“系统能自动搬数据”，而是团队能解释为什么搬、何时搬、搬移是否伤害前台业务，以及判断错误时如何固定和回退。Q045 将把这些层继续串起来，画出一条业务 I/O 的端到端路径。
