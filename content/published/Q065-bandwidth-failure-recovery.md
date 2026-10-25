# Q065：都说带宽够，为什么故障恢复时还是卡？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/MxxyckAN3lTNTt_EvSo3LQ
> 发表时间：
> 迁移时间：2026-10-25

假设一个集群刚加完节点，容量余量看起来很宽裕。业务平时运行正常，一台节点故障后，数据恢复开始，数据库提交时延却明显抬高。会上有人指着网卡规格说“带宽够”。问题是，那张规格表没有回答：故障时究竟有哪些流量经过同一条链路？

**分布式存储的网络设计，必须把前台请求、数据保护和故障恢复同时画出来，再核对链路、交换设备和节点的共同瓶颈。网口的标称速率只是起点，不能替代故障态业务验收。**

![图1：正常时链路有余量，不代表故障恢复时前台业务仍能达标。](https://mmbiz.qpic.cn/mmbiz_jpg/LF0nGncJCdWxibC1OcBM0VwibBXMqXwiaDtib0pUglbu8juZNg1IJepmwoLKyecVqdYDJdUias7wzuR9mDEp3xtLnLw8bYwZJicL2Bnrpn5ybWlqY/640?wx_fmt=jpeg&from=appmsg)

##  一次写入，可能不止一段网络旅程

沿用前几篇的 Ceph 副本池例子：客户端拿到所需的集群信息后，将请求送往相应 OSD；主 OSD 还要协调副本写入。图中可以把“客户端到 OSD”与“OSD 之间”画成两种箭头，它们并非同一个可随意相加的业务带宽数字。纠删码池的具体传输和确认路径又有差异，不能把副本示意当成所有写入的固定倍数。

网络对请求的影响也不只发生在吞吐打满时。链路成员利用不均、短时拥塞、丢包重传或路径切换，都可能让少数请求等得更久。先把业务端的尾时延与实际流量放在同一时间轴，再去判断是不是网络限制；看到交换机某端口很忙，还不能直接宣布它就是根因。

![图2：示意一次副本写入中的客户端路径和节点间保护路径；具体路径随产品与池配置变化。](https://mmbiz.qpic.cn/sz_mmbiz_jpg/LF0nGncJCdW5Ezkp6xpJ4PgcOdNZS9vAZo84jx3uVCeVhwDSu51wCCLCmPCVZgGNEiaOUMvyVETZVhmaVduVefPfXLW1kefDIn8hmZLZJLVI/640?wx_fmt=jpeg&from=appmsg)

## 节点故障后，恢复也要走网络

Q064 的保护方案留出了数据副本或校验片，却没有凭空恢复保护级别。故障后，幸存节点需要读取现有数据，再把恢复数据送往新的位置。前台业务此时仍在读写，同一组 OSD、上联、交换机和恢复目标可能同时承担两种任务。若恢复目标空间不足，网络再快也无法结束这段风险窗口。

因此要分开记录两类结果：业务在故障、恢复期间是否守住时延和错误率边界；保护何时恢复到预定状态。只把恢复限速压低，业务或许平稳，但保护不足的时间可能变长；只追求恢复速度，也可能挤占前台。这个取舍要由业务目标决定，不能靠一个默认参数代替。

![图3：前台请求和恢复流量可能共享网络及 OSD，恢复进度与业务体验都要观察。](https://mmbiz.qpic.cn/mmbiz_jpg/LF0nGncJCdUxLSytK6eI2t7BicZ7BPVwMxswmibCSnnQerCBtoGAw5PnpDMWxnRslt4TZuSCcBKoibZDodh7BXUhXn02QlascC0l2kiajbMicQs8/640?wx_fmt=jpeg&from=appmsg)

## 带宽、分布和冗余是三道不同的题

买了两条高速链路，不等于一笔业务请求能得到两条链路速率之和。流量怎样分布到成员链路，取决于拓扑、转发和哈希等实际配置；某条链路故障后，还要确认另一条是否有足够能力承接关键流量。链路本身双份，如果最终仍汇聚到同一台交换设备或同一处电源，也没有跨过目标故障域。

Ceph 可以只使用 public network，也允许另设 cluster network 承载 OSD 间心跳、复制和恢复。分开网络可能改善特定负载下的争用，也增加端口、布线、路由、安全与排障工作。评审不能把“双网”直接画成高性能勾选项；应先看实际瓶颈、冗余和运维能力。

![图4：网络容量、流量分布和故障后替代路径，需要分别验证。](https://mmbiz.qpic.cn/sz_mmbiz_jpg/LF0nGncJCdU9eWaFN0NwCZia1GJAT0zH1ffyGj3VibhnT31ibibujgxmoU4rTlVibRxQ6oQQuSnjX5lmSBkcxvAaXepDn3SucWicibgO29r903ibWVM/640?wx_fmt=jpeg&from=appmsg)![图5：单网与分网均有适用条件，关键是目标流量和故障态如何验收。](https://mmbiz.qpic.cn/sz_mmbiz_jpg/LF0nGncJCdUqKX2zEG1LR6SwfkFPOKOkwQFrkCaliclibVeCxVemiaRuAC7eGyIsNqT8gGFyFTbEEkaYyJUQEvA2v7LLfNTtdUAUgzlVr9HAcQ/640?wx_fmt=jpeg&from=appmsg)

## 把三种状态填进同一张表

下面是供方案评审使用的假设记录，不是某个集群的测试结果。业务目标与链路阈值需要由实际环境填写。

  

  
  
  
---  
  
  
  
---  
  
  
---  
  
  
  
---  
  
  
---  
  
  
  
---  
  
  
---  
  
  
  
---  
  
  
---  
  
  
  
---  
  
  
---  
  
  
  
---  
  
  
---  
  
  
  
---  
  
  
---  
  
  
  
---  
状态| 同时存在的主要流量| 先核对的共同资源| 应留下的证据  
---|---|---|---  
正常| 前台读写、保护写入| 客户端路径、节点间链路及交换设备| 业务端尾时延、错误、链路成员利用  
节点故障| 前台读写、剩余保护路径| 失效路径后的路由与余量| 业务结果、路径切换、保护状态  
恢复进行中| 前台读写、恢复/回填| OSD、恢复目标空间、节点间与上联| 业务尾时延、恢复进度、拥塞或重传  
  
  

真正要问的是：目标故障域失去后，哪些链路仍承担业务，恢复再加入时哪里先成为瓶颈，如何证明两项目标都达成。测试应先写停止条件和回退安排，不为做一张漂亮的拓扑图在生产环境随意触发故障。**网络设计的交付物，是可核对的流量与故障态服务边界。** 网络带宽和是否分网没有通用答案，必须结合目标拓扑、链路故障行为与恢复流量验证。

![图6：用正常、故障与恢复三种状态核对流量、共同资源和业务证据。](https://mmbiz.qpic.cn/sz_mmbiz_jpg/LF0nGncJCdV8HxEmg4KTibDtSkwWSSTT5umMOWJ8JDwnNEpXqtg3sEUynfdeF6aML19yicaCbTexPxdmFHBIyt62raUficpXCJRrtFPGfH8EH4/640?wx_fmt=jpeg&from=appmsg)

带宽够不够，要看故障时谁和谁挤在同一条链路上。

有具体选型场景拿不准？回「**进群** 」进『存储 100 问』同行群 —— 群里有选型答疑，也欢迎你带着真实场景来聊，我 1v1 帮你拆。

![联系方式](https://mmbiz.qpic.cn/mmbiz_jpg/LF0nGncJCdVAMogevLaj8S6vo6Xl6BtdHK3U9Tjia7jZw62zXkwECniat5ykE1ENV0EAr6dnZYv2yP9TBlgKSgt7KQu8S1Miaq4wYYw3QfUp1w/640?wx_fmt=jpeg&from=appmsg)
