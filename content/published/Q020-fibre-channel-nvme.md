# Q020：NVMe/TCP、RoCE 和 Fibre Channel-NVMe 的取舍是什么？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/2ca02UicDcV9IEpK5b9RnQ
> 发表时间：
> 迁移时间：2026-10-25

一套核心数据库已经稳定运行在双 Fibre Channel Fabric 上。新建的分析集群却只有以太网。两边都准备接入同一套全闪阵列，于是项目组拿出了三份方案：沿用 Fibre Channel-NVMe；在以太网上部署 NVMe/TCP；或者为 RoCE 建一张 RDMA 网络。三份方案的介绍页都写着低时延、高并发。可架构师没有先看峰值 IOPS，而是在白板上写下了一句话：我们不是在选一个更快的名字，而是在选未来发生拥塞、变更和链路故障时，靠哪套能力把业务带回来。下面是一个综合后的典型选型场景，不对应某个具体客户。先给结论：NVMe/TCP、RoCE 和 Fibre Channel-NVMe 没有脱离环境的“默认最优”。选择它们，本质上是在选择要继承哪套网络、故障域、兼容组合和运维能力。只有生产等效负载下的 P99、主机 CPU、路径故障和回滚条件一起通过，才构成部署理由。![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdX24LQKBeEKc3oveXjbgkAgmH9ibiaeHUUickn6sVLwC70JEUWwUCciayqNF56qznaAzUzM9BTStwricahaFibsIyrL3qJuTEmZcjozI/640?wx_fmt=png&from=appmsg)

# 先把三个名字放回同一层

阵列后端使用 NVMe SSD，和主机通过 NVMe-oF 访问远端卷，是两件不同的事。前者是阵列内部的介质与实现；后者讨论的是主机到存储之间，NVMe 命令和数据由什么网络承载。NVMe 规范把通用模型与具体传输分开定义。NVMe/TCP 将 NVMe 队列、命令 capsule 和数据映射到 TCP；NVMe/RDMA 使用 RDMA 跨 Fabric 传输；Fibre Channel 也有对应的 NVMe 传输绑定。它们让主机都能以 NVMe 语义访问远端存储，但并不意味着它们拥有相同的网络条件、主机资源消耗或故障表现。这里的 RoCE，应该理解为企业以太网环境中常被用来承载 RDMA 的一条实现路径，而不是一个可以替代所有 NVMe/RDMA 讨论的性能结论。它能否在这套业务中带来可感知的收益，要看网卡、交换机、驱动、配置和负载，而不是看传输名称。

# 三份方案，真正继承的是什么？

如果现网已经有两套独立的 FC Fabric、成熟的分区流程、HBA 管理和故障演练，评估 Fibre Channel-NVMe（行业中也常写作 NVMe/FC）的重点不是“FC 老不老”，而是现有运行体系能否端到端承载 NVMe。主机 HBA、交换机、阵列前端端口、操作系统驱动和多路径软件，必须按一个完整组合核对。只确认阵列端“支持 NVMe/FC”，不足以说明业务可以切换。NVMe/TCP 的吸引力在于它可运行于标准 IP 网络。对于已经有独立存储网络、清楚端口容量和东西向流量边界、也能持续观察网络状态的团队，它往往是更容易纳入现有运维体系的候选项。但“ping 得通、挂得上卷”只能证明连通性；它没有回答高峰时是否与其他流量争用、主机 CPU 是否有余量、链路异常时应用会等多久。RoCE 的讨论则应从能力闭环开始。若团队确实需要验证更低的协议处理开销，且网卡、交换机、驱动版本、配置模板、告警与故障定位都能由同一支团队负责，RoCE 才值得进入候选方案。反过来，如果一张专用网络只能在上线前由少数人调通、后续变更和排障没有可重复的方法，即使压测结果好看，也不应把它直接放到最关键的生产路径上。换句话说，FC-NVMe 的优势可能是沿用一套已经被验证过的 Fabric 运维模型；NVMe/TCP 的价值可能是复用可管理的 IP 能力；RoCE 的价值则需要连同端到端 RDMA 网络能力一起证明。这是架构判断，不是任何厂商对某一协议的性能承诺。![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdVaDfJAreIv8j2O4kwbM41HnKXLGhCjZUTd8xTDLolh13tTsGuuiaxR7MMMVvspCYpegvqXkByAp7MPdy71zqT6Nu5jPVOs22AE/640?wx_fmt=png&from=appmsg)

