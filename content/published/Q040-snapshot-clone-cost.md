# Q040：快照与克隆的内部机制和成本是什么？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/X3jL47f84O8gvRmjmzQfDw
> 发表时间：
> 迁移时间：2026-10-25

假设团队准备给数据库做一次版本升级。变更前，管理员点下“创建快照”，几秒钟就完成了；测试团队随后从快照生成一个克隆，也几乎不用等待。这个体验很容易让人觉得：快照和克隆既快又省空间，成本接近于零。

三个月后，快照越积越多，存储池容量增长得比业务数据快；删除老快照时，后台又出现持续的合并或回收任务。空间占用、写入开销和清理成本，开始在使用过程中显现。

空间高效快照和共享块克隆，通过共享基线、保留必要的数据版本，省下创建时的全量复制；真正要评估的，是哪些版本必须留下、写入增加了多少开销，以及何时能够回收。本文重点讨论这类实现；完整克隆还需要单独计算复制时间与容量。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdXHbYUj82VS9ScHyQprB4MnicLWmT0mN2TTr2EKtIFxhDrodqLuxzhvMZwM6kSiahnaDuey7gcoe8WfHIIKBwWNn3iclRT1yM8Ctk/640?wx_fmt=png&from=appmsg)

# 快照和克隆省下的是什么

快照通常表示某个时间点的数据视图。在很多实现中，它是只读的，用来回看、恢复或作为克隆的起点。克隆则通常是一条可写分支：刚创建时与源数据共享大量物理块，之后随着写入逐渐分化。

这里最容易混淆的是“逻辑独立”和“物理独立”。应用可以把克隆当作一套独立数据使用，底层却未必复制完整容量。以 OpenZFS 为例，克隆从快照生成，初始额外空间很少，但仍依赖其起源快照。

因此，一个 20 TB 卷在几秒内生成共享块克隆，通常只是建立了新的引用和映射，尚未写出另一份完整数据。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdWc80SF8WI45yINMcZdibUdj26E1wiahlFKkpB2YXZUTuDDjdFAFsz8jNBrtkVdDJvFv58awK6u52ypMG8U0icx3oLAoQrDCjl7Eg/640?wx_fmt=png&from=appmsg)

# CoW 与 RoW：旧数据到底留在哪里

理解写入路径，可以先区分“覆盖前保存旧块”和“把新写入送到新位置”两种行为。

传统快照语境中的 Copy-on-Write，常指覆盖前先复制旧块。以 Linux device-mapper snapshot 为例，源卷第一次覆盖某个尚未为该快照保存的块时，先把旧内容复制到 COW 区域，再完成写入。对这个快照而言，后续反复覆盖同一块，无须把每个中间版本都保存下来。

Redirect-on-Write 则把新数据写到新位置，旧块继续供快照引用。要注意命名差异：OpenZFS 也采用异地写入、更新块树的方式，但官方称它为 Copy-on-Write。这里区分的是行为，CoW 和 RoW 并非跨产品统一、互斥的分类。

还要区分系统原有成本与快照新增成本。OpenZFS 即使没有快照，也会分配新块、更新映射；快照额外保留旧块，并带来空间压力和生命周期管理工作。不能把底层写入成本全部算到快照头上，也不能只凭机制名称判断性能。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdUa0iaeh9mUeaa2vCaor3PgwHEdZfJjZrZyz4EdJTAicajqBvzKBFcP1FDQwTxIVUy4Cqc9vxEibc8Y3zwoP3UeQvQm2Uu77Tibc90/640?wx_fmt=png&from=appmsg)

# 成本取决于变化量和保留时间

容量成本取决于保留策略和变化模式。低变化量的大卷可能只保留少量旧块；频繁覆盖的小卷，如果同时保留多个时间点，也可能积累大量历史版本。

例如，同一逻辑地址先后写入 A、B、C，两个快照分别保留 A、B，当前数据为 C，就要保留这些不同版本；如果只有最早的快照，中间版本 B 未被其他对象引用，就不必一直留下。所以，累计写入量不等于快照占用，按变化地址去重也可能漏算。源卷删除的数据，同样可能因快照引用而无法释放。

规划时要统计源卷、各保留点和克隆共同引用的不同物理块，同一共享块只计一次；评估快照额外占用，则看哪些块仅因历史版本保留而不能释放。还要考虑分配粒度、压缩去重、元数据和回收余量。克隆自身的新增与改写也会增加占用。

