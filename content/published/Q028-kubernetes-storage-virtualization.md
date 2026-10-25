# Q028：Kubernetes、数据库和虚拟化分别常用哪些存储接口？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/RDalv2zvhH9BsemTbCxt4g
> 发表时间：
> 迁移时间：2026-10-25

# 三个团队，都要同一套“高性能存储”

假设一次新平台建设会上，数据库团队要“低时延、高可靠”的存储，虚拟化团队要“共享、可迁移”的存储，Kubernetes 团队要“自动创建、自动挂载、能扩容”的存储。三张需求单最后都写成了同一句：100 TB，高性能，高可靠。

架构师没有立刻选 FC、NFS 或 CSI。他先把这三张单子放在一起问：三类业务的一次写入，最后分别要等到哪里？谁来决定卷该建在哪？谁来防止多个写者把同一份数据写乱？

数据库、虚拟化和 Kubernetes 并不各自绑定一种协议。接口选择的起点不是平台名称，而是一次 I/O 的路径、共享的对象和完成确认的责任。

顺着这三次写入走一遍，就能看清为什么“同一套存储”不等于“同一种接法”。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdWghay78gIJ8DX7v7psD3VpOXleyNp1KdJq9iahCFicVpkR3fCDTEdZ8R4gY865lm2FphHJyic0VBDRhxvib154unnveHiaMJDEvibb8/640?wx_fmt=png&from=appmsg)

# 第一条路径：数据库提交，等的不是“存储已连接”

数据库团队最先演示的是一笔事务提交。应用发出提交后，数据库先处理日志，再通过文件系统或数据库设备把写入交给块设备；随后才是主机协议栈、存储网络、控制器、数据保护与介质服务。业务最终等待的，是数据库认可的持久化完成条件。

  * 

[code]
    事务提交 → 日志写入 → 文件系统或数据库设备 → 块设备 → FC / iSCSI / NVMe-TCP → 存储系统 → 持久化确认
[/code]

  

这就是为什么生产数据库常见的底层入口是块设备。数据库希望自己控制数据文件、日志、缓存与恢复过程；FC、iSCSI、NVMe/TCP 只是把块设备交给主机的不同方式，并不是“数据库专属协议”。

以 PostgreSQL 为例，WAL 的写入与同步会分别被统计；官方文档区分 WAL 写入时间与fsync同步时间，说明事务关心的不只是数据进入主机缓存，而是日志何时完成要求的同步。

这条路径也划出一条边界：备份文件、归档日志、离线导出文件可以放进文件或对象存储；但不能因为它们能放，就把活跃数据目录默认迁到任意共享目录。多节点能否共同访问同一数据目录，必须由数据库和高可用方案明确支持。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdXrtCSdvjOKp03QWIjAInTrOBQrLgVuOl3yIF5nIwGtqQVcNbvC9rFA91Uaa88wGV9FdpmWHoRWUkicIE7VaadcltH9EFEeASWg/640?wx_fmt=png&from=appmsg)

# 第二条路径：虚拟机写入，虚拟化平台在中间多做了一层事

虚拟机内的操作系统看到的是一块虚拟磁盘，可这块盘对虚拟化平台而言，通常是数据存储中的虚拟磁盘文件。一次写入先从虚拟机进入宿主机，再由虚拟化平台定位数据存储，最后才抵达块或文件接口。

  * 

[code]
    虚拟机应用 → 虚拟磁盘 → 宿主机 I/O 栈 → 数据存储 → 块路径或 NFS / SMB → 存储系统
[/code]

  

这里的关键不是“虚拟机里有没有一块 C 盘”，而是多台宿主机能否安全地访问同一份虚拟机数据。虚拟化平台还要处理虚拟磁盘锁、数据存储元数据、主机故障、迁移与接管。

一种常见实现是：存储向宿主机提供块设备，虚拟化平台在其上建立集群数据存储，再把虚拟磁盘文件放进去。vSphere 的 VMFS 文档说明，VMFS 的磁盘锁支持多个主机并发共享虚拟机磁盘文件。

另一种实现是：存储直接向宿主机提供 NFS 或 SMB 共享目录，虚拟硬盘、配置和快照直接以文件形式存放。Hyper-V 文档明确说明，虚拟机配置、虚拟硬盘和快照可以存放在 SMB 文件共享上。

所以虚拟化不是简单地“应当用块存储”。它需要的是一个被平台支持的数据存储，以及能承受共享访问和故障切换的协调机制。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdVs7ol4c4ZYn2KwXMt3RXflRIJJ3TKNXra1j2MBJAPlqQZEyQgjV1xojL6edTwiak4yDzTLic1Prrt9TfT3uvFe5oMiaKwJlWL3SU/640?wx_fmt=png&from=appmsg)

# 第三条路径：Pod 写数据前，先发生了一段看不见的准备工作

