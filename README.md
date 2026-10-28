# 存储罗盘

面向企业架构师、IT 负责人和存储选型团队的公开知识库，聚焦企业存储架构、可靠性、性能与选型判断。

## 快速入口

- [在线阅读版](https://zlj123455.github.io/storage-compass/)
- [联系方式 / 交流](https://zlj123455.github.io/storage-compass/card/)
- [企业存储架构师 100 问](content/100-questions/README.md)

### 企业存储架构师 100 问（65 篇）

- [Q001：Q001：企业为什么需要专业存储？](Q001-storage.md)
- [Q002：Q002：NAS、SAN 与对象存储的差别是什么？](Q002-storage-object.md)
- [Q003：Q003：一个 I/O 请求进入存储系统后发生了什么？](Q003-storage.md)
- [Q004：Q004：企业存储为什么不直接使用普通服务器硬盘？](Q004-storage.md)
- [Q005：Q005: 有备份、有副本，RAID 今天还解决什么问题？](Q005-raid-ai-replication.md)
- [Q006：Q006：块、文件、对象，别先问谁更快](Q006-object-file.md)
- [Q007：Q007：容量、性能、可靠性、成本，别各选各的](Q007-capacity-cost.md)
- [Q008：Q008：管理面绿灯，业务就一定正常吗](Q008-business.md)
- [Q009：Q009：同样 100TB，为什么存储价格差这么大？](Q009-storage-cost.md)
- [Q010：Q010：存储选型前，业务方必须提供哪些数据？](Q010-storage-selection-business.md)
- [Q011：Q011：IOPS、吞吐量和时延应如何一起理解？](Q011-latency-iops-throughput.md)
- [Q012：Q012：存储的可用容量为什么常常小于采购容量？](Q012-storage-capacity.md)
- [Q013：Q013：数据增长率如何影响企业级存储架构？](Q013-storage-data.md)
- [Q014：Q014：什么是 RPO 与 RTO，它们如何影响存储设计？](Q014-rpo-rto-rto-storage.md)
- [Q015：Q015：企业存储项目最常见的误区是什么？](Q015-storage-pitfalls.md)
- [Q016：Q016：NFS 是什么，适合哪些企业文件业务？](Q016-nfs-file-business.md)
- [Q017：Q017：SMB 是什么，和 NFS 的主要差异是什么？](Q017-nfs-smb.md)
- [Q018：Q018：iSCSI 与 Fibre Channel 如何选择？](Q018-iscsi-fibre-channel.md)
- [Q019：Q019：NVMe over Fabrics 解决了什么问题？](Q019-nvme.md)
- [Q020：Q020：NVMe/TCP、RoCE 和 Fibre Channel-NVMe 的取舍是什么？](Q020-fibre-channel-nvme.md)
- [Q021：Q021：多路径如何避免单链路或单控制器故障？](Q021-controller-multipath-failure.md)
- [Q022：Q022：文件锁、缓存一致性与协议选择有什么关系？](Q022-cache-protocol-file.md)
- [Q023：Q023：客户端挂载参数为什么会改变业务体验？](Q023-mount-business.md)
- [Q024：Q024：小 IO、大 IO、顺序与随机访问如何影响协议表现？](Q024-protocol.md)
- [Q025：Q025：什么是 RDMA，它在存储网络中何时值得使用？](Q025-rdma-storage.md)
- [Q026：Q026：存储网络的 MTU、拥塞与丢包如何影响时延？](Q026-mtu-storage-latency.md)
- [Q027：Q027：为什么不能只看链路带宽判断存储性能？](Q027-storage-bandwidth.md)
- [Q028：Q028：Kubernetes、数据库和虚拟化分别常用哪些存储接口？](Q028-kubernetes-storage-virtualization.md)
- [Q029：Q029：对象存储的 S3 API 与传统文件系统如何协同？](Q029-s3-api-storage-object.md)
- [Q030：Q030：协议迁移时如何降低业务中断风险？](Q030-migration-protocol-business.md)
- [Q031：Q031：存储控制器在系统中做什么？](Q031-storage-controller.md)
- [Q032：Q032：缓存如何提升性能，又带来哪些一致性风险？](Q032-cache-consistency.md)
- [Q033：Q033：写入确认发生在缓存、日志和磁盘的哪个阶段？](Q033-cache.md)
- [Q034：Q034：元数据为什么会成为文件系统的性能瓶颈？](Q034-metadata-file-data.md)
- [Q035：Q035：条带化、镜像和纠删码如何改变数据路径？](Q035-erasure-coding-striping-data.md)
- [Q036：Q036：全闪存阵列的性能瓶颈通常在哪里？](Q036-storage.md)
- [Q037：Q037：读写放大是如何产生的？](Q037-write-amplification.md)
- [Q038：Q038：数据缩减如何影响容量估算与性能？](Q038-data-reduction-capacity-data.md)
- [Q039：Q039：精简配置为什么可能带来容量耗尽风险？](Q039-thin-provisioning-capacity.md)
- [Q040：Q040：快照与克隆的内部机制和成本是什么？](Q040-snapshot-clone-cost.md)
- [Q041：Q041：QoS 如何防止一个业务拖慢整个存储池？](Q041-qos-storage-business.md)
- [Q042：Q042：多租户存储如何隔离性能与数据访问？](Q042-storage-multi-tenant-isolation.md)
- [Q043：Q043：存储虚拟化解决什么问题，又增加什么复杂度？](Q043-storage-virtualization.md)
- [Q044：Q044：分层存储何时有效，何时只会增加运维负担？](Q044-storage-tiering.md)
- [Q045：Q045：如何画出一个业务的端到端 I/O 路径？](Q045-business.md)
- [Q046：Q046：RAID 5、RAID 6 和 RAID 10 如何取舍？](Q046-raid-ai.md)
- [Q047：Q047：磁盘重建窗口为什么是可靠性风险？](Q047-rebuild.md)
- [Q048：Q048：纠删码适合哪些容量型负载？](Q048-erasure-coding-capacity.md)
- [Q049：Q049：双活、同步复制和异步复制有什么区别？](Q049-active-active-replication.md)
- [Q050：Q050：备份、快照和复制为什么不能互相替代？](Q050-snapshot-backup-replication.md)
- [Q051：Q051：勒索软件防护在存储层需要哪些能力？](Q051-storage-ransomware.md)
- [Q052：Q052：不可变快照与离线副本各自解决什么问题？](Q052-snapshot-replication.md)
- [Q053：Q053：如何设计跨机房灾备而不盲目追求双活？](Q053-active-active-dr.md)
- [Q054：Q054：性能压测为什么常常无法代表生产负载？](Q054-stress-test.md)
- [Q055：Q055: 如何设计可复现的存储基准测试？](Q055-storage-benchmark.md)
- [Q056：Q056: P99 时延为什么比平均时延更值得关注？](Q056-p99-latency-latency.md)
- [Q057：Q057：缓存命中率与工作集如何指导性能扩容？](Q057-cache-scaling.md)
- [Q058：Q058：存储告警应优先关注哪些容量与性能信号？](Q058-storage-monitoring-capacity.md)
- [Q059：Q059：固件、驱动和多路径升级如何降低风险？](Q059-firmware-multipath-upgrade.md)
- [Q060：Q060：一次存储故障复盘应包含哪些证据？](Q060-storage-postmortem-failure.md)
- [Q061：Q061：分布式存储为什么能横向扩展？](Q061-storage-scale-out.md)
- [Q062：Q062：Ceph 的 RADOS、MON、OSD 与 CRUSH 各自做什么？](Q062-ceph-rados-crush.md)
- [Q063：Q063：Ceph 为什么可以同时提供块、文件和对象服务？](Q063-ceph-object-file.md)
- [Q064：Q064：分布式存储的副本数和纠删码如何选择？](Q064-storage-erasure-coding-replication.md)
- [Q065：Q065：都说带宽够，为什么故障恢复时还是卡？](Q065-bandwidth-failure-recovery.md)

### AI 推理与存储 · KV Cache 六讲（6 篇，正文见公众号）

- [第1讲 模型为什么不能直接给答案？一次推理请求的完整旅程](https://mp.weixin.qq.com/s/IUrhhro7XZYgFW6R-T7RBg)
- [第2讲 KV Cache 到底缓存了什么？](https://mp.weixin.qq.com/s/FvR--NyGDy0eMbFVmLFlaQ)
- [第3讲 KV Cache 装不下了，为什么显存和推理延迟同时告急？](https://mp.weixin.qq.com/s/iweY7rpUYspn1GGxjUVURg)
- [第4讲 KV Cache 不够用了，究竟有几类解决办法？](https://mp.weixin.qq.com/s/ZxsIfohvzl8w7VxxIaPDMw)
- [第5讲 KV Cache 能不能放到 SSD？答案不在 SSD 有多快](https://mp.weixin.qq.com/s/0FGCsdislK28xeRNQYtjhA)
- [第6讲 企业级推理架构，先做 PD 分离，再做存算分离](https://mp.weixin.qq.com/s/Swm9M_wLfoYLKK9FVFX75A)

## 仓库结构

- `content/100-questions/`：100 个企业存储问题的目录。
- `content/published/`：已经定稿、可长期引用的通用正文。
- `assets/content/`：正文配图与图解资产。
- `channels/github/`：GitHub 导航与内容映射说明。

## 内容原则

- 先给结论，再说明机制、取舍和适用边界。
- 用可观察的负载、时延、故障域和恢复目标支撑判断。
- 保持厂商中立，不把规格表或宣传页当作生产结论。
- GitHub 正文以 Markdown 维护，渠道适配不复制正文。
