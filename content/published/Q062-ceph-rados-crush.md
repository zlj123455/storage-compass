# Q062：Ceph 的 RADOS、MON、OSD 与 CRUSH 各自做什么？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/HKDPKcgpBH2kqnjsrJmI9Q
> 发表时间：
> 迁移时间：2026-10-25

第一次看 Ceph 架构图，很容易把 RADOS、MON、OSD、CRUSH 排成一列，想象业务写入依次穿过四台服务器。沿一笔已经进入 RADOS 层的对象写入看，会发现这张图从一开始就画错了。

**RADOS 是底层分布式对象存储系统；MON 维护集群状态，CRUSH 参与计算数据应放哪里，OSD 承担实际对象读写与副本协作。它们是系统、服务角色与算法的不同层次。**

![图1：RADOS、MON、OSD、CRUSH 是不同层次，不是四个串联的数据中转站。](https://mmbiz.qpic.cn/mmbiz_jpg/LF0nGncJCdWlEEdf5Piao4DOoEtyHZCv6S88C89qhV6daib3YgOAru5aId6qOBMJZBZbU1BZwosmDPrtiaPqbj3puTrokficgLibHFdppuftICVY/640?wx_fmt=jpeg&from=appmsg)

##  写入前，客户端先需要一张地图

假设客户端要写池里的一个对象。它先要知道集群有哪些 OSD、池采用什么放置规则、当前 map 处于哪个版本。MON 维护集群 map，客户端从 MON 获得必要的状态信息。MON 的关键职责是让参与者对集群状态有共同认识，并非替每笔对象写入搬运数据。

这就是图中要分开的两类箭头：到 MON 的是状态信息流；真正的对象数据要发往承担该对象的 OSD。若把两种箭头画成同一条，就会误以为 MON 的网口决定了全部业务吞吐。

客户端通常会保存已取得的 map，并在集群状态变化时更新。因此，“先问 MON 要信息”是在说明建立和更新集群视图，不是说每次读写都先做一趟 MON 往返。排障时应查客户端看到的 map 版本和请求实际到达的位置，而不是只查 MON 进程是否在线。

![图2：客户端从 MON 获取集群状态，业务对象数据走向 OSD；两类箭头含义不同。](https://mmbiz.qpic.cn/mmbiz_jpg/LF0nGncJCdVLRwqE4ZfvV9uIFmfHp0pvTMJEmDnNJsnpel9srYtnibzvCh8GSagiaL6ibHCtlSwd1l79uV2AhGZh7HggdIR2p6AqGMGTy7AIVo/640?wx_fmt=jpeg&from=appmsg)

## 对象怎样找到一组 OSD

对象放在某个池里。Ceph 先把对象归入一个放置组，简称 PG；PG 是把很多对象作为一组管理和放置的中间层，不是另一台机器。客户端再结合 map、池的规则与 CRUSH 计算期望放置位置。

CRUSH 是放置算法，使用集群拓扑、权重和规则计算目标。它既不保存对象，也不单独保证故障时所有请求必定发向静态示意图的节点。实际服务还要看当前 PG 的状态和 acting set，也就是该 PG 在当前状态下承担请求的一组 OSD。图中“对象→池/PG→OSD”只保留了读路径所需的骨架。

PG 这层间接关系还有运维意义：新增或移除 OSD 后，集群可以调整 PG 的放置并迁移相关数据，而不是让每个应用自己保存一份对象到物理盘的地址表。PG 数量与数据分布也会影响管理成本，不过这属于容量和调优问题，读懂本次请求不需要先背一套 PG 数量公式。

![图3：对象进入池和 PG 后依据规则定位；故障时实际服务集合需看当前状态。](https://mmbiz.qpic.cn/mmbiz_jpg/LF0nGncJCdVv9oxs8qkPmrJiaBTWFmQKAQPsSGmz3MpPiaprtOHtfJgc4fOicuibBkC5j2shHMdQjDVemqxGuVibfSIRyfgRODVib0onFVSib3M1qc/640?wx_fmt=jpeg&from=appmsg)

## 数据到达 OSD 之后

在健康的副本池里，客户端写请求会到该 PG 的主 OSD；主 OSD 与其他承担该 PG 的 OSD 协作完成副本写入，再按配置和当前状态向客户端确认。OSD 是运行中的守护进程及其管理的存储资源，不能简单等同于一整台物理服务器：一台主机可以有多个 OSD。

如果有人问“副本写到几份就能回成功”，不能只回答“size 是三”。还要看池的 min_size、当前 PG 状态、目标版本和实际故障情况。本文只解释健康副本池的主路径，不用一幅简图推断降级服务语义。

读请求同样先要找到当前可服务的 PG。某些配置与版本可能改变读的来源，因此图上的主 OSD 是健康副本池的基础理解，不能据此断言任何读操作永远只从主 OSD 返回。遇到重试、重定向或 peering 时，更要以现场状态为准。

![图4：健康副本池的写入先到主 OSD，再由相关 OSD 协作完成保护动作。](https://mmbiz.qpic.cn/mmbiz_jpg/LF0nGncJCdVb4yMz6FTxBH2LYFnDtNv3R9jkDEqf2Czpb4BxtcicticPEgYniciawk0I2kAuPiayoDyFVib9OphQhW14yPhOX6VlUd1opEhpNWvmw/640?wx_fmt=jpeg&from=appmsg)

## 四个名字放回同一张职责表

  

  
  
  
---  
  
  
---  
  
  
  
---  
名称| 在这笔请求中做什么| 容易误解成什么  
---|---|---  
RADOS| 提供底层分布式对象存储能力| 一个独立转发数据的进程  
MON| 维护并提供集群 map 等状态| 每笔业务数据的中转站  
CRUSH| 按拓扑和规则计算期望放置| 保存对象的节点  
OSD| 处理对象读写、保护和本地存储| 一台物理服务器的同义词  
  
  

MGR 主要承担监控与管理相关功能，也不是这笔对象数据必须经过的转发站。MDS 和对象网关属于上层接口问题，下一篇再接上。

![图5：职责对照让四个名称回到系统、状态、算法与数据服务的位置。](https://mmbiz.qpic.cn/sz_mmbiz_jpg/LF0nGncJCdUruS2EOsKVPZr1NicguqezicgYH1kKXSQ7Gic9hslctwsDqC3wRr9XLQg9fwhbo4wBPVdAqD8pkGwKkG5tjCYbqVy5ibjFIOzhicYo/640?wx_fmt=jpeg&from=appmsg)

实际排障时，这张路径图也能指导提问：客户端拿到的 map 是否新鲜？对象属于哪个池和 PG？当前主 OSD 与 acting set 是谁？请求是在定位前、到达主 OSD 后，还是副本协作时等待？

**理解 Ceph 的第一步，是分清“谁告诉我集群现在怎样”和“谁实际替我读写数据”。** 这条区分，比背下四个缩写更能帮助你看懂下一张监控图。这里采用健康副本池的简化路径，故障、读优化和写确认条件仍要按目标 Ceph 版本与集群状态核对。

![图6：沿客户端、map、PG 与主 OSD 定位等待位置，避免只按进程名猜故障。](https://mmbiz.qpic.cn/sz_mmbiz_jpg/LF0nGncJCdUDXobpHHw2CoqyZvjy3ujXUwMibcObG7YNfibTVTwZMsJG08eKqqNRYTVdgPu6YbMiaxheCXM9Vtx9wB8vVnbCUdTJBnoy0x35lc/640?wx_fmt=jpeg&from=appmsg)

Ceph 架构图，第一眼几乎人人都会看错。

有具体场景，随时找我聊；想进同行群，回「进群」就行。

![联系方式](https://mmbiz.qpic.cn/sz_mmbiz_jpg/LF0nGncJCdWtcXoRFOA69OnibUutrkI1EejVXtibicUhWWInNqRgAqGAZyicIUDpSfNmjuWdtribibUN4EroPu8OWm3x6fibaGrcTias8EeMDuibEDwU/640?wx_fmt=jpeg&from=appmsg)