Kubernetes 团队的画面看起来不同。应用并不会直接发现一块新盘；它先声明一个 PVC，说明容量、存储等级和访问模式。之后 Kubernetes 调度器与 CSI 驱动决定卷能否创建、应该落在哪个拓扑域、能否连接到目标节点，最后 kubelet 才把卷发布给 Pod。

  * 

[code]
    Pod 声明 PVC → StorageClass → CSI 创建卷 → 连接或挂载到节点 → kubelet 发布给 Pod → 应用 I/O
[/code]

  

这是一条控制路径。CSI，即容器存储接口，负责让 Kubernetes 调用存储驱动创建、发布、挂载和回收卷。CSI 规范中可以看到控制端的CreateVolume、ControllerPublishVolume，以及节点端的NodeStageVolume、NodePublishVolume等操作。

但 Pod 真正开始读写后，数据路径依然要回到块或文件语义：可能是 FC、iSCSI、NVMe/TCP，也可能是 NFS。Kubernetes 官方文档对 CSI 的定位也是让容器编排系统接入任意存储系统，而不是定义一种新的 I/O 协议。

这解释了常见误会：“支持 CSI”只说明卷生命周期可以被 Kubernetes 管理，并不等于这个卷天然适合数据库，也不等于它已经解决了多写者一致性。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdUBqicRz6hhrU1OSxfKyC0FHdUkyyTruRdhPS2Nm4X7EDL1Qcb9iadU8kIY3q0uJVflhTU0gUTM7h0c1MtXt8gT2HibuCY6CIUAX4/640?wx_fmt=png&from=appmsg)

# 三条路径在“共享”这里分开了

走到这里，三张需求单里的“共享存储”已经不是同一句话。

业务| 共享的对象| 主要协调者| 先确认什么  
---|---|---|---  
数据库| 数据副本与写入权| 数据库与高可用组件| 谁可写、日志何时持久化、故障后谁接管  
虚拟化| 多主机可访问的数据存储| 虚拟化平台| 虚拟磁盘锁、主机隔离、迁移与接管  
Kubernetes| PVC 生命周期或共享文件目录| Kubernetes、CSI 驱动和应用| 节点拓扑、访问模式、挂载与应用恢复  
  
Kubernetes 的 RWO、RWX 等访问模式尤其容易被过度理解。它们首先是 PVC 与 PV 的能力匹配，通常并不自动替应用提供文件锁、事务一致性或多写者协调。Kubernetes 官方文档也提醒：多数访问模式在卷挂载后并不强制写保护；只有 ReadWriteOncePod 等特定模式才有更严格的单 Pod 约束。

因此，容器里的数据库仍需要明确单写者与故障接管策略；多个 Pod 共同处理素材或报表时，才可能需要共享文件语义；对象数据则通常由应用经 S3 API 或 SDK 访问，不必强行伪装成普通持久卷。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdUqwRRcMWVNedaPic6zHF6WvibDwoibW7yibwudCEvTb1xoAyibib8QsObBwMDqFporNyMXGxPDAOctoUoHVgDwBJH5TDUIiaGk1fXOIk/640?wx_fmt=png&from=appmsg)

# 接错接口时，问题会出现在不同的位置

数据库若把“能挂载”误当成“已持久化”，同步提交的尾时延与断电语义就可能失去验证。虚拟化若只确认所有主机都能看见数据存储，却没有确认隔离和锁的边界，路径分裂时风险不在容量，而在谁还能继续写。Kubernetes 若只验证 PVC 创建成功，却没有核对拓扑、访问模式和应用恢复，Pod 可能在故障后挂不上卷，或者多个实例同时碰到不该共享的数据。

这不是某个协议“高级”或“落后”的问题。块接口解决块访问，NFS 或 SMB 解决文件访问，CSI 解决编排系统和存储驱动的衔接。它们都不能替代数据库复制、虚拟化仲裁、应用副本、备份和灾难恢复。

# 回到最初那三张需求单

架构师最终没有让三支团队各自写一个协议名，而是要求每张单补齐六项信息：

  1. 应用需要块地址、共享目录，还是对象 API？

  2. 谁管理文件系统、数据布局和缓存？

  3. 是否需要多个主机或多个 Pod 同时读写？

  4. 一次写入要等到受保护缓存、介质，还是副本确认？

  5. 节点、路径或站点故障后，谁决定继续写和恢复？

  6. 自动创建、扩容、快照、备份和恢复分别由哪一层负责？

这六个问题回答清楚后，接口通常就不难选：数据库从持久化路径出发，虚拟化从数据存储与集群协调出发，Kubernetes 从控制路径和实际数据路径同时出发。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdXiaWycWCK2Rx0BYWCdshgcD3enrpYc9qT8Gr9p63nDjudpkusf0Ld6EaYyNYemS6klSZuHUgOUOXUy81eHXq9KEQ0ehDHsdnsQ/640?wx_fmt=png&from=appmsg)

真正应该被写在需求单最上面的，不是“我要 FC”或“我要 CSI”，而是：这项业务的一次 I/O 怎么走，谁对它的完成和恢复负责。
