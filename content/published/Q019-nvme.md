# Q019：NVMe over Fabrics 解决了什么问题？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/gJByiRbJ4Ni7yEcCx2t50g
> 发表时间：
> 迁移时间：2026-10-25

月末批处理一启动，数据库提交的 P99 就越过了业务阈值。存储团队先看阵列：后端是 NVMe SSD，控制器 CPU 没有打满，空闲时跑出的 IOPS 也很好。于是讨论很快落到一个听起来很合理的方案上：主机到阵列还是原来的块访问路径，是否应该换成 NVMe over Fabrics，简称 NVMe-oF？下面是一个综合后的典型复盘场景，并不对应某个具体客户。NVMe-oF 解决的是主机如何跨网络、仍按 NVMe 命令和队列模型访问远端存储的问题。但在动手之前，先要确认 P99 到底花在了哪里；没有这一步，协议升级很可能只是把一项看起来先进的改造加入清单。![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdXaMV30U9GEhj9jHQOicqYpTtBaZQbQCGq731Go2ia2T2B8XRU5RsUwDAQnxH3vPMoDXnCauOwcGIy5AXZaf0u5EfzSiaWicGoia1oU/640?wx_fmt=png&from=appmsg)高分没有解释这次超时项目组后来把同一时间段的应用提交、主机队列、网络端口、控制器和后端任务拉到一条时间线上。结果并不神秘：高峰期的写入并发上升后，一部分请求先在主机等待；同时阵列在进行复制与快照相关的后台工作。网络路径不是唯一变量，阵列后端也没有“完全空闲”。![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdVAG3rjGJbLVgwia6lyiarYwvFATovR1KPUeYu7NYOXb0fGyic41ZoSJPPZvqGAbgWIicBeSDHibuMMg1ojoj7YHNH4RoWNoleEmVgA/640?wx_fmt=png&from=appmsg)这正是存储 PoC 常被误用的地方。顺序大块读写的峰值、空闲时的 IOPS，能证明设备在某个条件下能跑多快，却无法证明月末的同步写、日志刷盘和应用锁竞争会不会把少量请求拖进长尾。P99 的含义是：99% 的请求在某个时间以内完成。它衡量的是最慢那 1% 的请求。只要这部分请求越过数据库或应用的超时线，业务看到的就是重试、事务变长或服务降级；此时平均延迟再漂亮也救不了现场。

# 一条 I/O 有三层：介质、主机协议和传输承载

讨论 NVMe-oF 前，最好先把一条 I/O 拆成三层。阵列内部使用 NVMe SSD，是**介质和阵列内部实现**；它决定控制器如何面对后端设备、缓存和数据布局。主机使用 SCSI 或 NVMe 命令集访问远端卷，是**主机访问协议**。命令最终跑在 Fibre Channel、TCP/IP 或 RDMA 网络上，则是**传输承载**。这三层可以有不同组合。一套全闪 NVMe 阵列，完全可能仍向主机提供 SCSI 块访问；主机切到 NVMe-oF，也不会顺带把控制器排队、快照整理、复制确认或应用锁替换掉。NVMe-oF 改变的，是主机到远端存储之间的协议路径。NVMe 以提交队列和完成队列组织 I/O；NVMe-oF 将命令、完成和数据传输映射到网络 fabric，让远端存储也能使用这一模型。NVMe 规范体系将通用模型与具体 transport 分开定义，当前包含 RDMA、Fibre Channel 和 TCP 等传输类型。![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdUa1Mb2EVaxJ4gibw7Cyck7dQZlfmpnzU8icVmJTFgIic2e2y8D7PShUHoeMcHDNOzgzRbSr1UbqGqGv5Og9hLaLPz2ibAFxTGJibkQ/640?wx_fmt=png&from=appmsg)当协议和主机路径确实是等待来源时，团队有机会减少不必要的转换或争用，并让远端访问模型与 NVMe 更一致。但如果请求主要堵在控制器、介质后台任务、CPU、网络拥塞或应用提交语义上，NVMe-oF 不会替你清掉这些队列。

