# Q025：什么是 RDMA，它在存储网络中何时值得使用？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/Y2amRZx0agraDYw9JOYjrw
> 发表时间：
> 迁移时间：2026-10-25

# 一次“把 TCP 换成 RDMA”的提议

假设这样一个选型场景：一套全闪存储正在做 PoC。普通以太网方案已经能跑出不错的吞吐，但供应商又演示了 NVMe/RDMA——同样的服务器和存储，时延更低，主机 CPU 占用也更少。项目组很快形成了一个直觉：既然 RDMA 更快，生产网络就应该直接采用 RDMA。

架构师没有立刻同意。他先追问：生产业务慢在哪里？是数据库锁等待、应用排队、同步写持久化，还是主机网络栈？演示中的优势出现在平均时延，还是业务真正关心的 P99？链路拥塞、交换机故障和路径切换时，RDMA 方案还能按业务允许的时间恢复吗？

这些问题不是在否定 RDMA，而是在确认一件事：RDMA 的价值，是缩短并减轻数据传输路径；如果生产瓶颈根本不在这条路径上，换成 RDMA 也不会自动改善业务。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdVXGb7kvXo6LWpT3WaU9ZkKp1VJBSn6nFic93uAOLWe7KwG3PBfxZbFlzVZQ7hYYibSJ4fYRL9VUjfPaZpNiau6YXaK1iatqAzOzEU/640?wx_fmt=png&from=appmsg)

# 核心结论

RDMA 是 Remote Direct Memory Access，即远程直接内存访问。它不是一个独立的存储协议，而是一种数据传输机制。NVMe/RDMA、iSER 等上层协议可以利用它，让网卡直接在本地与远端已经注册的内存区域之间搬运数据，减少中间拷贝、系统调用和内核网络栈参与快速数据路径的次数。

RDMA 值得使用，通常要同时满足四个条件：后端存储足够快，传统网络软件路径已经成为可测量的开销；业务对小 I/O、高并发和尾时延敏感；主机 CPU 开销确实影响系统密度或成本；团队能够建设并运维端到端的 RDMA 网络。少一个条件，都需要重新算账。

# 一次远程 I/O，RDMA 到底改变了哪一段？

先看简化后的普通网络路径。应用或存储客户端提交数据后，请求通常要经过用户态与内核态边界、套接字与 TCP/IP 协议栈、内核缓冲区和网卡；远端收到数据后，还要经过相反的处理，最终交给目标缓冲区。现代操作系统和网卡已经能通过分段卸载、合并与零拷贝接口优化这条路径，但每个请求仍可能产生软件处理、上下文切换和数据搬运成本。

RDMA 在建立连接前，会先完成一系列准备工作：应用注册可供网卡访问的内存，创建队列对（Queue Pair，QP）和完成队列（Completion Queue，CQ），并交换访问所需的地址与权限信息。之后，客户端把工作请求放入发送队列；支持 RDMA 的网卡，也叫 RNIC，读取描述符并执行数据传输；远端 RNIC 按已经授权的内存区域放置数据；操作完成后，CQ 中出现完成记录，供软件确认结果。

这条快速路径的关键不是“网络不需要 CPU”，而是把重复的数据搬运和一部分协议处理交给 RNIC，并减少每次 I/O 进入内核的次数。连接建立、内存注册、队列管理、错误恢复、存储协议处理和数据持久化仍然需要软件与 CPU。RFC 5040 对 RDMA/DDP 的描述也是“允许”直接放入上层缓冲区和实现内核旁路，而不是承诺整个 I/O 链路完全零拷贝、零 CPU。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdWbNGSjwic6VvicxNx5lfUBOw4xmPzrN9a3lwIXLcPgmCknhDeNxxaSe0Dt4U3LPkKBcvaRjjwMGf8nxpahsHme1ElGRxhDlUIcY/640?wx_fmt=png&from=appmsg)

# 内存为什么必须先注册？

让远端设备直接访问本机内存，如果没有边界控制，会成为严重的安全和稳定性风险。内存注册的作用，是把一段虚拟内存映射并固定为 RNIC 可识别的区域，同时生成访问键，限定远端可以访问什么地址、执行什么操作。

因此，RDMA 的性能并不是凭空得到的。注册与注销内存有成本，固定内存会占用资源，QP、CQ 和队列深度也需要规划。连接数量很大、缓冲区生命周期很短或实现频繁注册内存时，控制路径的开销可能抵消一部分收益。成熟实现通常会复用缓冲区和注册结果，但 PoC 仍要观察真实客户端与目标端如何管理这些资源。

