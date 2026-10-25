# Q049：双活、同步复制和异步复制有什么区别？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/-fE-C1eVzfrTuVkJ96P_PA
> 发表时间：
> 迁移时间：2026-10-25

假设一套数据库跨两地机房部署。方案会上，有人说“用了同步复制，就是双活”；也有人建议改成异步复制，认为业务照样能自动接管。直到跨站链路中断，团队才发现：两地都有数据，并不能回答哪一地还能写、用户要等多久。

这三个词其实不在同一条比较线上。

同步和异步复制，回答的是远端副本何时进入写入确认路径；双活回答的是业务如何在两地提供服务。数据能否保住、业务能否继续、故障后多久恢复，需要分别设计和验证。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdXMexgT4hGw05XvArVAUFTliagF35zwdTmdYMxiaYo3ZFJw4EH6RdeLSGsGfNn4p84bX2GCszlJVbPEn1QibNPSticpialm5WObx2Tk/640?wx_fmt=png&from=appmsg)

# 跟着一次写入，看远端何时参与

先让应用向 A 站写入一条记录。同步复制下，A 站不能只因为本地接收了数据就向应用返回成功；它要等 B 站按产品约定完成远端确认。跨站往返时延和 B 站处理能力因此进入前台写入路径。微软 Storage Replica 的同步模式就是先获得远端日志确认，再确认应用写入。

但“远端确认”究竟表示写入受保护缓存、持久化日志，还是最终介质，必须查目标产品的确认语义。应用事务提交还可能涉及数据库日志、多个卷和上层协议；不能把一次块写确认直接说成整套应用已经一致。

异步复制则允许 A 站先完成本地确认，再把变更送往 B 站。这样，远端链路的往返通常不再逐次决定前台写入完成时间，但两站之间会有待传输或待应用的变更。A 站若在这些变更到达可恢复点前失效，B 站可能缺少已经向应用确认过的数据。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdUh8QcWLTqXDlPjGTIJoUqX5Z300B4wQGw65lZxgGopY3GvTk5J0aE7Fspshn2JviaoER5ncBoLRsjDwJBDzCTlLJcAghKKUB5A/640?wx_fmt=png&from=appmsg)

异步也不是一种固定的“每隔几分钟复制一次”。例如 Ceph RBD 可用日志或镜像快照进行异步镜像，两种方式的传输和故障恢复粒度不同。讨论 RPO 时，应看可恢复的一致性点及其年龄，而不是只看网络队列里还剩多少字节。

# RPO 很小，不代表 RTO 也很小

在复制健康、故障范围符合设计、已确认写入确实受到远端保护的前提下，同步复制可以争取已确认写入不丢。链路断开后系统是暂停写入、只让一站继续，还是降级为本地写入，各产品的策略不同；若允许失去远端保护后继续写，“RPO 为零”就不能无条件沿用。

异步复制要接受非零的数据损失窗口，但窗口不是采购表上的一个静态数字。写入峰值、链路抖动、远端回放能力和一致性组范围都会改变故障时真正能恢复到哪里。

即便 B 站拥有完整副本，数据库进程、主机挂载、IP 或路由、客户端连接都可能尚未切换。RPO 问“可能失去多少数据”，RTO 问“业务多久恢复”；同步复制主要改变前者的边界，不会单独交付后者。微软同样把伸展集群的自动切换与普通集群间复制的人工接管区分开来。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdUh57J8BQh9KPb5ccH10DZNAwmnQJEkaibCma3gWRP3YufHpBsEMx5e1gx9k0gY2MYicOowTXxwW8AWGrJ42uuutErzDYn1CO51U/640?wx_fmt=png&from=appmsg)

# 双活不是“两个副本随便写”

“两地双活”先要问活的是哪一层：A、B 两站各承载不同业务，还是同一业务能从两站接入？前一种可以让不同数据集各有主站；后一种还要处理主机路径、应用路由、写入协调与冲突边界。两台设备都开机、两个机房都有副本，不足以证明同一数据集可同时服务。

