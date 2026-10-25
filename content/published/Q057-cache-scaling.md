# Q057：缓存命中率与工作集如何指导性能扩容？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/yfxp08QiR6NvrCWvAtacyA
> 发表时间：
> 迁移时间：2026-10-25

假设月末报表查询突然变慢。团队发现缓存命中率下降，准备加大缓存。另一位工程师却问：是哪一层没命中？新增空间能把哪些等待消掉？

命中率变化是排查线索，却不能直接开出扩容清单。先看目标业务窗口内的工作集与数据复用，再用未命中负载和业务响应验证收益，才能判断钱该花在缓存还是后端。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdWzkDsLf2cwq79GJOF1icchZqnaGiaEzy9IQXibyiaJPnaicawfuX9RwDn4sT1E433sUumZ53XDZjqGpnN3Pb4ZvViaLY3Pzx0wWpCrM/640?wx_fmt=png&from=appmsg)

# 命中率低，低的是哪一层？

一次查询可能经过数据库缓冲区、主机页缓存和阵列缓存。数据库里没命中，不代表数据一定从盘上读回：主机缓存仍可能满足它。PostgreSQL 官方统计就明确区分了数据库缓冲命中与操作系统缓存。

因此，不能把不同层的命中率互相代替。还要看分母按请求、数据块还是字节计算，时间窗口是否一致。若指标是累计计数，应使用这段时间的增量，并排除计数重置的影响；历史总比例可能淡化月末的变化。

比例之外，更重要的是每命中的访问有多少。做一个纯算术假设：某一层每秒收到 1,000 次查找，命中率为 90%，就有 100 次未命中；同样比例下，查找增加到 10,000 次，未命中就变成 1,000 次。这是该层的访问计数，不是设备物理 IOPS。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdVSLbb7Uyg4Gf3nBZUZ1S808ncemz1mFicb9gEFTuMrrDRgmMfzSMOtVNFuibeP1tOvU7EUrqLtVcqLLjM9iabFpgbPibIxKUDmGs0/640?wx_fmt=png&from=appmsg)

# 工作集不是整个数据库

月末可能只集中访问近期订单和几个索引，历史数据仍占着大量磁盘空间，却不在这段查询的主要路径上。按全库大小配缓存，容易把“存了多少”误当成“这一轮需要反复读取多少”。

工作集是在某段业务窗口内活跃访问的数据。白天交易与夜间报表的窗口不同，工作集也可能不同；一张当前缓存占用截图，并不能说明数据被淘汰后是否马上又会用到。

真正影响扩容收益的是复用。如果这批数据再次被读取前，已经被其他访问挤出缓存，就可能反复淘汰、再读回来。更多可用缓存有机会保住它，但仍需核对缓存策略和访问记录。

反过来，某次扫描只读一遍，读完短期内不再访问，扩大缓存未必能减少这轮的读取。工作集可以很大，却缺少值得长期保留的复用；“数据活跃”和“加缓存有效”不是同一个判断。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdVTwia6GGOib0tgqnRiaZiaUpKwX326cWwxOLn5pDXnyq6m66pvPKrFIJfHBwruKic7MjJ0735ZYILgJvJLgGVekTFEicL8RhhshIsVw/640?wx_fmt=png&from=appmsg)

# 先问：新增空间会减少哪些未命中？

回到月末查询。若未命中的主要是反复使用、刚被淘汰的数据，缓存容量不足就是一个值得测试的假设。若主要是第一次读入的新数据、被策略旁路的访问或低复用扫描，加大容量也未必解决问题。

我会在隔离测试环境里对齐请求组成、目标负载和起始状态，逐步改变同一层的可用缓存，同时记录实际吞吐、未命中负载、后端等待和业务完成时间。不能拿预热后的结果，对比另一轮冷启动成绩，就宣布扩容有效；吞吐减少导致的等待下降，也不能算缓存扩容的收益。

假如缓存继续增加，业务收益已经很小，就需要追问剩余等待在哪里。曲线变平不证明测出了精确工作集，也不保证每种负载都有清晰拐点。缓存块粒度、替换策略和热点变化，都会影响可用空间的实际效果。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdVgPbmVa0wjjXCCVk3Aib3ibgPHsuv6ogtNgN4eqZqUVarAdrMhS3x0yElxr9rLUXJWicglR8PeicAE2tfq6VBe9RSqn5oe1MHic7OY/640?wx_fmt=png&from=appmsg)

# 写缓存变大，持续写入就能更快吗？

读缓存靠复用减少下层访问，回写式写缓存则能先承接一部分写入，再由后端写回。短时突发过去后，后端若能排空积压，增加缓存可能有价值。

但如果进入缓存的新脏数据负荷长期超过有效写回能力，积压仍会增长。更大的缓存可能只是让压力晚一点暴露，并没有补上后端的持续处理能力。

所以要分开看脏数据积压和写回速率，不能用一个“写命中率高”证明持续写入已经够用。不同缓存模式的确认语义也不同；不能为了成绩而降低原有持久化条件，缓存保护与故障后行为仍需验证。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdX677N364ticKTSqgsCClicLqQAzKZDH8eewkVfx0IR7dfic7iaGyhEjSfFhqZ1uLycGicwFPeiaZq6mQoPRsegibJFicLibRC0szVZggzM/640?wx_fmt=png&from=appmsg)

# 最后决定，扩的是缓存还是别处

有复用、反复淘汰，并且扩容确实减少关键未命中等待，才有较强证据支持加缓存。低复用读取或持续写回受限，则要评估后端吞吐、数据布局，或者应用访问方式；已经命中却仍慢，就继续追查其他等待。

缓存也有成本。应用内存与主机缓存可能共享同一份内存预算，增加一边可能挤压另一边。热点迁移、重启或故障后缓存变冷时，后端能否承受负载，也不能靠温热状态下的命中率承诺。

对这次月末报表，我要看到的不是一个更高的百分比，而是新增空间保住了哪些会再次使用的数据、减少了多少下一层访问，又让哪些查询更早完成。缓存统计与保护能力依具体实现，生产系统的冷缓存实验也需要先评估影响。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdVickQZ7KyF51WPgJRS9UoyJKjbV5s4oV0mfYFBe78Ixn47NmQ9IKEib2OgUctEoMv1dXoGKWof14bHOlLmW5oFbu74SeshNTxRA/640?wx_fmt=png&from=appmsg)  
文章讲的是通用判断方法，落到具体环境，还要结合业务负载、现有架构和实际约束。如果你正在处理企业存储相关问题，欢迎扫码添加我交流；想参与同行讨论，也可以添加后回复「进群」。![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdX1hxGcZ5HSXicKvTtsQ77a2etOjvkXFQnwiazs3AzVt7ZCibNFicuRZYWY8xBLMMGwatl6A9eYwEy3HlFOoxy9dFgFFc3usQ1DQbk/640?wx_fmt=png&from=appmsg)
