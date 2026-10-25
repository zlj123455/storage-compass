# Q018：iSCSI 与 Fibre Channel 如何选择？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/IYBhjAZHanHzpJLaQ0VWgA
> 发表时间：
> 迁移时间：2026-10-25

数据库迁移项目到了组网阶段。新机房已经铺好万兆以太网，却没有 FC 交换机。架构师建议先用 iSCSI，让业务按计划上线；DBA 担心交易高峰的尾延迟，坚持等 FC 设备到货。一方在算采购周期，一方在算一次超时会牵出多少重试和补偿。这不是“哪个协议更快”的问题。两条链路都可能成为可靠的块存储通道，也都可能因为设计不完整而在故障时让应用停住。真正要回答的是：业务需要什么级别的时延与恢复目标，网络和主机多路径是否隔离了共同故障域，以及这些承诺能否在真实负载和故障注入中被证明。

# 核心结论

iSCSI 把 SCSI 命令承载在 TCP 上；FC 则运行在独立的 Fibre Channel Fabric 中，采用逐跳的 Buffer-to-Buffer Credit 流控。前者的优势是复用以太网与 IP 运维体系，后者的优势是独立存储网络和成熟的 SAN 隔离模型。若业务对尾延迟、路径恢复和变更风险的容忍度极低，并且企业已有独立 FC 双 Fabric 与相应运维能力，FC 往往是风险更小的延续；若能为 iSCSI 建立真正独立的以太网存储路径，并在 PoC 中证明 P99、故障切换和应用恢复满足 SLO，iSCSI 同样可以承载关键负载。选择的顺序应当是：先写清业务 SLO 和故障域，再选协议；最后用 PoC 验证，而不是拿端口速率或平均 IOPS 代替结论。![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdXHGE5gN4yEnaicNWqtUtc4ba526NicibjmeEoRMQqWNbXxuISWXAsS2siab7rhOvUPR6cTp16T4OibJE1L6viajyD3IibOucRsdwvCfQ/640?wx_fmt=png&from=appmsg)

# 一笔 I/O 走过的两条路径

FC 路径中，主机 HBA 将 SCSI I/O 发往 FC 交换网络，再到存储控制器。每一段相邻链路都协商可接收的帧数量；发送端只有在确认下游仍有缓冲空间时才继续发送。这是 FC 的逐跳 credit 流控，而不是“整张 SAN 永远不会排队”的承诺。ISL 过载、慢排设备、端口超卖或错误分区，仍然会带来拥塞与延迟，需要容量规划和监控。iSCSI 路径中，发起端将 SCSI 命令封装为 iSCSI PDU，再经一条或多条 TCP 连接传输给目标端。它既可以和普通业务网共用物理网络，也可以使用独立 NIC、独立交换机或独立 VLAN/Fabric；这是架构选择，不是 iSCSI 协议的宿命。发生排队或丢包时，TCP 的拥塞控制与重传会参与恢复，因而网络设计、缓冲行为和超时设置更直接地影响业务观察到的时延。FC 通常更容易形成独立存储 Fabric；iSCSI 则要求团队明确把以太网的隔离、带宽、拥塞与故障域设计出来。无论哪一种，存储控制器队列、介质响应、主机队列深度和应用并发都可能主导最终时延。![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdW0uhba8SbvjXuBI3RnkiaCjcic4kFxpZ3n1ySvmv0dibib9AVsORnDmJeIWmbfTibicn8aBUAOkannWmTRzrqkGUVBfTWugVhEtLDL4/640?wx_fmt=png&from=appmsg)

# 不要用平均延迟替代业务体验

