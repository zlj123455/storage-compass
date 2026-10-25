# Q043：存储虚拟化解决什么问题，又增加什么复杂度？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/jcfhxZySJO-jyKx9hSNBdA
> 发表时间：
> 迁移时间：2026-10-25

假设一台虚拟机看到一块 2 TB 虚拟磁盘，可以在线扩容、迁移。几个月后数据库出现延迟抖动，团队看遍客户机磁盘、数据存储和阵列物理池，却没人能立刻说清请求落在哪个控制器、哪个池、哪组介质。

虚拟化解决资源分配和变更管理，却不消除物理资源；它只是把“管理设备”变成“管理映射、池和策略”。

存储虚拟化的价值，是把物理实现抽象成可池化、分配、迁移和保护的逻辑资源；代价，是映射、状态、共享预算和排障责任。只有关系可观察、可恢复、可演练，抽象才有用。

本文主要讨论块存储和虚拟机磁盘场景；文件、对象和带库虚拟化的映射与控制面并不完全相同。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdWRPn4zwYGr8AEI2A2ahBicMHFvYcdibFavlyPVePtB4dfCZib0iaPrOcDWwyqYq0L1DlVpQwgSUj7jlGwNR2TUtxfiaFicvg6XNRtiaw/640?wx_fmt=png&from=appmsg)

# 一块虚拟盘背后，不只有一块物理盘

应用写虚拟磁盘时，请求可能依次经过文件系统、虚拟磁盘、数据存储、LUN 或卷、存储池、控制器和介质。产品命名不同，共同点是主机只见逻辑地址，系统负责映射后端资源。

SNIA 将虚拟化定义为抽象一个或多个设备、系统或服务的功能，让外部看到统一实体。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdUrz1MSyLstMHO83k9jNuzz7tcDQDyDOxjNVem6P1hUalzyHBwGk5DyobibQN8ZaibPkvqATPrVSFbq2ofPqqwX3MMnGYvKBB2Ww/640?wx_fmt=png&from=appmsg)

# 它先解决三个管理问题

第一个是池化。多块设备形成共享池，逻辑卷按需取得空间，减少长期闲置，也便于纳入新增设备。

第二个是位置解耦。虚拟磁盘和主机映射可以不变，后端卷、控制器或介质可以迁移，扩容、替换和重平衡不必重做上层连接。

第三个是服务组合。精简配置、快照、克隆、复制和 QoS 可以围绕逻辑对象编排；但组合越多，策略状态和依赖也越多。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdUrz1MSyLstMHO83k9jNuzz7tcDQDyDOxjNVem6P1hUalzyHBwGk5DyobibQN8ZaibPkvqATPrVSFbq2ofPqqwX3MMnGYvKBB2Ww/640?wx_fmt=png&from=appmsg)

# 第一种复杂度：地址映射变长了

设备直连时，排查路径较短；虚拟化后，“哪个盘”至少包括客户机设备、虚拟磁盘、阵列卷、资源池和介质。

应用延迟、主机队列、虚拟化层统计和阵列计数器，未必对应同一对象或时间窗口。客户机利用率不能证明后端无拥塞，阵列总吞吐也不能证明单台虚拟机尾延迟正常。

我会保留业务对象到虚拟设备、卷或镜像、资源池和策略层的映射，再把 P99、队列、控制器和后台任务放到同一时间线上。

Ceph RBD 就是一个例子：镜像先存在于池中，再映射为主机块设备；映射命令需要指定池、镜像和用户。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdWgfE4YlJwHPoLjohBDSljdGQg1WRRaIWqlMSPHbNMoUgUmOAY1FxiaELtaogxuOnF2A0jVscVhoCc6L6EB8aHoKE4D9MFeJoug/640?wx_fmt=png&from=appmsg)

# 第二种复杂度：共享池变成共同预算

精简配置让逻辑设备可以先声明较大的容量，物理空间等实际写入时再从池中分配。Red Hat 的 LVM 文档说明，thin pool 可以按需提供空间，也允许超额承诺；因此必须持续监控数据和元数据使用率。

租户看到“卷还有空间”，不等于共享池能兑现所有未来写入。快照、克隆、迁移和重平衡还会与前台业务竞争控制器和介质；Q041 的 QoS 也只在覆盖的资源层生效。

