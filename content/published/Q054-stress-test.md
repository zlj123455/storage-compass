# Q054：性能压测为什么常常无法代表生产负载？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/yM30FbRve96EpZoHeVLUsw
> 发表时间：
> 迁移时间：2026-10-25

假设选型 PoC 时，测试主机持续发送固定大小的随机 I/O，存储给出了漂亮的 IOPS 和平均时延。上线后，订单数据库却在业务高峰叠加备份时偶发提交超时。有人翻出报表说：“当时明明测过，存储不可能是问题。”

这份报表未必错。错的是让它回答了一个原本没测过的问题：一笔订单能否在高峰期按时提交。提交慢也未必是存储造成的，数据库锁、CPU 调度和应用重试同样要查。

压测结果只对当时的请求、路径、缓存状态、并发方式和完成条件成立。它可以说明系统在哪组条件下表现如何，却不能直接证明生产业务在另一组条件下也会稳定。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdUuhjmcibkRQpctSm6JxD2x38KiaBSObCWoXTphm6IZrTEGJrM9cU7fJbQP07wwfa9ZuEgCOn5o64aITBXYbQXQqH5qR3jvK6HJ8/640?wx_fmt=png&from=appmsg)

# 先回到 PoC：那条曲线到底测了什么？

看一笔测试 I/O。它由哪台主机发出，是读还是写、请求多大，是否经过生产会用到的数据库、文件系统和网络协议？如果测试直接打到设备，生产却从虚拟机经过文件系统、多路径和阵列控制器，这两个时延甚至不是同一段路径。

还有“并发 32”这类常见说法。测试里设置的队列深度，是希望维持多少在途请求；同步 I/O 引擎、缓存和操作系统限制都可能使实际深度不同。要看测试结果中的深度分布，而不是把命令行参数当成设备实测值。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdVPgrGNTPq4VmvcWPI07ibnBUzic54Iibttb7Rc7rVqbOYia4d6iaCfzDr4hANJDu42tQ0xWpSrZaeWsIhHR507Sr6KFwMsz5dYWibAg/640?wx_fmt=png&from=appmsg)

缓存也会改变故事。反复读一份较小的数据集，可能越来越多地命中主机或阵列缓存；生产的工作集若持续变化，命中率就未必相同。缓存本来是生产性能的一部分，问题不是“要不要禁用缓存”，而是测试用的工作集和预热状态是否对应了要验证的业务状态。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdVibua44I9JnE3PonT7dMryUVLiaBak4tJhiaibYnpN1MzDT3icJYibMxHxDHN3I4Er6Rxuia8j1S8XmWGpicKTP7sxgB3Bxx570DfLLIc/640?wx_fmt=png&from=appmsg)

# 再跟一笔订单：它在等哪个“完成”？

订单应用说“提交慢”，不等于某块 SSD 读写慢。一次事务可能先等数据库锁，再写日志、等待所需的持久化确认，最后才向用户返回。若时间消耗在锁或线程排队上，把设备换快也未必能解决；若等待确实出现在日志写入路径，才需要继续对照主机队列、协议和存储端。

PoC 如果只记录一次普通写调用返回，而数据库的提交路径要求日志同步完成，两者的计时终点就不同。write() 把数据交给系统，不自动等于 fsync() 已完成；具体数据库如何保证提交持久性，还要看它的日志和刷盘配置。把不同“完成”语义的延迟放在一张表里比较，数字再精确也无法解释那笔订单。

所以我会把应用提交、数据库等待事件、主机 I/O 和存储响应放在同一时间线上。先找业务时间究竟耗在哪一段，再问 PoC 是否覆盖了这一段；不要因为一张设备跑分高，就跳过这一步。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdVX9ZvqgwiaLeRvHH7FpVOP3M1BpO14uJREl2f44ebvNAcw2aDX7RZ2ybZS01EvwbOibExKGqBR5YXoU6ic7ibzagkEnO6jcVLuSMo/640?wx_fmt=png&from=appmsg)

# 为什么偏偏在高峰加备份时变慢？

测试机可能一直按固定并发把请求送出去；订单流量却会突然涌入，超时后还可能重试。即便两边的平均 IOPS 相近，请求到达的时间形状也可能不同。排队不是按平均值发生的：短时集中到达时，少数提交会等得很久，而整段时间的平均时延仍可能好看。

备份开始后，前台事务还可能与备份共享主机 CPU、缓存、网络链路、控制器队列或后端介质。哪一层真的争用，不能凭“备份正在跑”就下结论；需要对照备份开始前后相同业务量下的等待位置，以及延迟分布。这里关心的不只是最高 IOPS，更是关键提交是否仍落在业务允许的响应时间内。

这也解释了为何一段稳态、热缓存、没有后台任务的压测不能替代生产高峰。它测到了一个有价值的基线，却没有覆盖让业务失约的那个状态。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdUJZcl21t7LmicFc6tWW71l5YhaLgJKPmbiaOxtstgrPB4uTOeeLVUXOHMicwQo67aAGfNwotSZSvricommaN13nEe92bBKiaVaImtw/640?wx_fmt=png&from=appmsg)

# 回到开头：下一次 PoC 该补哪道题？

我不会丢掉合成测试。它便于控制变量，找吞吐上限、比较请求大小或协议差异。但那份成绩应写明适用条件，不能单独充当上线承诺。

接着补一组与订单提交相关的验证：沿用生产的主机和协议路径，复现接近真实的请求大小、突发与工作集，使用相同的完成语义；在业务高峰与备份重叠的状态下，同时观察应用提交时间、数据库等待、实际 I/O 深度和存储响应。如果不能复现异常，也至少知道这次 PoC 尚未证明什么，而不是替生产提前宣判“没问题”。

原先那条漂亮曲线仍然有用，只是结论要改写成一句带条件的话：在这套请求形状、缓存状态、并发和路径下，系统达到了什么表现；而那笔订单要求的完成条件，是否也被验证了。这才是压测能带到生产里的证据。请求路径和完成语义随实现变化，观测到的时间关联还需要实验支持，才能作为因果判断。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdUlghXwQh9p9nb7pQ7jWIfwSR5ibAw2ZDS6ibhIxZCg023kEO5QWabEGzB0ojIO6EwfBMniappNd2bBWYJRia4ia2583aBYzGhxBM8s/640?wx_fmt=png&from=appmsg)

想看懂跑分背后的请求路径，可以读张冬《大话存储（终极版）》第 19 章，理解应用、文件系统、缓存与设备如何共同影响 I/O 表现。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdX1hxGcZ5HSXicKvTtsQ77a2etOjvkXFQnwiazs3AzVt7ZCibNFicuRZYWY8xBLMMGwatl6A9eYwEy3HlFOoxy9dFgFFc3usQ1DQbk/640?wx_fmt=png&from=appmsg)