数据库和虚拟化真正害怕的常常不是平均时延，而是高分位时延和恢复窗口：请求在高峰是否突然排队？一条路径异常后，应用多久得到错误、多久恢复提交？这些问题不能仅凭“链路是 FC”或“以太网跑得很快”回答。对于 iSCSI，测试重点应是独立网络在备份、迁移、突发流量和链路异常下的 P99，而不是空闲网络上的单次峰值。对于 FC，也要在端口利用率上升、ISL 压力、控制器切换和路径故障下观察同样指标。只要尾部时延越过应用超时阈值，协议名称就不再重要，业务看到的都是交易重试、虚拟机 I/O 等待或服务降级。![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdVpthFPibzsDJE5rdjh3zicPJbk6OPEAsYEagdQZI9rVmlHvwv2ly9ICY09qAuDuB2Tq07F1S9k1iaQyUMBblqRtdjBqtCUUBy24M/640?wx_fmt=png&from=appmsg)DCB、PFC 与 ETS 也不应被当成“部署 iSCSI 的必选开关”。iSCSI 基于 TCP，本身能够处理丢包；很多场景会优先通过独立物理网络、独立交换机、合理带宽余量和 QoS 来控制风险。若网络团队选择 PFC/DCB，必须把它当作一项端到端的网络工程，验证优先级一致性、拥塞传播与故障时的退化行为，而不是假设打开 PFC 就自动获得确定性。

# 多路径故障切换由什么决定

FC 和 iSCSI 都需要主机侧多路径软件或虚拟化平台参与路径选择、失败判定和 I/O 重试。Linux 的 device-mapper multipath 会维护路径的活动或失败状态，并按策略选择可用路径。切换时间由多个环节共同决定：链路故障是否能立即被识别、主机驱动与 MPIO 的检查和超时参数、阵列控制器行为、文件系统和数据库的重试策略，以及故障是“拔线”还是更难发现的单向中断、网络黑洞或控制器异常。FC 不一定毫秒级、iSCSI 也不一定数秒级；这些都应成为验收数据。双 Fabric 的价值在于消除共同故障域。FC 的双交换网络只有在 HBA、线缆、交换机、存储端口和电源路径都独立时才真正有效；iSCSI 也需要两套独立 NIC、独立交换网络与独立目标端口，才能避免“两条路径其实经过同一台设备”的伪冗余。![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdVK9YcGm6XDGrV5jJrfrMHAp0ujqMjQ6bNXic9V1GR49Ee1y0FibKqDKibkJPtum1FyuwGU3Z2ASTVlxxySicSy9FLX8z4qE25elTw/640?wx_fmt=png&from=appmsg)

# 成本、距离与运维边界

FC 的成本包括 HBA、交换机端口和许可、光模块、分区治理与专门技能；其回报是存储网络的职责边界和运维模型更清晰。iSCSI 可以减少新增专用基础设施，但成本会转移到以太网容量、隔离设计、跨团队变更流程和可观测性上。跨站点场景要先看复制、RPO/RTO、仲裁和应用切换怎么设计，再判断是否需要把块协议跨站点延伸。FC 与 IP 都能通过相应的延伸或承载方案跨距离，但距离带来的往返时延、链路抖动、分区和恢复语义不会被协议消除；“能连通”不等于“可以承担同步写入”。

# 上线前验证清单

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdWb2gpIfMkf0e0ic9ASKuRf8ibpMszyFMxKReUSW4KjtBBZpDrTwF8Jic08TxhZMyfU4TNNKFVib1MaIAK0wnFOzna33RVniaDA0PcA/640?wx_fmt=png&from=appmsg)

  1. 写出验收线：按真实混合读写、并发和持续时间记录 P50、P95、P99，以及业务可接受的提交超时、错误率和恢复时间。
  2. 核对真实故障域：逐项画出两条路径经过的 NIC/HBA、线缆、交换机、存储端口、电源与管理面；同一设备上的两个端口不能算双活冗余。
  3. 分别注入三类故障：断开单路径、制造网络黑洞或单向异常、故障控制器或交换设备。记录主机、文件系统和数据库从异常到恢复的完整行为。
  4. 验证路径恢复：不仅测“切走”，还要测原路径恢复后的回切、负载分布、错误日志和是否出现重复提交或人工干预。
  5. 验证拥塞边界：在生产近似的备份、迁移或其他突发流量下观察 P99 和队列；FC 与 iSCSI 都需要这项测试。
  6. 明确运行责任：FC 检查 zoning、端口余量和 Fabric 健康；iSCSI 检查隔离、带宽、QoS、丢包与跨团队告警。两者都要把兼容矩阵、固件版本和变更回退写进上线条件。

FC 是独立存储 Fabric 的选择，iSCSI 是基于 IP 存储网络的选择。FC 同样可能遇到拥塞，iSCSI 经过合理设计也可以承载关键业务。能否进入生产，取决于团队是否把时延、故障域和恢复行为从"厂商承诺"变成了可重复验证的事实。