Linux 的用户态 RDMA 接口也说明了这一设计：快速路径通常通过映射到用户空间的硬件寄存器直接提交操作，避免系统调用和进入内核的上下文切换；但资源创建与管理仍由内核协调。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdUKr6mVryJuuyQBoGQnJ8iac2ia1YrXGfndnUo1Cq1r6vFu5AC19So6CwUL2UcqBiaU2HOic5oDNA7hY19HFYibmo2DXAyOCH2tq774/640?wx_fmt=png&from=appmsg)

# RDMA、NVMe/RDMA 与 RoCE 不是同一个概念

这三个词经常被混在一起。

RDMA是远程内存访问的数据传输能力。

NVMe/RDMA是 NVMe over Fabrics 的一种传输映射，用 RDMA 承载 NVMe 命令和数据。

RoCE是在以太网上实现 RDMA 的方式之一；另外还有原生 InfiniBand 和运行在 TCP 之上的 iWARP。

所以，“存储支持 NVMe-oF”并不等于“必须建设 RoCE 网络”；“网卡支持 RDMA”也不等于端到端方案已经可用。主机适配器、驱动、交换网络、目标端、路径管理、监控工具和故障处理都要形成一条完整支持链。NVMe 官方规范也把 RDMA 定义为 NVMe-oF 的一种传输，而不是 NVMe-oF 的全部。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdWRibn4iaiblu0JkhG5pon6lmqVQyEMPPpKT88659PlDwmfIGg1XH1SDwDdvCJRbpN8rqJwrrE7Kgth90Ru807CkwOx56GzK9hcEs/640?wx_fmt=png&from=appmsg)

# 什么时候，RDMA 的收益最可能出现？

第一类是后端已经足够快，网络软件路径开始显得“重”。例如全闪或 NVMe 存储能够快速完成请求，此时主机协议栈、数据拷贝和每次 I/O 的 CPU 成本更容易进入端到端时延预算。若后端本身是慢速介质，或控制器长期排队，优化几十微秒甚至更小的一段网络路径，业务可能感知不到。

第二类是小块、高并发、对尾时延敏感的业务。小 I/O 的有效数据少，每个请求固定的软件处理成本占比更高；并发上升后，CPU、队列和调度抖动还可能放大 P99。RDMA 的价值往往不只是提高峰值 IOPS，而是减少主机开销，并让时延分布更稳定。

第三类是CPU 本身就是稀缺资源。如果一台服务器因为存储网络处理消耗了大量 CPU，减少这部分开销可能允许部署更多业务实例。不过必须用“相同业务吞吐下的 CPU 占用”衡量，而不是只比较两个方案谁的峰值更高。

第四类是运维能力已经准备好。以 RoCE 为例，拥塞、丢包、交换机队列、优先级、ECN/PFC 的设计以及端到端参数都会影响结果。不是把 RDMA 网卡插进现有以太网就能获得稳定低时延。网络团队必须能观察拥塞与丢包，存储团队必须能关联主机、网络和目标端指标，故障时还要知道由谁恢复、如何降级。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdWM92lLCBaMLUc0aXlrYcibt27nDHx6DAtXXibGibMQmWKvVUAJy4zCuUDbmxKYvjG82RYd15DQYFSpyiccn2MB08uWl43lVm2yla4/640?wx_fmt=png&from=appmsg)

# 哪些场景不应该因为“更先进”就采用？

如果业务主要是大块顺序传输，现有 TCP 网络已经满足吞吐和 CPU 目标，RDMA 的增量价值可能很小。如果慢点在数据库锁、应用线程池、文件系统元数据、同步复制或介质垃圾回收，RDMA 也只能缩短其中一段路。

更重要的是，RDMA 不会替代数据持久化和高可用设计。RNIC 把数据放入远端内存，只说明传输完成；数据是否进入受保护缓存、是否满足副本或日志要求、存储何时向应用确认，仍由上层协议和存储系统决定。传输时延更低，不能被解释成数据已经安全落盘。

如果团队无法解释拥塞时的行为、无法观测 RDMA 相关计数器、没有验证网卡或交换机故障后的路径恢复，那么更低的实验室时延，可能换来更难定位的生产故障。此时，成熟的 TCP 方案往往是更可控的选择。

# 最后怎么判断值不值得？

最终判断 RDMA 是否值得，不是看演示中的峰值性能，而是看三个结果：它是否改善了生产真正关心的尾时延或 CPU 开销；收益是否足以覆盖网络建设和运维成本；发生拥塞与故障时，系统能否在业务允许的时间内恢复？

只有三个答案都有证据，RDMA 才从一项高速技术，变成一个值得采用的架构选择。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdUPUJxrcyB6rYYc2B0U8QK0RicqJzZdxd8KF5jmib3dPbGDkWVUl6rldwdRMqibGxicra9On5cQOe4kibBKdGTiajd7zmbO0YGGTPMtA/640?wx_fmt=png&from=appmsg)
