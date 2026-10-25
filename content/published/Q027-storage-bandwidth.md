# Q027：为什么不能只看链路带宽判断存储性能？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/by3wCHGu-JL1cRWJ_sfwfQ
> 发表时间：
> 迁移时间：2026-10-25

# 网络升级了，数据库为什么没有明显变快？

假设这样一次升级：存储网络换成了更高带宽的以太网。上线后，备份窗口明显缩短，大文件复制也更快，但数据库提交时延几乎没有变化，高峰期的 P99 仍然会升高。

有人怀疑新链路没有生效，也有人认为存储性能不足。可同一条链路对两类业务产生不同效果，本身已经说明：备份和数据库等待的不是同一种资源。备份主要持续搬运大块数据，数据库日志写入可能在等待一个小请求完成并得到持久化确认。

链路带宽回答“一秒最多能运输多少比特”，不能回答“一笔 I/O 多久完成”“一秒能完成多少次请求”，更不能说明数据何时安全落盘。判断存储性能，必须把带宽放回请求大小、IOPS、队列、时延和完成语义中。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdXAicezAowpHJkGWN0h6QBy4Bk6XHhdQPw8XibXvS2BdEBHtdobccrbUABicLzKccghOibXcMqkvz5tyKdMNjAQrW0Iy3Q7Cvvcesw/640?wx_fmt=png&from=appmsg)

# 带宽、吞吐、IOPS 和时延不是同一个指标

带宽是链路的传输能力。例如 100 Gb/s 除以 8，理论上相当于 12.5 GB/s；这还是没有扣除以太网、IP、TCP/RDMA、存储协议和控制流量之前的线路上限。业务实际完成的数据量才是有效吞吐。

在同一观察层、同一时间窗口内，可以用一个简化关系理解吞吐：

  * 

[code]
    吞吐 ≈ IOPS × 平均 I/O 大小
[/code]

  

这不是说三者能够独立增加。大块顺序请求用较少的 IOPS 就可能形成很高吞吐；4 KiB 小请求即使达到很高 IOPS，链路带宽仍可能没有跑满。SNIA 对存储性能的描述也把块大小、IOPS、吞吐、时延、服务质量和队列深度放在同一个工作负载模型中。

时延回答的是一次请求从提交到完成要等多久。平均时延可能看起来正常，少数慢请求却会进入 P99 或 P99.9，直接影响数据库事务、虚拟机响应和同步写。因此，“链路利用率不高”不能反推出“业务时延一定很好”。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdXfQWcORARHPaTOB9UIv7L9oeL4IyhemSicEdXhWKBkx73kVAGibpJymO5B64Pia92Ug1FJH4LkRVOCze9EtRapFS8UE8xconJRu4/640?wx_fmt=png&from=appmsg)

# 同样搬运 1 GiB，存储收到的工作量可能完全不同

备份通常倾向于大块、顺序和较高并发，关注持续 GB/s。数据库数据页和日志可能产生小块随机读取、混合读写或低队列深度的同步写，更关心单次完成时间。

同样传输 1 GiB 数据，可以由约一千个 1 MiB 请求完成，也可以由约二十六万个 4 KiB 请求完成。这个简化计算没有考虑拆分、合并和缓存，只说明一个事实：数据量相同，请求数量可以相差两个数量级。每次请求还要经历分配、排队、协议处理、完成通知和错误处理，所以第二种负载可能先耗尽 IOPS、CPU 或队列，而不是带宽。

SNIA 的基准测试指南明确提醒，块大小选择不正确，会分别产生过于乐观的吞吐或 IOPS 结果。只展示大块顺序带宽，不能代表生产中的小块随机性能。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdWytibUy1VFBWIsppZXKAkUTk9Doc1wUpQUUiaKhyN8STSicP1dwbUZk7epAltLfnFqgfl0ialiaLS5vBrNUfXlUiaiaKMsfJbOibTyuGs/640?wx_fmt=png&from=appmsg)

# 更宽的链路，只能缩短完整路径中的一段

一次存储 I/O 的端到端时间，可以拆成应用等待、文件系统或块层处理、主机排队、协议与网络、存储前端、控制器队列、缓存和数据保护、介质服务，以及完成响应。