# 为什么一张性能表选不出传输方式？

项目组最容易犯的错误，是拿空载条件下的平均时延或峰值 IOPS 给三种传输排座次。那张表只能说明某个设备组合在某个测试脚本下的表现，不能说明月末批处理、数据库同步写或分析任务同时启动时，业务会不会被最慢的一小部分请求拖住。更有价值的问题是：在同一组块大小、读写比例、并发和持续时间下，应用提交的 P99 是否改善？主机 CPU、队列深度、网络异常计数和存储端等待各发生了什么？把链路断开、目标端口异常或交换机维护加入测试后，应用是否超时、是否重试、是否需要人工恢复？这里的 P99 是指 99% 的请求完成所需时间。对数据库、日志和在线交易而言，少量请求跨过超时线，带来的往往不是“平均慢一点”，而是重试堆积、事务拉长或服务降级。传输升级是否有价值，应由这条业务时间线回答。![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdXlWYultlF5ic9ibGbxwsuNr721hDibV6Cmm6Ric7XkMOU8QtYa6VucF92LnaoendYWz5oPGJojiaicObqAY6e6Ts10ottgIm3cI7UvA/640?wx_fmt=png&from=appmsg)

# 两条看起来冗余的路，可能仍在同一个故障域

无论选择哪种传输，都不能把“有两条路径”直接翻译成“业务高可用”。两块网卡接到同一台交换机、两条 FC 路径共用同一个控制平面、两端口落在同一控制器或同一供电域，都会让表面的双路径留下共同故障点。Linux 的 NVMe 多路径会把具有相同标识的 namespace 合并为一个块设备，再按策略在底层路径间选择；ANA 机制会影响优化路径和非优化路径的选择。但这是主机侧的路径管理能力，不是“业务零中断”的承诺。路径失效后业务实际等待多久，仍由目标阵列、驱动、超时参数和应用重试逻辑共同决定。所以在选传输之前，应先画出主机、HBA 或网卡、链路、交换机、阵列前端端口、控制器和供电之间的完整关系。只有每一条候选路径跨越了预期的故障域，双路径才有讨论价值。![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdWBorN78YPyzHMU5V4Arq4CjJ6BSiaMeKtEPkgCBVtcaONNacibwHyXicPyNqhovPIwjMgd6jL2vEkQypDxicA88FibSeA1NGzsD0p8/640?wx_fmt=png&from=appmsg)

# 把选型变成可验收的 PoC

项目组最终没有在会议室里宣布“哪个协议最好”，而是把三种候选方式变成同一张验收表：

  1. 基础设施：现有 FC 或以太网是否独立成存储故障域？谁负责日常变更、监控和故障定位？
  2. 真实负载：用接近生产的块大小、读写比例、同步写、并发和持续时间建基线，不只跑顺序大块吞吐。
  3. 业务指标：同时记录应用提交 P99、主机 CPU、队列深度、网络错误或拥塞指标，以及存储端等待。
  4. 完整兼容组合：核对操作系统、内核或驱动、HBA/网卡、交换机、阵列与多路径软件的版本组合，而不是分别查看组件清单。
  5. 故障注入：分别验证单链路、单端口、单交换机路径和控制器相关故障；观察在途 I/O、应用超时、重试和路径恢复。
  6. 回滚条件：在测试前写下通过线、失败条件、回退步骤与责任人。没有回滚条件的“性能改善”，上线后很难成为可执行决策。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdXNIfegAfUs0vPt1tZRcfPIdT9uHamibUUmGM2xOVKC60gsSp7fKoAgBkMlmedBiaBtwBsViasB6bKIILuS89seyA3waCicVokIYPg/640?wx_fmt=png&from=appmsg)如果一套方案只在空载时领先，却无法解释高峰 P99、故障切换和运维责任，它就还没有赢得生产资格。对企业存储而言，传输协议不是采购清单里的一个缩写；它是未来多年网络、主机和存储团队共同要承担的一条 I/O 路径。![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdW08KSvcfmiaODA0CmBxONfqSic3mVrO1Y8EicQbo7ZiagU6Mj7kdiagLeQO2iagucQcuoK5MCd17Mia9ZjdHfib4S8Mribo6sAyn6ZBIso/640?wx_fmt=png&from=appmsg)
