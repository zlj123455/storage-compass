# Q007：容量、性能、可靠性、成本，别各选各的

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/A4EoVUBH3aKdihIc397vDA
> 发表时间：
> 迁移时间：2026-10-25

存储扩容方案评审会，投影上依次翻过四张表：容量、性能、可靠性、成本。每张表都找到了自己的"最优"。架构师没急着点评，只说了一句："把四张表叠在一起看看。"![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdXT8gqEkIbmrEIriczksicqX31x1VticCia4ic4nUxezxeju2E6G5x2iaHg9Iter8bqedR2jXFpib3Ksw8gzFicQHGr2JqekuI8ibfUjavI/640?wx_fmt=png&from=appmsg)

# 容量：买来的 TB 不等于能用的 TB

容量团队选了每 TB 单价最低的方案。架构师问了一个问题："如果一块盘坏了，重建的数据写到哪里？"没人接话。![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdVsQ88SFBkiazHF33hSEKuicbQOYU1mxQelXPnG8nvIu0gfxMok6HRXwYjLV5J1xBtwia39QTAY7xxsshncp3ztvBHs0JkG95cEDo/640?wx_fmt=png&from=appmsg)业务能用的容量，不等于硬盘标签相加。保护开销、元数据、增长缓冲、快照保留、故障恢复余量——都要从采购容量里扣。余量不是闲置，而是故障处理能力的一部分。没有地方接入恢复数据，业务可能被限速、中断或长期降级运行。只按"已用容量 + 增长率"采购，通常没回答：故障覆盖到哪一级、恢复允许多快、恢复期间业务能接受多少延迟。一句话理解：容量不是买多少 TB，而是故障时还有没有地方接住恢复的数据。

# 性能：干净环境下的跑分不算数

性能团队拿来了一份 IOPS 报告，数字很漂亮。架构师问："这是在什么状态下测的？""空闲，无后台任务，容量不到一半。"![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdVqP5VlT59YBMyODyWQyyaDcIibd6ckE8wnvXfa4VGftSkWB45licVwZaedAmQzuqSKyUwPBj5OvyIP0U5EOta2aF2jWa2ibcPqLg/640?wx_fmt=png&from=appmsg)干净环境下的低时延，不能证明高峰、后台任务和故障恢复同时发生时仍能满足业务。重建、数据回填都要和前台请求竞争资源——承诺恢复更快，往往需要预留更多资源；把资源全让给前台，恢复目标就要重新评估。业务真正购买的是高峰和故障期间都可接受的体验，不是一段无干扰的曲线。一句话理解：性能不是一条无干扰曲线，而是故障恢复期间还能不能达标。

# 可靠性：副本数量不等于保护能力

可靠性团队写了"三副本、双控"。架构师问："这三份副本跨了哪些故障域？""都在同一个机柜里。"![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdU3gJKLbQbibelCicqngD7o57gib23riaalpz4ian3YbTZOzZV8jia39kKEpUk9wh8uysOlRSUPLSCJZSb0SQ2WleEGepdLoBbAoTCFQ/640?wx_fmt=png&from=appmsg)单盘、控制器、机架、站点、误删除，不是同一种故障。RAID、副本、快照、备份各自只覆盖其中一部分。保护层数增加，往往会改变可用容量、写入路径和恢复时间。"数据很重要"不能直接转成技术配置，仍要落到恢复顺序、恢复点和恢复时限。可重建的临时数据可以接受较低保护等级；交易数据库的日志缺失可能无法接受——前者按后者配置是浪费，后者只靠"昨晚有备份"则把恢复风险留给业务。一句话理解：可靠性不是数有多少层保护，而是故障发生后能不能按目标恢复。

# 成本：每 TB 单价不是总拥有成本

成本团队对比了三家厂商的每 TB 单价，选了最便宜的。架构师在白板上画了一条三年时间线："第一年采购，第二年扩容，第三年故障没在目标时间内恢复——代价在哪里？"![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdUQibPQfvazaBKoANs9KiaObia3p2xn0ic6htBXjlZLNzibiaXTsHhIicVu8FicK8MJ8bePr1YSY1u0mT2WiapL4LoqXZiatbYke70RgKodE/640?wx_fmt=png&from=appmsg)采购价不是唯一成本。更高性能要付更高的介质和网络成本；更高可用性要付副本和演练成本；压低前期投入，可能把扩容频率和人工排障转移给运维。没有把三年内的增长、保护、扩容、订阅、运维和一次恢复失败的业务风险放进同一张账，就只能比较采购单。一句话理解：成本不是每 TB 多少钱，而是三年后业务为这个选择一共付了多少。

# 四件事必须在同一张表里验收

架构师把四张表叠在一起，在交叉处画了几个圈。![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdVWzKkMeNqhJZvRfr7G4XdnCIpI3ECxj5Iiccj4B4Z5g9j6QIiat7LJvplO2rcqHibJ7LxQ3e8qHvzrYYMEPxTWnsQbmZHoCKfQ6A/640?wx_fmt=png&from=appmsg)需要证明的事| 不能只看的数据| 还必须同时观察什么  
---|---|---  
容量够用| 原始容量、当前使用率| 保护开销、增长、热点分布、恢复余量与可扩展路径  
性能可用| 峰值 IOPS、平均时延| I/O 分布、P99、并发、元数据、备份/重建期间的业务体验  
故障可控| 副本数、控制器数量| 故障域、fencing、RPO/RTO、恢复顺序和演练证据  
成本合理| 每 TB 单价、初始采购额| 三年扩容、保护、网  
  
容量只填数据、性能只在空闲时跑、可靠性只看截图、成本只看第一年——四项即使分别"通过"，也不证明系统在真实高峰和故障时能兑现承诺。

# 从规格比较改成约束验证

架构师把 PoC 从"比较规格"改成"验证约束"。启动前先收集：数据量与增长、保留与可恢复范围、I/O 特征、并发与 P99 目标、正常与故障时的服务目标、RPO/RTO、三年成本边界。缺任何一项，不应急于要求厂商给出"推荐型号"。然后用同一套数据跑四类场景：![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdWyic0ITUkp7stKYBRBGU5aV2SvEBAweFd7Xd8dMrzubElgEVabKY8f1Be0K1yZicZ05DjMXUL7JAWz3PH2E4t61nvLW7yvJYkibs/640?wx_fmt=png&from=appmsg)

  1. 正常高峰下的真实请求分布；
  2. 备份、快照、复制与前台并发；
  3. 容量接近预警线时的扩容或重分布；
  4. 介质或节点故障后的降级、恢复与校验。

验收不只写"通过"，要记录每个场景的业务错误、P99、队列和恢复进度。这样得出的结论才是"这个方案适合这份业务承诺"。

# 什么时候可以简化

有人问："不是所有数据都需要这么复杂吧？"对可丢弃、可重建、单一团队使用且允许较长恢复的数据，确实可以选更低成本的方案——关键是业务已明确接受相应后果。但只要数据跨团队共享、承载交易或生产服务、需要跨故障域恢复，四项就不能再分开审批。最危险的不是"没买到最高规格"，而是用一份容量报价替代了一份业务承诺。容量、性能、可靠性、成本不是四个评分项，而是同一份业务承诺的四种投影。拆开各选各的，等于还没搞清业务要什么就开始比报价。
