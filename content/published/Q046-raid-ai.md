# Q046：RAID 5、RAID 6 和 RAID 10 如何取舍？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/dz7wUl0r8cIPrUwGZ5scJQ
> 发表时间：
> 迁移时间：2026-10-25

假设一次存储方案评审里，容量团队倾向 RAID 5，理由是可用空间更多；数据库团队坚持 RAID 10，担心随机写延迟；运维团队则认为 RAID 6 能多承受一次磁盘故障，所以最安全。

三种说法都只说对了一部分。

RAID 的取舍不能只看“能坏几块盘”，而要同时看写入路径、容量效率、故障组合、降级性能和重建窗口。真正的答案不是一个级别名称，而是业务能否接受它在故障期间的表现。本文讨论经典 RAID 5、RAID 6 和镜像对组成的 RAID 10；现代阵列的缓存、分布式备用空间和数据布局可能改变实际结果。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdWN0ElvlAq8ZAzl93f4ib8zCp3AgJlLhN7QVrQcagEOG4D8QeNBrtsJMeJbIh7yUt3fb438EZLNtMYE3tCGQgXXIkI1stWvJdcE/640?wx_fmt=png&from=appmsg)

# 先看三种布局如何保存冗余

RAID 5 在一个条带组中保存一份分布式校验，可承受任意一块成员盘失效；RAID 6 保存两份独立校验，可承受任意两块成员盘失效；RAID 10 则把数据写入镜像对，再跨镜像对条带化。

SNIA 将 RAID 5、RAID 6 分别归为单校验和双校验，将 RAID 10 归为镜像组条带。它们不是同一条“安全等级”刻度，而是不同的冗余方式。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdWzJOUAVQuVHlaFqkrvYdzfIw4P5SibmpvTgnaQkiclvmj2Zux0ExueY2KdySj34pSJWaaD13ZK4MtKrbnaSAeb6fkYvfs2dog9g/640?wx_fmt=png&from=appmsg)

# 容量公式只是第一笔账

假设有 N 块同容量盘，并暂不计算热备、元数据、校验区、系统预留和厂商布局：经典 RAID 5 的理论可用容量约为 N−1 块盘，RAID 6 约为 N−2，双副本 RAID 10 约为 N÷2。Red Hat 文档也用减去一块或两块成员盘的方式描述 RAID 5/6 容量。

但采购表上的容量效率不能回答故障后业务是否还能完成。更高可用容量若换来无法接受的重建窗口或写入波动，节省的盘并没有降低业务成本。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdW26peqbaFfkeGtEcBGIX1SkByA3RUyUZDkExNRSf5GZsafBJYSPEbREtaSNDU5Elic5SBOdXsU0TibpcqWdgc96rGD8IBGU7Oh4/640?wx_fmt=png&from=appmsg)

# 小块写入的差别在更新路径

RAID 5/6 的非整条带写入通常要处理旧数据与校验，再生成新的校验并写回；RAID 6 还维护第二份校验。整条带写、非易失缓存、写日志和控制器优化可以减少这类开销，所以不能拿固定的“写惩罚倍数”套用所有产品。

Linux MD 文档说明，非整条带写需要读取旧数据后才能计算新校验，而写回缓存可以聚合为整条带写。RAID 10 不计算校验，但写入仍要到达镜像副本。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdUny1RB39hqKeHU2Yf7Z31bQvqCvvDeibv29EMt8q6tlEaDpdyEhL51YMqWZbLnwxqmNjqyQ5hvysibPaM0FTAG1QqFicAbL2dXds/640?wx_fmt=png&from=appmsg)

# “坏两块盘”必须说明坏在哪里

RAID 6 的双校验针对同一组内任意两块成员盘失效。RAID 10 能否承受两块甚至更多盘失效，则取决于故障是否落在不同镜像对；同一镜像对的两份数据都失效，阵列就可能不可用。

因此，不能把“RAID 10 可以坏多块盘”写成无条件承诺。还要继续检查镜像副本是否跨机框、控制器、电源和故障域放置，否则逻辑上的两份副本仍可能一起失效。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdXbg6XMibFBco14BX5vib8xtGmtFaPHZOHgDEJBs2C1yNm6RpYZReCblZGoU4oVs4zv1FKiaPCyO83x7gS0NiaH075ymwGn9l5jvo4/640?wx_fmt=png&from=appmsg)

# 真正拉开风险的是降级与重建

成员盘失效后，RAID 5/6 读取剩余数据与校验来重建缺失内容；RAID 10 通常从仍存活的镜像副本复制。两种方式都会占用队列、带宽、控制器和介质，并与前台 I/O 竞争。

SNIA 提醒，大容量盘可能延长 RAID 重建带来的性能影响。IBM 也说明，RAID 5 在磁盘失效到重建完成期间，读写性能都可能下降；分布式 RAID 则可能通过把重建区域分散到多块盘来改变瓶颈。

所以我会比较健康、降级、重建和恢复后的 P99、吞吐、队列与剩余保护能力，而不是只比较正常状态的峰值。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdUpmru8sdmpPQGlhhY7Gds4TTTwpTGQVicIwl9uOzickdHiaLMqd6EuArE9J7pZpKoqO87SluNIfib8ygIw4ClmyxQ4DYFMZriaxiaiaU/640?wx_fmt=png&from=appmsg)

# 选择依据是不可接受的失败方式

如果业务对随机写延迟敏感，并愿意用容量换取更直接的镜像路径，我会优先验证 RAID 10。若容量效率重要，同时不能接受第二块盘失效就丢失保护，则验证 RAID 6，但必须测试校验写和重建期间的业务表现。

RAID 5 不是天然错误，却需要更严格的前提：业务接受单盘容错、故障域足够小、重建时间可控，而且数据还有独立保护。任何选择都要核对目标产品的条带宽度、缓存保护、热备或分布式重建方式，不能把经典公式直接当成阵列实测结果。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdUmf26vegp3RT9xF2ySfRQcHs9Ca5RZbloagoSib8Yz0s93ibO5j1QV0sjd3mrJrSpMw5gicYicq6gZ0OCUzicFO3ImS1ww0ic7jHeIQ/640?wx_fmt=png&from=appmsg)

# PoC 必须故意让阵列进入坏状态

测试至少覆盖正常、单盘降级、第二故障边界、重建中和重建后校验。每种状态记录业务 P50/P99、吞吐、队列、重建速度、告警、缓存状态和剩余容错能力；同时验证更换错误磁盘、控制器切换和异常关机后的恢复流程。

RAID 仍然不是备份。它不能撤销误删、修复应用逻辑错误，也不能单独应对勒索、控制器缺陷或站点损失。独立快照、复制、不可变或离线备份以及恢复演练，必须在 RAID 之外设计。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdUx9HJy01He2tKrj33K9oObesib3DwzL2zRZnGnpbOO1yrFwvlf86giaDF3JjBDCGtrghUz3Du4rzseicoky3Jh3ib8EvqMZs2Bnzc/640?wx_fmt=png&from=appmsg)

我的验收标准不是“选出了 RAID 6 或 RAID 10”，而是团队已经证明：正常写入可接受，故障后业务仍守住目标，重建窗口已知，第二故障边界说得清，阵列之外也确实能够恢复。Q047 将继续拆解，为什么重建窗口本身就是可靠性风险。
