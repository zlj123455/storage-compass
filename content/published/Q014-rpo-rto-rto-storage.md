# Q014：什么是 RPO 与 RTO，它们如何影响存储设计？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/w2y502iT3XIYiullDnWrHw
> 发表时间：
> 迁移时间：2026-10-25

主数据中心在上午十点零三分失去响应。监控先显示主机不可达，几分钟后，业务入口开始把新请求导向备用站点。业务方在事故复盘中问：副本不是都在吗？为什么恢复后少了十点零二分那笔订单？存储团队说：副本在，但"副本在"和"最后一笔没丢"是两件事。前者是 RPO，后者要验证。![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdVtdcYSP9NqRsOxLfFjnCQicbUwBI8ibiby3nfEE3ZVD3LofHgWn3hD20DI6sN3lpSjItXfDa12S6xTkktdz1pAufv09V4WIkHOtc/640?wx_fmt=png&from=appmsg)RPO 决定一笔写入在什么边界之后才算"丢不了"；RTO 决定备用站点需要预先准备多少资源、切换还剩多少人工步骤。它们直接决定复制模式、双活拓扑、网络、仲裁和演练方式。不要把 RPO 理解成"备份做得有多勤"。在站点灾难场景中，它应落到最后一笔可恢复的业务提交：

  * 

[code]
    实际 RPO = 故障时刻 − 幸存站点中最后一笔可一致读取的业务提交
[/code]

RTO 也不是某个卷从只读变为读写的耗时，而是从故障判定开始，到业务恢复验收通过的总时间：

  * 

[code]
    实际 RTO = 业务恢复验收通过时刻 − 故障判定起点
[/code]

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdXJ8vFZm1HrAuuo6HicsUqkfsVULJfxxwpBdcAvc2WlONYhAAZtyicnbEnfnLrdLCaiceSBZ8uw29gNic9ePWqFqVMdIBibgzqSQJibk/640?wx_fmt=png&from=appmsg)同一套阵列，换一种部署方式，答案完全不同。一句话理解：RPO 不是备份频率，是最后一笔可恢复提交距故障的时间差；RTO 不是卷切换耗时，是业务恢复验收通过的总时间。

# 异步主备：接受一个明确的丢失窗口

最常见的异地灾备是主备复制：生产站点 A 的 LUN 按周期把增量复制到站点 B。异步复制先由 A 向业务确认写入，再在后台传变化；有些实现以快照差异作为增量来源。![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdXdY6METMbxDA5icFpX8ubOISQsWkQCkow4xBz1dfy41SZHsVgN9OgRXx4s7DGtoKibfN8qdiaXemicf1USmqP2JcbhCibMuFc8eK04/640?wx_fmt=png&from=appmsg)好处是写入不必等远端确认，站点可以拉得更远，对生产时延影响小。代价也明确：故障发生时，B 只有最近一次完成同步的恢复点。同步周期设为五分钟，不等于 RPO 一定是五分钟——同步积压、链路带宽不足、初始同步未完成，都会让最后可接管点更早。RTO 也不只取决于复制速度。A 站点失效后，团队还要断开复制关系、提升 B 的读写角色、让主机访问备用 LUN、启动数据库与应用、检查消息消费位置、切换入口流量。若这些动作依赖人工手册，RTO 的主要组成往往不是"数据已经在 B"，而是"谁在什么时候确认可以接管"。一句话理解：异步主备的关键不是选"异步"两个字，而是把允许的丢失窗口写清，并持续监测它是否真的被守住。

# 同步主备：把远端确认放进写入路径