以 NetApp SnapMirror active sync 的 SAN 方案为例，对称双活可让两地的主机走各自本地的优化路径，但背后仍有同步复制、一致性组和仲裁机制。产品文档明确区分对称与非对称访问，也没有把“双站可接入”解释为两份副本能脱离协调、独立修改同一数据。

反过来，同步复制也不必然是双活。A 站写、B 站仅作备用，同样可以同步；Ceph 的双向异步镜像，也可以是 A 站某些映像为主、B 站另一些映像为主，而不是同一映像两地同时主写。判断方案时要画清每个业务和数据集的服务位置，不要只看拓扑宣传图。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdV6NXkKDzwzfLhhqUHGzLkCib0jz7jZdiclfdksXaSiakoAGwouTl9oCD0yObrgkDvjQb9wmsGuwPu0AvaXTrnnV1Q01TXTcj4kbs/640?wx_fmt=png&from=appmsg)

# 真正棘手的是：两地都活着，链路却断了

站点故障相对直观：一边确实消失，另一边按规则接管。跨站链路分区更危险：A、B 站都还在运行，却无法确认对方状态。如果双方都把同一数据集当作自己的可写主副本，恢复链路后就可能面对无法自动合并的冲突。

因此，双活方案需要回答“失联时谁还能写”。见证节点、仲裁和隔离机制用于限制写入所有权；在某些分区条件下让一侧暂停 I/O，是为了防止数据分叉。NetApp 的仲裁者文档就把它用于决定哪份副本继续服务、哪份停止 I/O。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdVzDQZJqgvVWmHy8U6fR7qGsoqLzticQ8iaDpdeiafed8Hic4nWuyNvsAwH4H6Wn6ib7Qialzkhzehptpn7g7gDFc9LxibZnStS9EcO9g/640?wx_fmt=png&from=appmsg)

接管之后还有回切。原站恢复上线时，谁是新的权威副本？未同步的数据如何补齐？业务何时可以安全迁回？这些动作既影响恢复时间，也可能再次触发前台延迟。只演练“把一台设备关掉”，还不足以证明跨站方案可用。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdVGibaJJ9tsO5c77WltnIqNWvcMRLyFW4UILlJFdw0j0E86plickaSNW5HmwfKtqlmzerI5HibQkWEHocoYJdKPUl54AB7M605icIk/640?wx_fmt=png&from=appmsg)

# 我会怎样选和验收

如果业务能容忍短暂的数据损失，先用目标 RPO 倒推异步复制方式、积压告警和一致性点，再安排接管。如果已确认写入不能丢，再评估同步链路的时延、带宽与断链策略；若还要求两地同时承载同一业务，还需核对访问路径、仲裁、主机与应用兼容性。

PoC 不只测正常状态的复制延迟。我会固定业务负载，分别切断复制链路、关闭一个站点、恢复链路并回切；每次记录写入 P99、确认点、复制积压、哪一站能继续写、实际恢复点、客户端重连时间和数据一致性。还要故意让仲裁节点不可达，验证系统究竟保服务还是先保正确性。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdUjP3EYAIeHwMfuPEuYxGE1svKJEuSheZykX7p9CU0fvhZKAnCoo6S4Ukf8fibM1icaTDw4WJsTiat9yXljvyqFFcMJD47icxYWeKs/640?wx_fmt=png&from=appmsg)

验收标准不是界面上写着“双活”或“RPO 0”，而是一次业务写入从提交到确认、故障后到恢复，都能在约定边界内被解释和复现。复制解决副本更新，双活解决服务拓扑；独立备份仍要另行设计。本文讲的是常见架构边界，具体确认语义、仲裁、双站访问和应用一致性，要按目标版本与故障演练核对。

想进一步理解远程复制与容灾，可以读张冬《大话存储（终极版）》第 17 章，补齐同步、异步复制与故障切换的底层概念。