带宽主要影响数据在线路上的序列化和传输时间。大块数据经过低带宽链路时，这一段可能是主导因素；对于小块 I/O，传输的数据很少，数据库锁、系统调用、网络往返、控制器排队、SSD 尾时延、RAID 或副本写入更可能占主导。

Linux 的 blk-mq 也说明了存储请求在主机侧并非直接进入设备：请求可能经过软件暂存队列、调度或合并，再进入硬件派发队列；设备资源不足时，请求还会留在派发队列等待。链路再快，也不会自动消除这些队列。

同步写还多了一条重要边界：业务等待的通常不是“数据已经通过网卡”，而是上层协议和存储系统给出的完成确认。数据是否进入受保护缓存、是否完成日志或副本要求，取决于具体持久化语义。链路带宽不能替代这项承诺。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdWsKFffTyngAWGhH8q0kzeiah8hpTboPBJdS6Vqtc2vebUoN3iavQDXdkiaiaS737G3ADgWvFpQyfIppmQz6ibnUEtbVoPHvncB3oAw/640?wx_fmt=png&from=appmsg)

# 标称端口带宽为什么不能直接相加？

一套存储可能有多块高速网卡和多个前端端口，但标称带宽总和不等于单个业务流能够全部使用。多路径策略可能按连接、设备或请求分配流量；一条连接未必能跨所有端口并行。主机 PCIe、CPU 和协议栈也可能先到边界。

流量进入存储后，还要汇聚到控制器、缓存、数据缩减、RAID 或副本处理以及后端介质。前端端口能够接收，并不代表后端能以相同速率完成。重建、快照、复制或数据迁移共享资源时，限制点还会随系统状态变化。

因此，吞吐通常受路径中最先达到处理上限的环节约束；时延则是各层服务时间、排队、重试和一致性等待的累积。不能把某一个端口的规格，直接当成端到端性能承诺。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdVXb4gvteibUMO796QbRzfMicJ1Saeo5HhZsDDErELT2FgtA0wBqloiaov28ianZvjNXHC4vbz2IxKmeqaZicFUSHf0pD7iaAs7TBozI/640?wx_fmt=png&from=appmsg)

# “链路跑不满”本身不一定是问题

业务可能采用小 I/O、低并发或串行提交；也可能每次请求必须等待持久化完成。此时链路利用率不高，是请求生成和完成条件的结果，不代表系统配置错误。盲目增加并发虽然可能提高 IOPS 和带宽，也可能让队列增长、P99 恶化。

测试工具的配置值同样不等于实际行为。以fio为例，官方文档特别提示：同步 I/O 引擎可能无法利用更高的iodepth，异步引擎也可能受操作系统和缓存路径限制，应核对实际达到的深度分布。fio：I/O depth

所以验收目标不应默认是“把链路跑满”，而应是在生产请求大小、读写比例、顺序性、并发、缓存状态和完成语义下，满足业务所需的吞吐、IOPS 与尾时延。

# 带宽必须和哪些数据一起看？

选型或排查前，至少补齐十项输入：I/O 大小分布、随机与顺序比例、读写比例、并发数、实际队列深度、平均与 P99/P99.9 时延、同步或异步完成、工作集与缓存关系、主机 CPU 开销，以及控制器和介质服务时间。还要分别观察正常、后台任务、重建和故障切换状态。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdVQTibbPOOOeqtKOyAicN7txLjibhJbFV23QodXib1RaaAUTGFaSnXecblIMIY1loyWFZ91Px5JV2zHsIePjWvHUfia4flDNyn4yibb8/640?wx_fmt=png&from=appmsg)

回到开头的升级：备份变快，证明大块持续传输从更高带宽中获益；数据库变化不大，说明事务主要等待的不是链路搬运。网络升级并非无效，只是解决了不同的性能问题。

链路带宽决定一段路最多能搬多少数据；请求大小决定需要完成多少次工作；队列和时延决定每笔请求什么时候轮到；持久化语义决定业务究竟要等到哪里。把这些指标放回同一条 I/O 路径，才是在判断存储性能。
