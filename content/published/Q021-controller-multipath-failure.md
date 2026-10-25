# Q021：多路径如何避免单链路或单控制器故障？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/KxGVVuScoyo1zXpldxHS3Q
> 发表时间：
> 迁移时间：2026-10-25

一次月末跑批中，数据库主机的一条前端路径出了问题。存储管理员很快确认：另一条路径仍然在线，卷也没有消失。可业务侧先看到提交变慢，随后开始报超时。等路径恢复后，团队才发现自己一直把“有两条线”理解成了“业务不会中断”。这是一个综合后的典型复盘场景，不对应某个具体客户。问题不在多路径没有工作，而在它的工作范围被想得太大。**多路径能把同一存储对象经由多条路径呈现为一个逻辑设备，并在可用路径间选择或重试；但只有路径真实独立、故障能被识别、备用路径可访问，而且应用愿意等到切换完成时，它才能避免单路径故障扩大为业务中断。**路径数量不是恢复能力。真正要问的是：一条 I/O 从主机到阵列，经过了哪些共同部件？失效发生后，主机多久发现、在途 I/O 如何处理、应用又能等多久？![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdVe1ggUw85lAlRRnicgC26rHEVLZtGgQpj8sZ9o7rEjxVhiao29TTlfCaTfTn3c2YMKZYTIJCxPsFS14qHX2UtaVagjF3WmeicOKg/640?wx_fmt=png&from=appmsg)

# 多路径不是两根线，而是一条 I/O 的备选路线

一块远端卷通常可以经由不同的 HBA 或网卡、链路、交换机 Fabric、阵列前端端口与控制器被主机访问。多路径软件的工作，是把这些通向同一存储对象的路径收敛为一个主机可用的逻辑设备，并决定 I/O 应走哪一条。以 Linux NVMe 为例，multipath 会将具有相同标识的 namespace 整合为一个块设备；主机再按配置的策略从底层路径中选择。支持 ANA（Asymmetric Namespace Access）时，主机会区分优化、非优化或不可访问的路径，而不是把每条路径都视为完全相同。这解释了两个常见误会。第一，多路径不只是在故障时“换一根线”，正常情况下也可能按优选状态、NUMA 亲和性、轮询或队列深度选择路径。第二，主机看见两条路径，不代表两条路径都能独立承担业务；它们可能在更靠后的某一层汇合。![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdVjDwicia644q4GzvzJJ5ibIwm5vAXyCBhCDRcUjHEPFxrj4Uzn6TtW3eIw3gW2cct25KCBdMaOeic2noFZcRz64lZAMOiaYQuwzufE/640?wx_fmt=png&from=appmsg)

# 先找共同故障点，再谈冗余

两条线接到同一张交换机，依然怕交换机；两张网卡插在同一块故障域内，依然怕主机侧适配器；两条路径最终落到同一阵列前端端口、同一控制器或同一供电域，也依然会一起失效。因此，设计多路径时，图上不能只画 A 路和 B 路。应把每一段都标出来：主机 HBA/NIC、线缆或光模块、交换机与 Fabric、阵列端口、控制器、卷的归属关系，以及这些部件共享的供电和控制平面。单控制器故障尤其容易被误判。若阵列能够让另一控制器接管该卷，并且主机到另一控制器的路径已经可见、状态正确，主机多路径才有机会继续提交 I/O。若控制器故障使卷对所有路径都不可达，或者备用控制器没有足够资源与正确的访问状态，主机侧配置再完整也无法把不存在的目标路径变出来。![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdUJDgQJ8lpuiaABz250Iug5Xv9Eia8O4b3TNtlBv5f22DDCIROwlWoONoItk5fS2KY10MKoSDstsrA0ZyToCSwbW6GXHalS6FJWA/640?wx_fmt=png&from=appmsg)

# 切换已经发生，为什么业务仍然超时？

一条路径发生硬断链时，主机通常比较容易收到链路异常；但单向丢包、端口半失效或目标端卡住时，请求可能先静静等待，直到超时机制认定这条路不可用。识别方式不同，业务感受到的等待也不同。识别之后，在途 I/O 还要经历重试、重排或失败返回。Linux 的 NVMe 诊断接口可观察命令重试、故障切换、因没有可用路径而重排或失败的计数。 这说明“已经切到另一条路径”只是路径层的一项事件；数据库的连接超时、文件系统的错误处理、事务是否重复提交，仍在更上层发生。对传统 SCSI/dm-multipath 环境，这个边界更直观：当所有路径都不可用时，`queue_if_no_path` 这类策略会让发起 I/O 的进程持续等待路径恢复；另一类策略则可能在重试后让 I/O 失败。两者没有绝对好坏，关键是应用、文件系统和运维流程是否知道自己会看到“等待”还是“错误”。s)所以“设备已经切换成功，为什么数据库还卡住”并不矛盾。设备层在做路径选择，应用层在等待自己的超时与恢复逻辑；两条时间线必须一起验证。![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdXS1lpGMu1g8g7twcJsMQvk9pHNUkI84K1J8YR1WbhibCElF28ezHTviaYrictdcnLdyHM9ZAy3PryYj5SpLap74FFd1A31HUuDia4/640?wx_fmt=png&from=appmsg)

# 不能只做一次拔线测试

拔掉一根线是必要测试，但它最多证明其中一种硬故障能够被识别。真正的生产演练至少要分开验证下面几类事件：![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdXA8zS6zQRKaWdLq5fWUeAWbAicibMAQ2x295Wjlaia3PXqB1zRyyTIu9ITb6g5kz8LUFSeicXEW9sHKamA9I9DpiaxEmfMhJwKxKSQ/640?wx_fmt=png&from=appmsg)

  1. 拓扑核对：确认两条路径从主机到控制器经过的 HBA/NIC、交换机、端口和供电域确实不同。
  2. 业务基线：在生产等效负载下记录应用提交时延、主机路径状态、重试与错误日志；没有基线，就无法判断切换是否真的影响业务。
  3. 单链路故障：断开一条链路或禁用一个端口，观察路径状态变化、在途 I/O 和应用感知时间。
  4. 单向异常：模拟只发不收、报文黑洞或目标端无响应，验证超时、重试与切换，而不是只看物理链路是否 down。
  5. 目标端口或控制器事件：验证卷的访问状态、优选路径、控制器接管和性能余量，而不是只确认另一端口亮着。
  6. 路径恢复：确认恢复后的路径是否重新可用、是否错误地抢占流量，以及业务性能能否回到基线。
  7. 全路径不可用与数据一致性：明确此时应用应等待、报错还是切换服务；检查事务状态、重复执行和人工恢复步骤。

运行 dm-multipath 的 Linux 系统还可以订阅路径失败与恢复事件。内核会为 `PATH_FAILED` 和 `PATH_REINSTATED` 生成对应的 device-mapper uevent；这类证据比“监控页面曾经是绿色”更接近一次可复盘的切换过程。![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdWvvjp5mfVKNtjzsL2c8FhfzkibnOsSnlsW817KuCJO3yew2OvcdcNoRLoqSKyK1KjQk3QLLHuRaIUuf9NHuxJfnOPCStsVx1SU/640?wx_fmt=png&from=appmsg)多路径解决的是主机到远端存储之间的路径可用性，并不替代备份、复制、双活或站点级容灾。更重要的是，它也不能替应用决定一笔超时的写入究竟有没有落盘、是否能够安全重试。真正可用的多路径，不是拓扑图上多画一条线，而是在一次可重复的故障演练后，团队能回答：哪一层失效、主机如何切换、业务会等多久、谁负责判断写入结果，以及下一步如何恢复。