性能成本还取决于映射结构。逐层查找的增量链可能随深度增加读开销；Linux thin provisioning 则使用统一数据结构，避免这种随链深退化的查找路径。其文档提示的是“大量快照记录大量变化时可能需要更多元数据”，不能简单推成“共享越多越慢”。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdVrv1kt7NdshxiaiavhW3iblB33mfxaH6nErpugicvOhEhHWiasia4fFe1Fn4kia8k7V4H8hkpKowBHtonZyVib8YYfGckh2SaEaveZomQ/640?wx_fmt=png&from=appmsg)

# 为什么删除可能比创建更慢

创建快照往往只需建立新的元数据关系；删除快照却需要回答一个更难的问题：哪些数据块已经无人引用，哪些仍被其他快照或克隆依赖，哪些增量还要合并到父层？

不同产品的删除路径差异很大。有的只更新引用并异步回收空间，有的需要合并增量、重写映射或执行链条整合。VMware 的官方知识库提供了一个具体例子：删除虚拟机快照会把 delta 中的数据合并到父盘或基础盘；合并是 I/O 密集型操作，耗时受增量大小、快照数量和底层存储性能影响，期间性能可能暂时下降。

这不代表所有阵列都会“全量回写”，但说明删除入口很快，不等于后台工作已完成。容量接近满载时执行大规模合并尤其危险：前台仍在写入，后台也可能需要额外空间和带宽。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdVeB1e04zLwYkoaSWpCuibnxNNvoicGI5SicjShyGGsD3T66BLuNIlVumL1Z1dMfD4R3QFtqSBeEFkpwtVkiabgn1txUo8sPM5YECQ/640?wx_fmt=png&from=appmsg)

# 快照不是备份，崩溃一致也不是应用一致

快照可以成为备份流程的一部分，但本地快照不自动提供独立保护。与生产卷共享阵列或管理域时，设备故障、误操作和账号失陷仍可能同时影响两者。备份方案还需评估故障隔离、保留策略和恢复链路。

一致性也要单独判断。崩溃一致类似突然掉电后的磁盘状态，应用可能需要日志恢复。若数据库文件和日志跨卷，必须通过一致性组或应用协调形成一致的时间点；各卷分别快照成功，不保证整套应用达到崩溃一致。

应用一致还需要应用参与。Windows VSS 是一种实现：writer 配合完成准备、刷新缓冲和冻结写入。其他平台可以使用数据库备份接口或应用钩子，不能把 VSS writer 当成通用前提。

因此，“快照成功”只证明存储系统生成了一个时间点视图，不等于数据库一定能恢复，更不等于它已经成为备份。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdV1oTibYm200OfVgenXS9UoialCKicR8LX97RlibxO29GWERKPOGRXcfsaXJuDn4aJCRSm9pvZVjBqKmpFEbsiaianLVic9w2sGpJwRics/640?wx_fmt=png&from=appmsg)

# 我会怎样监控和验证

我会同时监控快照数量与年龄、变化率、物理占用、回收进度和池余量；采用增量链的产品再看链深。将 P99 延迟与后台 I/O 对齐观察，并分清界面显示的是引用容量、独占容量，还是删除后预计可回收容量。

PoC 先在相同负载、相近池占用率下，对比有无快照的性能，再观察保留旧版本、池占用上升后的表现。生命周期测试覆盖持续写入时创建、读取历史快照、写入克隆、删除老快照、低余量下回收，以及故障恢复后的跨卷与应用一致性验证。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdXwkqcxSX5omiatpzGm7dVPWwqWMlRABnwicIb1Yv1ozrWbqrUuctk1FpfV5QbvgRUN0BpEpWs7mL4lJ1IkE3bSsb3Zia1VvSzhls/640?wx_fmt=png&from=appmsg)

还要记录产品边界：最多支持多少层、克隆能否脱离父快照、删除是同步还是异步、空间何时真正返还、后台任务能否限速、容量不足时会暂停还是失败。这些答案应来自目标版本的文档和实测，而不是从另一家厂商的机制类推。

我的验收重点，是保留策略下的实际占用、业务延迟和可恢复性。下一篇讨论 QoS 时，再看多个业务与后台任务争抢资源，怎样避免一个工作负载拖慢整池。
