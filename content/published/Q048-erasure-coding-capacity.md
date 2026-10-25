# Q048：纠删码适合哪些容量型负载？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/8hP_4-YBqHA2d5n-7L7cXg
> 发表时间：
> 迁移时间：2026-10-25

假设一个对象存储池同时保存视频原片和大量小型业务对象。容量不断增长，团队计划把三副本换成纠删码。试跑时，大文件吞吐能够达标，小对象请求的尾延迟却明显变差；停掉一个节点后，两类业务又出现了不同程度的波动。

同一套保护方式，为什么会产生不同体验？答案要从每次请求经过的路径里找。

纠删码值得优先用于大块访问、低频覆盖、容量收益显著的负载，前提是正常读写和故障恢复都能守住业务目标。对象大小、更新方式、时延要求和恢复余量，比“冷数据”或“热数据”的标签更有判断价值。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdV54KZQWgC0eObmXGcw9sjO4ibJhEiascChOuy7uJH0h6Ls2pfSTottErdDlYKqJnFbh9Qw0fwmbclE6jpreWGGgibYWYnH9ySk2s/640?wx_fmt=png&from=appmsg)

# 跟着一个大对象写进去

以常见的 Reed–Solomon 编码为例，系统按条带组织数据，将每个编码组分成 k 份数据分片，再生成 m 份校验分片，并按放置规则写到不同设备。大对象可能跨越许多条带，不能理解为整份视频只做一次拆分。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdXyPkeH7klBQiaqj195g5Ifico649xK3aO7icS6puzibxITnsx0M3dM4yxiaC47klYiaL8VibSX2aOWQM1P0NiaQMa1QQOjib41ibibwoLrCc/640?wx_fmt=png&from=appmsg)

用 4+2 举例，四份数据配两份校验，理论占用为原数据的 1.5 倍；三副本则为 3 倍。这笔简化账不包含元数据、对齐、预留与恢复空间，也不证明两种方案具有相同可靠性。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdVia82Gv3KyiboS76XlZuGZ7Q4RLF8jEIrPwF3huticqYzibxliaC54IBtXZzRicEu55OCsqN8q1f5hPgGvBPlLztyeDm5kNtkRO09uk/640?wx_fmt=png&from=appmsg)

写入路径还包括编码、分片传输、持久化和状态协调。返回成功需要满足产品的确认规则，不能仅由 k+m 推导。我的核对重点是：确认时哪些分片已受保护，后续还剩哪些后台工作。

# 换成小对象或局部更新

接着让同一个池处理很多小对象。每次请求携带的数据变少，但请求处理、分片管理和网络交互仍有成本；对齐和最小分配粒度还可能侵蚀理论容量收益。

如果业务改成块或文件接口下的小块覆盖更新，部分条带更新可能需要读取旧内容、更新校验，再写回相关分片。缓存、日志和编码实现会改变这条路径。S3 整对象替换与底层局部覆盖也要分别测试，不能把它们当成同一种写入。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdWEShficHH6VA62nJC3kc29w0wxNsan667o6fxRcQZLkKESyUJdrbCc3YN4rg9wtvwkHO2GEicAHbTuQTLhbW0sCtAkkjs7VOVJw/640?wx_fmt=png&from=appmsg)

这并不构成小 I/O 的绝对禁区。例如 Ceph Tentacle 提供了针对小 I/O 和填充开销的优化，但有版本和编码插件条件。选型应追问目标配置做了什么优化，再看实测结果。

# 现在让一个节点离线

健康时，读取所需的数据分片通常无需解码。节点离线后，如果请求命中了缺失数据，普通 RS 重建路径需要从其他可用分片取得足够信息，解码出缺失内容；后台还要生成并写入新的分片。

前台降级读取与后台恢复由此争用 CPU、网络和介质。需要多少参与分片，取决于编码和修复方式；局部修复码可以在某些故障下缩小参与范围，不能把“每次都读 k 份”推广到所有实现。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdXShOXpCHibUNibwUhw5QKYqwAJqiaHbUMw5JrzUxIvWgZ6hT7vXRPtjicAYqwedjkDeIVGBWpFXPEbfH72sswzrUic9s7hqD9deMV0/640?wx_fmt=png&from=appmsg)

还要问故障究竟拿走了什么。RS 的 m 对应同一编码组可容忍的分片丢失数；如果一个机架放了多份分片，丢一个机架就可能越界。即使数据仍可解码，系统也可能因最低服务分片数等策略暂停 I/O。恢复能力和持续服务能力必须分别验证。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdXd43VGicymL2aFT1wZR3SxbbXf5RIbSlPdWgS5CcDQiabib0SFRTyrNo5QE4vchpFd9F3KL0WhkGlcoUicFSHSNXJ5eglBwBwndD0/640?wx_fmt=png&from=appmsg)

# 回到业务，哪些负载值得优先尝试

视频原片、大块备份数据、归档和数据湖文件，如果主要以大块写入、连续读取为主，通常值得优先评估纠删码。访问频繁并不自动排除它，例如反复顺序读取大型数据集，关键仍是吞吐和时延是否达标。

业务日志、频繁小块更新和低时延在线请求，则需要更严格的验证。大文件如果总被零碎读取，也未必符合前面的有利条件。备份库还要测试恢复时的集中读取，不能只看每天写入是否顺畅。

我会按访问方式划分存储池：让容量收益明显的数据先试用纠删码，让时延敏感的数据与元数据保留适合它们的保护方式。是否分池，最终由测量结果决定。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdUNDGodw3vb6JI6hAGvRQibernBTianV9MpS2Qumz6HQ0zsXxdIVVic7J9dxTfaZH0IqicISDiav9jbMPnUKyYPnibK9DROFPZY3Bgl4/640?wx_fmt=png&from=appmsg)

# 用三个状态验收这笔容量账

PoC 应固定数据集、对象大小分布和并发模型，分别测正常、节点故障后的降级读取、后台恢复三个状态。既测大对象吞吐，也测小对象和局部更新的 P99、超时与错误率，避免总吞吐掩盖某类请求变慢。

再把容量推到计划运行水位，检查故障后是否仍有符合放置规则的目标节点与恢复空间。记录实际物理占用、CPU、网络、保护恢复时间，以及恢复期间的业务表现；所用缓存和优化配置也应留档。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdWkuojaBvoHQWcANPaWvDJLueYib96ibdIVGyJe9rP9mPOjHT9K9nugUALtRiaKctPibQABQLFp6Fx3bJQ45360n2S7kZdy33hgYV0/640?wx_fmt=png&from=appmsg)

* * *

> 阅读扩展资料
> 
> 张冬.《大话存储（终极版）》. 清华大学出版社。本文涉及的 RAID 与条带化基础、分片与校验的直观模型、重建开销的定性描述，这本书讲得比多数厂商白皮书清楚，适合还没有底层直觉时先读一遍。
> 
>   
>
