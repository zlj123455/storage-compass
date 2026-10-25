# Q063：Ceph 为什么可以同时提供块、文件和对象服务？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/Ge_gG4G2c5KLab_i91dG4g
> 发表时间：
> 迁移时间：2026-10-25

假设虚拟化团队要一块磁盘，工程团队要共享目录，备份团队要 S3 接口。方案说三者都能用 Ceph。问题随之而来：底层既然叫分布式对象存储，磁盘地址和文件路径是从哪里来的？

**Ceph 在 RADOS 底座之上放了不同的服务接口：RBD 提供块设备，CephFS 提供文件系统，RGW 提供对象 API。三条路径共用底层能力，但各自定义自己的访问方式、元数据和管理边界。**

![图1：虚拟磁盘、共享目录和 S3 请求从三个入口进入同一 RADOS 底座。](https://mmbiz.qpic.cn/mmbiz_jpg/LF0nGncJCdWMMPMcGdA5uw3EZ6kUbr81y8u4ZT3Wa7nkULtKkicRibH790DAa3DejiaIYlCR5QKMOcR1ibGD76P53ib6Z4iaakuhgxZCibYa2eI0Pc/640?wx_fmt=jpeg&from=appmsg)

##  一块虚拟磁盘，底层不是一个大文件

虚拟机看到的是连续的块地址。RBD 把镜像的内容组织成多个 RADOS 对象，客户端通过内核模块或 librbd 等方式访问块设备。业务发来“读这个地址、写那段数据”，RBD 负责把它对应到镜像中的对象，再由 RADOS 完成底层读写与保护。

所以，RADOS 对象是实现材料，不是用户直接拿到的 S3 对象。虚拟机里的文件系统也在块设备之上；Ceph 不会因为知道 RBD 对象的位置，就自动理解数据库表或文件名。

这条路径给虚拟化团队的验收重点是块读写的时延、客户端接入方式以及主机故障后的恢复。即使镜像底层分散在多个 OSD 上，单个虚拟机的写入方式和宿主机路径也会限制它能利用的并行度。

![图2：RBD 将块地址映射到镜像对象，虚拟机文件名不直接成为 RADOS 对象名。](https://mmbiz.qpic.cn/mmbiz_jpg/LF0nGncJCdVGLXFjxQChdicenC56eBvo3K7UlLphv2hMGYDxLjPq3ibbY5My3Dso6aSDJhsj9pbERTyQ1cZibpjvLwu7iaKbR1KV6GXa1CbVOVM/640?wx_fmt=jpeg&from=appmsg)

## 一个文件路径，还需要目录这层秩序

工程团队打开 `/project/report`，不仅要取数据，还要解析路径、处理目录、权限与文件元数据。CephFS 的 MDS 负责这类元数据交互和客户端能力管理；获得所需能力后，客户端可直接访问 RADOS 读写文件数据。不能把 MDS 画成每个文件数据块都必须经过的网关。

这也解释了文件工作负载为什么会出现与块设备不同的瓶颈。大量创建、列目录或重命名可能先考验元数据路径；大文件连续读写更可能压到客户端、网络与 OSD。共享同一 RADOS 底座，不会抹平这些差别。

不能因为文件数据可直达 RADOS，就认为 MDS 可有可无。没有正确的目录、权限和客户端能力状态，应用看到的就不是一个可用的共享文件系统。上线验收应把元数据操作与文件数据吞吐分别测，而不是只跑一次大文件顺序读写。

![图3：CephFS 的元数据交互到 MDS，文件数据可由客户端访问 RADOS。](https://mmbiz.qpic.cn/sz_mmbiz_jpg/LF0nGncJCdUHYommHuib8OAd37FxcsGxe71Fnpic2F9Fr6A4CA7Z6dH2aW3Ot5gicetHceoJztHkgmicrhV9fMNkksWRWKosiaqEyaIG6127Ria4A/640?wx_fmt=jpeg&from=appmsg)

## 一个 S3 请求，先经过对象网关

备份程序发出带桶名和对象键的 HTTP 请求。RGW 处理 S3 兼容接口、身份与桶相关逻辑，再把元数据、桶索引和数据组织在 RADOS 上。RGW 不依赖 CephFS 的 MDS 去解释 S3 的键；RADOS 内部对象也不因此与一个 S3 对象始终一一对应。

“兼容 S3”还要看应用实际使用了哪些 API、认证及生命周期功能，不能把接口名称当成所有行为一致的保证。若为旧系统接 NFS 或 SMB，通常还要设计相应网关或服务层，不能说 CephFS 自身就是这些协议。

网关本身也需要容量与高可用设计。RGW 到 RADOS 的路径虽然共用底座，但 HTTP 连接、认证和桶索引都会影响对象请求。只测 OSD 吞吐，无法证明备份程序按预期完成列举、上传、读取和失败重试。

![图4：S3 请求经 RGW 处理接口和桶语义，再落到 RADOS 的元数据、索引与数据。](https://mmbiz.qpic.cn/mmbiz_jpg/LF0nGncJCdVrNHIicWKmZGLibHlXvoGZuPFFQsS71wiaRuj4OY7HYXgCFGhCFZXELGDfehJjJmWObmHZgyE4Bd7cHqRQy0IDtx2hOefOg1QHtA/640?wx_fmt=jpeg&from=appmsg)

## 同一个集群，不等于同一份数据

三种服务可以共用 OSD、网络和集群管理，但名称空间、权限、元数据组织各不相同。默认情况下，不能把一块 RBD 镜像拿去用 S3 键读取，也不能把 CephFS 文件路径直接当作 RGW 对象键。若需要跨接口共享内容，应设计明确的复制、同步或应用转换流程，并验证一致性。

  

  
  
  
---  
  
  
---  
  
  
  
---  
业务动作| 接口层| 关键依赖| 上线前再核对  
---|---|---|---  
读写虚拟磁盘地址| RBD| 镜像对象、RADOS、客户端| 随机写时延与宿主机接入方式  
打开共享文件路径| CephFS| MDS 元数据、文件数据池| 目录操作与客户端能力边界  
PUT/GET 备份对象| RGW| HTTP 网关、桶索引与数据池| 实际 S3 API、身份与网关容量  
  
  

![图5：三条路径的接口与元数据各自独立，不能把同一底座等同于数据互通。](https://mmbiz.qpic.cn/sz_mmbiz_jpg/LF0nGncJCdXpTBxMQkq5F5RLDZ1Dmul4s5COtczDL62l0rqBpTHbNic3f3UTGYbfHtc9OGHwQ6Nd0zuWO3kbepjp94hOuLMRVD39Ns1I1BxQ/640?wx_fmt=jpeg&from=appmsg)

共用底座也意味着共用风险。某个池单独命名，并不自动获得物理隔离；OSD、网络、容量或集群状态异常仍可能影响多个服务。设计时要问的不只是“能否同时开三个接口”，还包括故障域、容量余量、性能竞争和责任边界如何分开验证。

实际交付时，可以给三个团队各留一条端到端测试：虚拟机确认磁盘写入与恢复，共享目录确认创建和权限，对象应用确认所需 S3 操作。再安排共同负载测试，看三类请求同时进入集群时谁先排队。这样才能看见共用底座带来的效率，也看见它的共享限制。

**Ceph 的“多接口”是一套底座承载三种服务契约。读者真正要选的，是业务需要哪种契约，以及愿意承担哪条额外路径的成本。** 具体客户端、网关、隔离方式与 S3 功能仍需在目标版本和部署中核实。

![图6：按业务动作选择接口，并验证共享底座上的资源竞争与故障影响。](https://mmbiz.qpic.cn/mmbiz_jpg/LF0nGncJCdUj74e68wVZkEsCD8KgBlAbicPkO6eJDfs6BiagAvfDaIaYaHXYYMTJvYkjyQqMibq14Fjq5EV4dfEXibwX2hibV09icib8oY6fEWuGcA/640?wx_fmt=jpeg&from=appmsg)

一套集群跑三种接口，省的是钱，难的是隔离。

有具体场景，随时找我聊；想进同行群，回「进群」就行。

![联系方式](https://mmbiz.qpic.cn/sz_mmbiz_jpg/LF0nGncJCdUvm9ISZVaP2SIw31ib0HDUCNpM3ct5xpIc59eiaMbKzITX45icWgG1VKMSCiajt9YGj0eJXvQpMx8VcIW3b1M09PjFJ2Yox5hRoxA/640?wx_fmt=jpeg&from=appmsg)
