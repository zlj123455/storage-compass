# Q042：多租户存储如何隔离性能与数据访问？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/V7mfdw-OE9urj5aQBL5EEw
> 发表时间：
> 迁移时间：2026-10-25

假设财务、研发和备份团队共用一套存储，各自有独立卷和账号。平时相安无事，研发批量导入数据后，财务查询开始变慢。恢复演练又发现，某个部门账号竟能把其他部门的快照克隆出来。

前一个问题是资源争用，后一个是权限越界。给研发限速，解决不了克隆权限；收紧权限，也不会让共享队列自动空下来。

多租户隔离，要让身份、数据归属、访问权限和资源预算对应起来，同时明确共享故障的影响范围。分了卷、建了账号，只完成了其中一部分。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdWBRCNbRke8fD0jhCLg0aCg6IbUFcJu4Z6GKt3DGw62kicYUr2IFc5wvhMsyxSw55iaX8rOIjsmEZLPya3hltZ1pevicibhwY78YcM/640?wx_fmt=png&from=appmsg)

# 数据放在哪，与谁能访问，是两件事

命名空间先解决“这是哪个租户的数据”。例如 Ceph RGW 允许不同 tenant 使用同名桶；但请求能否读取对象，仍要通过对应的授权检查。桶名分开，不代表所有访问路径都已经检查过。

访问边界还取决于协议。文件服务要核对共享或导出规则、身份映射和文件权限；块存储要检查主机到 LUN 的映射，卷内文件权限通常由主机负责；对象存储则要检查身份凭据、桶策略和对象权限。

我会用租户自己的账号验证读、写、列举和删除权限，并检查显式授权的跨租户共享。网络分段可以减少可达范围，但请求能到达服务后，仍需要服务端判断它有权做什么。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdWFkpXJXgs5vvNugcC88FpsM0xS24AjoUzsRDRpIvG1plbjTcFQZGGb1DXibbibjdiaObeV1zbxxG5mcJS5vzwFnvbe2oGvt9lVicA/640?wx_fmt=png&from=appmsg)

# 管理员能管到哪里，也属于隔离范围

业务账号读不到别人的文件，租户管理员却能修改别人的导出规则，边界依然有缺口。快照、克隆和备份恢复尤其要检查：它们可能把原本受保护的数据变成另一份可访问副本。

ONTAP 将集群管理员与 SVM 管理员区分开：后者管理自己的 SVM，具体能力受角色限制；集群管理员的范围更大。因此，租户之间的权限隔离，不能直接推导出对平台管理员也保密。

加密也要说清保护对象。服务端静态加密保护落盘数据，正常获准读取的请求仍可获得明文。若还要求平台管理员无法读取，就要进一步设计客户端加密、密钥控制和恢复流程。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdVLK5fvyTk1gALxTQxoDibgmbdrLIsOPicMTff1ss0yzzSlWeZWkmNdIn7LFLXkRV9oAQ5mDyf7Dsn4OSfzs5UeuqwnMDboviaCG0/640?wx_fmt=png&from=appmsg)

# 性能预算要跟着租户走

Q041 已讨论 QoS。放到多租户场景，关键是额度到底分给谁：限制单个卷，未必限制了拥有多个卷的租户总量；允许租户自行创建卷，却没有总预算，资源消耗就可能继续扩大。

请求需要先归入受控对象，再由调度器按 IOPS、带宽等额度安排服务机会：过量请求延后放行，关键业务在产品支持和能力允许时获得最低保障。这样才能把租户身份转换为实际的资源约束。

因此要确认产品支持的控制层级，再决定租户共享额度与卷级约束如何配合。不能默认两种策略可以任意叠加。ONTAP 的共享与非共享策略组就有不同计量方式，具体限制还需核对版本。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdWWVTwIhHgePHbstspEdrVBLKg7Ac15gNs2RQQkeyCE2mpHxyHSAckXWwoaLL7yvNdibBiaQz4hC63kMXyuJiaIiaxbDddJjHyCMicU/640?wx_fmt=png&from=appmsg)

容量也需要预算。一个租户持续写入，可能耗尽共享池；大量小对象还会增加元数据压力。Ceph RGW 提供用户和桶的容量、对象数配额；一个租户若有多个用户，还要确认总量如何约束。配额限制使用量，不能当成已经预留了物理空间。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdUBgb8ee1f53VibPlC7RicXS4qrSqzlkia6ZW5QDu9dCK63pKfWmWphdNicLx6zWLkObT65MJDnsgKwq4A5dDP4PSo4u63UoeUssr4/640?wx_fmt=png&from=appmsg)

我还会单独核对快照保留、复制和后台恢复的资源归属。租户看板里的前台流量，未必包含它触发的全部成本。是否满足性能目标，要看混合负载和故障后的可用能力。

# 共享硬件，仍然可能共同停机

即使租户之间访问权限正确、限速有效，只要仍共用控制器、网络或管理服务，一次故障或升级就可能同时影响多个租户。逻辑边界不会自动生成独立故障域。

对于同一企业内、可以接受共同维护窗口的部门，共享资源通常更容易提高利用率。若业务无法接受共同中断，我会评估专用资源或独立集群，并继续检查电源、交换网络和管理账号是否仍然共用。

隔离越强，容量闲置、监控和恢复管理的成本可能越高。选择依据应该是可接受的影响范围，而不是租户数量本身。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdVLsjZx0K6RzbgYjyKRzcHte6jHP4TGE64yvZP8JxDCA6U0rxnc7MYzKndFDky8Th3iaiavVjUSicL4jYeGoeTLMa1YzcU2q3xEibQ/640?wx_fmt=png&from=appmsg)

# PoC 要让一个租户主动碰边界

准备两个测试租户，在授权的测试环境里，用 A 的身份尝试访问 B 的卷、文件、对象和快照，同时验证 A 自己的正常业务能够完成。只看管理界面隐藏了哪些对象，不足以证明服务端拒绝越权请求。

再让 A 制造大块传输、小请求突发和容量增长，观察 B 的事务 P99、超时率与完成量，同时记录 A 的限速等待、任务完成时间和配额拒绝行为。只让 B 的延迟好看，却让 A 长期无法完成任务，同样不能验收。

迁移、故障切换、备份恢复和权限撤销后，还应复测，并保留能追溯租户、对象和操作结果的日志。特别要确认恢复出的数据仍属于正确租户，旧凭据按约定时效失去访问能力。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdXV2JwvGXiaICd5Ibs9ib3swBLWKpfPwia3jNITu1SsBQ3dhEzhrVTDQkGwEmIymyahuvs6SA7t47NcicoyFxo8XJt3DOyiaWmRNiaE8/640?wx_fmt=png&from=appmsg)

我的验收底线是：未经授权的访问被拒绝，竞争时业务守住约定目标，共同故障的影响范围也已被接受。Q043 接着讨论，存储虚拟化如何组织这些资源，以及它带来的管理复杂度。
