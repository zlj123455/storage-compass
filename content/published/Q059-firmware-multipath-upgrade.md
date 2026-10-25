# Q059：固件、驱动和多路径升级如何降低风险？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/jzK5wSEh5L2woWlcU6dnuQ
> 发表时间：
> 迁移时间：2026-10-25

假设一次维护已经结束：升级任务显示成功，设备也重新在线。团队准备关闭工单，数据库却仍有提交超时。有人认为再等一会儿就好，另一个人建议马上装回旧版本。可这两个动作，都还没有回答业务究竟在等什么。

我会先把“组件升级完成”与“业务恢复”分开。降低风险的关键，不是把版本全部更新，而是确认兼容组合，控制每次变更影响的范围，并提前写清何时停止、怎样恢复。

升级可以修复已知缺陷、满足安全或支持要求，长期不升级也有代价。问题不是要不要变，而是这次要消除什么风险，以及切换期间能否守住业务的完成条件。

![图1：自拟假设场景中，组件升级完成与业务按时完成是不同验收对象，在线状态不能证明业务恢复。](https://mmbiz.qpic.cn/mmbiz_jpg/LF0nGncJCdVw0xdMwSoMNRRJiaOxqCVzCEVnDr7icXFCG3Se5s1ogrMSBARHm9FFibCuvvoLvSGU6h9Cree4B41D3xmVjdB4dtqwCE3tzXNqG8/640?wx_fmt=jpeg&from=appmsg)

## 要核对的，是一整组版本

一条存储路径可能同时依赖操作系统与内核、主机驱动、HBA 或网卡固件、多路径实现，以及存储端版本。每个组件单独“受支持”，不等于这一组组合受支持；全部选最新，也不等于相互兼容。

我会把当前组合、目标组合和每一步的中间状态一起核对。驱动先换、固件后换时，过渡组合是否受支持？是否必须经过中间版本？允许混版本多久？答案应来自对应产品的支持矩阵与升级流程，没有通用的先后顺序。

以 ONTAP 官方升级路径为例，能否直接升级取决于当前版本和硬件，有些路径需要中间版本。这说明目标版本正确，仍不足以证明走过去的过程安全。

固件还要核对实际激活状态。NVMe 工具文档区分下载、提交与激活，有的动作在下一次复位后生效。安装包已写入，不能直接当成新固件已运行；激活是否需要复位或重启，也要计入影响范围。

![图2：兼容性要核对当前、过渡和目标组合；五项为示例，不是通用升级顺序或完整清单。](https://mmbiz.qpic.cn/mmbiz_jpg/LF0nGncJCdVyzrTx4Hr00xgjEE6wBCMLmoBs0320EazZ7f4YqAxj4ePZ0MBs1xUPg2XoUexKPoZxUZlfm4eJZlErDjicJqtNWsC80lJnJZM4/640?wx_fmt=jpeg&from=appmsg)

## 路径有两条，风险未必分成两份

假设主机显示两条路径，却都经过同一块 HBA。如果更新会复位整块卡，两条路径就可能一起受影响。交换机和控制器也可能成为共同依赖。路径数量回答“看见几个入口”，不能代替故障域分析。

我更关心：本次变更会碰到哪些共同部件，剩下的路径能否承载维护期间的负载，切换等待会不会超过应用期限。这些要在批准的验证环境中带负载检验，并结合生产配置核对；备用路径能连通，不代表剩余带宽和控制器能力够用。

还有一种误判是“没有报 I/O 错误，所以没影响”。在 RHEL 9 的 DM Multipath 中，所有路径不可用且启用无路径排队时，请求可能一直等到路径恢复，应用却已经超时。暂时排队不是完成承诺。Linux 中用于 SCSI 的 DM Multipath 与原生 NVMe 多路径是不同实现，不能照搬超时和重试参数。

![图3：假设两条路径共用同一块 HBA；若本次操作复位整卡，两条路径可能同时受影响，须核对实际复位范围。](https://mmbiz.qpic.cn/sz_mmbiz_jpg/LF0nGncJCdWic9xuslmb5ALo0hZMKa0PgKticgyxmFLB4sibzJw77ZhaZ0FiaP9LcoRlFW8JeSLkoaEwJKvpadAJMGW2JDbTXw0ACjAianebM2LI/640?wx_fmt=jpeg&from=appmsg)

## 分批升级，要等状态恢复再继续

缩小批次可以减少一次受影响的业务，也会拉长实施与观察时间。“每次只升级一个节点”不是所有产品的通用规则。变更单元与顺序必须按产品支持的流程来定；冗余不足或不支持在线升级时，应先迁移业务，或安排明确的停机窗口。

一次切换结束，我会确认替代路径真的在承载请求、离线部件已恢复、冗余重新成立，再看对应业务的错误、超时与长等待。前一批没恢复就推进下一批，可能把临时降级变成全路径不可用。

“无中断升级”也不是零等待承诺。ONTAP 官方文档明确提到接管与交回期间的 I/O 暂停；业务是否能容忍，仍要结合应用期限验证。固定等几分钟不是万能验收，观察窗口要覆盖实际恢复与代表性负载。

![图4：按产品支持的变更单元分批，恢复验收通过才推进下一批；路径、冗余与业务标准须在变更前约定。](https://mmbiz.qpic.cn/sz_mmbiz_jpg/LF0nGncJCdWgAM9hVxzzLV6DXHkGxW3vME8wmStEeekLXabVY8FuVh8GgHhN24og0KmlwPuWBhyicpUibc1nt9aN0TcibD7iaklEbN9YjS9lDRQ/640?wx_fmt=jpeg&from=appmsg)

## 旧安装包，不是一份恢复方案

回退至少有四件不同的事：恢复配置、退回软件、降低固件版本，以及恢复数据。它们的前提与代价不同，不能用“已经备份”一笔带过。备份不会自动撤销驱动变更，也不保证数据能被旧软件读取。

升级前要确认可回退的版本范围、新特性或格式变化是否阻断降级、需要哪些恢复介质，以及恢复能否在窗口内完成。ONTAP 的 revert 有版本相关的前置检查，而且属于中断性流程，并不是简单启动旧镜像；其他产品应核对各自规则，不能默认升级在线、回退也在线。

方案还要写清止步条件和责任人。比如出现数据错误、冗余没有恢复，或业务持续超出约定的完成期限，就停止后续批次，由主机、存储与应用负责人核对证据，按批准预案恢复，而不是临场反复刷版本。

![图5：配置恢复、软件回退、固件降级和数据恢复的对象与前提不同，四项不能相互替代，也不保证全部可行。](https://mmbiz.qpic.cn/sz_mmbiz_jpg/LF0nGncJCdViaqR9LibYU4OHZ069icqn0JicTZqKqXgYyicwe2cjPTq1UCOOPiaqAmAGhEqzr6ibIVWV2Qiaxnl5tGDJdUtH4oTchjz0aLPUuaP4rNc/640?wx_fmt=jpeg&from=appmsg)

## 工单关闭，要拿业务结果说话

回到开头，设备在线之后，先沿同一时间线对齐应用超时、主机等待和路径事件，确认异常从哪一层出现。时间重合只是线索，不能直接认定新固件有问题，更不该盲目追加变更。

升级前后的比较，还要保留相近的请求类型与负载，分别看超时、错误和长等待；不能只用成功请求的平均耗时证明恢复。当前运行版本、实际可用路径、业务完成与冗余状态，都应留下记录。

升级的终点，不是版本号变了，而是要修复的问题得到验证，业务在约定条件下恢复，系统回到约定的冗余状态。不能让临时降级留到下一次故障。每一步都能证明这一点，变更才是在降低风险。升级顺序、过渡版本、激活条件和恢复方式，必须先满足实际部署的支持规则。

![图6：按约定的请求类型与负载，核对运行版本、路径承载、业务结果和冗余状态；图中为验收框架，不是实测结论。](https://mmbiz.qpic.cn/mmbiz_jpg/LF0nGncJCdWKguchhR7Iu0I70B93qT8W99VKUA6jII40YgbNSg9lk8x7wibiaCcGO4q7ZibTDvx5CskaEl7vicvAdwLtEyFn2HibUoNSbMF3ianCc/640?wx_fmt=jpeg&from=appmsg)

升级最怕的不是失败，是以为成功了。

有具体场景，随时找我聊；想进同行群，回「进群」就行。

![联系方式](https://mmbiz.qpic.cn/sz_mmbiz_jpg/LF0nGncJCdWvM9sATIqhzUHf7iaHAkEuvRCKYCgIMjkLegER4afNfs2vlTibA6rq0B0K6kia26wfYTxGAkpCub7JADAZjvLMmceA8qqzhdE0hY/640?wx_fmt=jpeg&from=appmsg)