# 三种承载，先看你准备继承什么

若这次复盘证实主机访问路径值得优化，应先核对已有基础设施和运维体系，而不是直接比较"哪一种最快"。已经有双 FC Fabric、HBA、多路径和变更流程的环境，评估 NVMe/FC 时，重点是这些已有能力能否端到端支持 NVMe。需要核对的是 HBA、交换机、阵列端口、主机驱动和多路径组合，而不是任何一个组件的单独宣传页。NVMe/TCP 将 NVMe 队列、capsule 和数据映射到 TCP，可复用标准 IP 网络；标准本身还定义了数据完整性与 TLS 等可选能力。对于已经具备独立存储网络、容量余量与网络可观测性的团队，它可能是更容易验证的路径。但跑在 TCP 上不会自动解决 CPU 余量、突发拥塞、网络隔离和故障恢复。NVMe/RDMA 则把要求延伸到支持 RDMA 的网络、网卡和驱动实现。它在特定实现与负载下可能获得更低的协议处理开销；同时也把网卡卸载、驱动版本和网络运维一致性变成项目条件。CPU 与绝对时延需要在目标 workload 中测量，不能从传输名称直接推出。![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdUyLxoc0ibxHq7VPj1MEnibnGuribIJw6oicia3ntIVKqUhvIevZcg3zVNYsspgOqlxC7FFkWF2txnEMg82vkrx6ibRAPfiau5LvmX23c/640?wx_fmt=png&from=appmsg)

# 把要不要上变成一次可以验收的 PoC

回到这次复盘，团队把 NVMe-oF 写成一个待验证假设：如果换掉主机访问路径，业务提交 P99 能改善多少；这个改善在链路和控制器故障时还能否成立。![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdVxRWEjo179v1Esnqy6mm9PowHicwrrMwGaYdkunhXKT2UsfTXWu5Da9BM6MouybfmMLw8bzbqrA53FHnTYfWL5940wMUCaOc7k/640?wx_fmt=png&from=appmsg)PoC 至少要留下六项证据：

  1. 用生产近似的读写比例、块大小、同步写、并发和持续时间建立 P50、P95、P99 基线，而不是只保留峰值 IOPS。
  2. 对齐应用提交、主机队列、网络、控制器和后端介质的时间线，确认协议路径在长尾中的占比。
  3. 核对主机操作系统、内核/驱动、HBA 或网卡、交换机、阵列和多路径的完整兼容组合。
  4. 在相同 workload 下比较现有路径与候选路径，同时记录 P99、CPU、队列深度、超时和重传/链路错误。
  5. 分别注入单路径断开、目标端口异常、控制器切换和路径恢复，观察应用何时超时、如何重试、是否需要人工处理。
  6. 预先写下通过线、回滚条件和责任人。若只写"性能应更高"，故障时就没有能执行的结论。

Linux 的 NVMe multipath 会基于 ANA（Asymmetric Namespace Access）选择优化路径；这是主机侧能力，不是对业务恢复时间的承诺。路径失效后应用实际会等待多久，仍需由阵列、驱动、超时配置和应用重试共同验证。![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdWkFQV5jJDdoDBw2oZvzibiaFkic3XGRmdWOAqc4JrCPX5Et3Njo1grXZTZKy97vNhsmO174VEkTF93Zvf9Mq71GP0qzOrT6vGnSg/640?wx_fmt=png&from=appmsg)那次复盘最后留下的结论更窄：只有当生产证据表明主机—协议—网络路径是 P99 的主要等待来源时，NVMe-oF 才是优先级靠前的改造。**如果根因仍在控制器排队、后台任务或应用同步点，先处理那些等待，通常比换一个协议名字更接近问题本身。