同步复制改变了确认点。业务写入到达 A 后，存储同时向本端与 B 发起写入，双方按约定完成才向主机返回成功。主站点突然消失时，已确认的写入也应位于 B 的可接管副本中，目标 RPO 可以压得很低。![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdV2BwPCEyJNHXLO8J0CCmHKtALZvs82do6w35UkXSickLZ87IMp8Zgnotp0JQFgB5FE5yb20Y9McEo5icdP362zrENp7vPOXrkek/640?wx_fmt=png&from=appmsg)同步复制不是一句"零丢失"的承诺。它把跨站点链路的往返时延、抖动和远端状态放进了业务写入路径。链路质量变差时，交易写入变慢；链路中断时，更困难的决策出现了：

  * 让 A 继续单写，业务可用性好，但这段新写入不再具备站点级保护；
  * 停止写入，保护原定 RPO，却把压力转移到业务可用性和 RTO。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdXJTibRkiaAiaibicxzqBcvYo7WOCaficJEHt5ckBGQ8xZe8krDe7Jk1bpdurU12wDqbuZDNKumf6Vw0brYZeOX8KU5gM4b9oOLG9Cmg/640?wx_fmt=png&from=appmsg)不是产品参数能替代的架构选择。方案必须明确：复制 Pair 出现中断或异常状态时，业务还能以什么保证继续写；监控该在多久内告警；恢复同步之前，是否允许把"RPO 接近零"继续写进服务承诺。另一个常被遗漏的条件是一致性组。一个数据库往往把数据、日志、临时文件放在不同 LUN。若分别复制、分别接管，单个卷都"同步成功"也可能拼不出一个可启动的数据库。关联 LUN 必须以一致性组进入同一复制与切换边界。一句话理解：同步复制不是零丢失的承诺；链路中断时"继续写还是停止保护"是架构决策，一致性组是不可遗漏的前提。

# 两地双活：缩短切换链，但把仲裁变成核心组件

两地双活不是"在 B 再放一份副本"。它让两端 LUN 都能向主机提供读写服务：读取通常优先走本地，写入则需同时处理两端。一种典型的存储双活实现会在写入前取得对应区间的锁，再把 I/O 并行写到本地和对端，双端完成后才返回主机。这解释了双活为什么能让已确认写入拥有更强的站点级保护，也解释了它为什么对链路时延、网络质量和写入冲突更敏感。![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdVickpnPUDIw1BbpQOhqXp8EdcprVbwh6HK1DtTMj00ee0RuOG6UKLOO0y5Xw212uyibxXjLIxNogWEPY77PXR7RuN1jl5ickC5YE/640?wx_fmt=png&from=appmsg)双活最容易被画漏的是第三方仲裁。站点间链路断开时，A 看不到 B，B 也看不到 A；若双方都继续接收写入，数据将分叉，这就是 split-brain。仲裁的任务不是"提高性能"，而是确定谁被允许继续写服务，谁必须停止。优先站点模式、单仲裁或双仲裁是不同取舍，但都要求把故障顺序写入演练：站点故障、链路分区、仲裁不可达同时发生时，哪一侧能继续，哪一种组合需要人工强制启动？![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdV2kJs1CKcwC54YLUT5cXib4UtIJqUtl6Q6NJqKw1G2hI5ibNJXbeYSia07JwzwsDTuicLibtCiaqribDtMnfkTFHceqTRLMibW9PBlyQc/640?wx_fmt=png&from=appmsg)业务网络、阵列间复制网络和仲裁网络不能只在图上画成三根线；它们应有独立的链路、冗余和故障验证。失去 A 后，B 是否能承受全量流量，也必须在切换演练中验证。否则入口即使很快切过去，P99 时延和错误率仍可能把"RTO 很短"变成假象。一句话理解：双活能把 RTO 和 RPO 压得很低，但不意味着任何故障组合下都是零；仲裁和全量负载验证是不可跳过的环节。

# 方案评审时，别先问产品，先把这张表填完

要回答的问题| 直接影响的设计  
---|---  
要抵御主机、机房还是区域故障？| 副本与仲裁必须跨越的故障域  
最后一笔不可丢失的业务提交是什么？| 同步/异步复制、确认语义和一致性组  
允许中断多久，计时从哪里开始？| 备用资源、自动化、切流与验收流程  
站点间链路断开时谁可继续写？| 仲裁、fencing 与降级服务策略  
失去一个站点后谁承受全量负载？| 计算、网络、存储性能余量  
误删或逻辑损坏怎么办？| 快照、PITR、不可变备份与恢复演练  
  
RPO 和 RTO 最终不是写在招标书上的两个数字，而是一次故障发生后能被拿出来核对的事实：最后一笔订单是否还在、失效侧是否已被隔离、备用站点多久开始正确处理业务、全量负载下是否仍稳定。一句话理解：灾备设计不是选"支持复制"或"支持双活"，而是把故障后的核对事实提前写清。
