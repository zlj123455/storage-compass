# Q009：同样 100TB，为什么存储价格差这么大？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/SB6HNgOCC2-DdLJ4rxepGA
> 发表时间：
> 迁移时间：2026-10-25

存储供应商演示会，两家厂商轮流上台。A 厂商报价低，B 厂商高出不少，容量都写着 100TB。有人小声问，两份报价都是 100TB，为什么不能直接比单价？架构师坐在台下，说了一句："先看每份报价到底交付了什么。"![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdWSbXHLiag8ZfTlHjZdWc9uFdPU36NwaBRsIgcYLlmxGFOjQAOZt2krkzy8wiasibzbbWYSDBP76tFAjXJia7gECLfNuMAr5CxdJ6s/640?wx_fmt=png&from=appmsg)

# 把"100TB"翻译成人能核对的话

A 厂商写的是设备装进去的原始容量，B 厂商写的是扣除保护空间后的可用容量，还有的把压缩、去重等前提下可能得到的效果也放进了口径——这就是有效容量。架构师举手问，报价写 100TB，业务真的都能用吗？A 厂商的人说，这些数字都可能出现在报价里。架构师说，但它们不是同一个数字。采购前要追问的是：保护、预留、快照和增长空间扣除后，业务真正能用多少？依赖压缩或去重的话，什么样的数据才能达到预期？先把容量口径写进验收条件，单 TB 单价才有可比性。![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdUqT8LMZ5QOnicGrDVMgowculxAXzCyxGsqR4iaAWwyZVlUrPrZX6JAsat7BgwKma2HJwUpwoh3XcNIDscMGKdjk3Hd2H9NKhO8w/640?wx_fmt=png&from=appmsg)一句话理解：100TB 可能分别是原始容量、可用容量或有效容量，不追问口径，每 TB 单价就没有意义。

# 价格里常常买的是"高峰时仍然可预测"

轮到性能演示，两家都亮出了规格表上的 IOPS 数字。架构师问，这是在什么状态下测的？厂商回答，空闲环境，无后台任务。架构师说，平时访问不多时许多方案看起来都够用，差异往往出现在月底结账、批处理、多人同时访问，或后台任务突然挤进来的时候。此时业务感受到的不是最高 IOPS，而是页面是否卡顿、数据库请求是否排队、共享目录是否变慢。能否隔离不同业务、缓存怎样处理突发写入、系统是否会出现尾延迟，都会改变体验。不要只测空载，让候选方案在真实混合负载下运行，再看高峰期的排队和失败重试，才是在比较业务体验。![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdVH0jzicMlItibGVDfOFsCAlibLyRbibEHaqooIGJ4p7Swf3ib4hic9oembrXLiaxRqYZcaSJYeS7Chf3oKSuy3ia221ciacXalLwxMXg6o/640?wx_fmt=png&from=appmsg)一句话理解：价格差异的一部分，买的是高峰时仍然可预测的体验，不是空载跑分。

# 故障发生时，配置差异才真正显形

B 厂商展示了双控、多路径、故障隔离等冗余配置，A 厂商的方案更简单。架构师问了两家同一个问题：平时都能读写，出问题还一样吗？要验证的不是口号，而是三个场景——路径异常时业务会不会中断？部件故障时谁来隔离风险？恢复演练时多久能完成、由谁操作？两套设备平常都能读写，不代表故障后仍会以同样的方式服务。价格差的一部分，来自冗余路径、控制器设计、保护策略、重建能力和恢复工具——为了把"发生故障"变成可预期、可验证的恢复过程。能恢复，才是可验证的承诺。![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdWHzvQO1ZhdtsgtHkDHlvAyO1XLD9LTuiaQ2e2CWzjFJmtzU9uHDls2LufJWUSyGNzXOLPL2Is3H1BrZrQDSDbZaeS3CszweAtg/640?wx_fmt=png&from=appmsg)一句话理解：平常都能读写不算数，故障后的恢复路径和边界才是价格差异的来源。

# 一次采购价，不是三年总成本

演示进入服务条款环节。架构师在笔记本上画了一条三年时间线：第一年采购，第二年扩容与支持，第三年迁移与升级。起始报价低，是不是就更划算？不一定。扩容方式决定一次买多少，软件与支持决定哪些已包含，升级与迁移决定谁承担风险。架构师说，他的做法是把报价拆成一张"承诺清单"：容量口径、目标负载、故障场景、恢复目标、扩容方式、服务边界，逐项写进验收条件。把钱花在哪里写成清单，比单看一个总价更容易看出差异。![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdWTcvNayic0GwYejSIvibBGdLqg660fNWqzo5CanSvZIjWg3ugw0mv0ZOIXFaGH2vXVCAia5UbLicdUhjlD2Bn5FQCa7yfWslvKj1Q/640?wx_fmt=png&from=appmsg)一句话理解：比的不是采购总价，而是三年内扩容、保护、运维和一次恢复失败的综合代价。

# 最后，用四个问题让报价可比

演示结束后，架构师把四个问题写在白板上——先让承诺变得可核对，再比较价格：

  1. 容量口径：这 100TB 到底怎么计算？是原始、可用，还是依赖特定前提的有效容量？
  2. 高峰负载：在我们的混合负载下，怎样验收体验？响应时间、排队和资源隔离如何达标？
  3. 关键故障后：任一部件或路径失效后，业务怎样恢复？恢复在哪个环境完成、要多久、由谁操作？

三年成本：扩容、许可、支持、迁移和三年运维成本，哪些已经包含？存储价格差异，往往不是因为容量不同，而是因为"出问题时谁来承担不确定性"不同。对可重建、访问稳定、故障影响有限的业务，简单方案可能就是正确选择；对停顿和恢复代价很高的业务，便宜方案也可能把成本推迟到了事故发生之后。![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdVCKU935F5P1libhYFQtotThOop6xH2w4X21dqpxibzUZXB7UK7ianQRU2Q27t399Mx08yJM4eFlhUOo1Nic094NgQESZQDEObsicXY/640?wx_fmt=png&from=appmsg)