容量和性能都要问“预算归谁”。卷级上限不等于租户总上限，池的余量也不能重复算作每个租户的可用空间。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdWEGtSTDFwSmlZSEib307Y1swkgyjWhic2PVyXkT2s4kzicx4gE5YQltGlMsRFUhg0sMcmKxAx7JK6x27XnehTLzte3icicWzZhFfOs/640?wx_fmt=png&from=appmsg)

# 第二种复杂度：共享池变成共同预算

精简配置让逻辑设备可以先声明较大的容量，物理空间等实际写入时再从池中分配。Red Hat 的 LVM 文档说明，thin pool 可以按需提供空间，也允许超额承诺；因此必须持续监控数据和元数据使用率。

租户看到“卷还有空间”，不等于共享池能兑现所有未来写入。快照、克隆、迁移和重平衡还会与前台业务竞争控制器和介质；Q041 的 QoS 也只在覆盖的资源层生效。

容量和性能都要问“预算归谁”。卷级上限不等于租户总上限，池的余量也不能重复算作每个租户的可用空间。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdWvWrjmjBU5A0ic3yCY3gOOMAXMiakGzicecLYZ8yzZicWZoxVCicGbJSfGWrTDLUzGOIryJnLhCZSUG78vIAm0PibGZ1Vetn15MpibJ8/640?wx_fmt=png&from=appmsg)

# 灵活变更不等于无风险变更

虚拟化让变更更容易发起，但代价并不相同：逻辑扩容和策略修改有时只是控制面或元数据变更；数据迁移与重平衡则会持续产生实际 I/O，并占用网络、缓存和控制器资源。扩大逻辑设备后，容量告警和 QoS 预算也可能需要同步调整。

我会把每项变更写成一条责任链：谁可以发起，修改了哪个逻辑对象，影响哪些租户，额外消耗哪类资源，失败时如何暂停或回退。只有“操作成功”而没有业务延迟、后端占用和回滚证据，不能算完成一次安全变更。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdVQ2b9otBiaCia8pduRs54icZvBFAEXHicsHdsds02ibyic0zvo687h50pkqqiaGc23yOAyxLPc8NjgvhwsRicvZET3oYc4NUCAc514Mj4/640?wx_fmt=png&from=appmsg)

# 逻辑设备不等于独立故障域

给不同业务创建不同虚拟卷，可以隔离命名和部分策略，却不会自动隔离控制器、网络、管理服务、元数据或电源。虚拟化本身也不自动提供冗余、备份或独立故障域；一个共享池发生故障时，多个逻辑设备仍可能同时不可用。

这也是存储虚拟化最容易被误解的地方：逻辑边界解决“谁看到什么、谁分到什么”，故障域解决“哪里坏了会一起受影响”。如果业务不能接受共同中断，就要继续向控制器、集群、机架和站点层追问，而不是只增加虚拟卷数量。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdWvmx27RED3S7XcPslRZEEmOnZA5mfLT5qicAKztNribKR0fDp4y4LdqOshWwFNul6FbFe8WUFevHgS3y4C2ae7wvugicp8h4NKc0/640?wx_fmt=png&from=appmsg)

# PoC 要验证映射与变更

我不会只验收“能创建一块虚拟盘”。测试至少要覆盖：创建和删除、扩容、快照与克隆、在线迁移、池接近满载、QoS 竞争、控制器或节点故障、权限撤销、恢复和回滚。

每一步都记录两类证据：业务侧的完成时间、P99、超时和可用性；基础设施侧的映射关系、池空间、控制器资源、后台任务和告警。特别要验证快照父子关系、迁移期间的性能代价，以及故障后策略是否仍然作用于正确对象。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdWjAm7xzzUhv4JMrwTVAlqE171Q47FnvmPoFJnLbe1wP6XoCwMk0HEOdQK0ClL64wCyIzgwC9EibOCNqaBHebpDwicjibE2RBZNTA/640?wx_fmt=png&from=appmsg)

我的验收标准是：团队能解释一条请求经过哪些层，能在变更前算清资源代价，能在争用和故障时定位共同影响范围，并能把逻辑对象恢复到正确状态。Q044 接着讨论，分层存储何时值得增加这层策略，何时只会让运维更难。
