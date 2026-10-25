# Q064：分布式存储的副本数和纠删码如何选择？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/zEn6Ir9d_wsJRrsfuGNZww
> 发表时间：
> 迁移时间：2026-10-25

假设同一集群既放数据库卷，也放大型归档对象。采购讨论先算空间：三副本太贵，换成纠删码是否就够了？值班工程师问的是另一组问题：失去一台主机或一个机架后还能否服务，剩余空间和带宽够不够把保护补回来？

**选择副本数或纠删码，先按负载和故障域定义服务目标，再把容量、降级读写与恢复预算一起验证。保护参数是设计输入，不能单独充当业务可靠性结论。**

![图1：同一集群的数据库卷与归档对象，应分别定义保护和恢复要求。](https://mmbiz.qpic.cn/sz_mmbiz_jpg/LF0nGncJCdV2Rd5Wqh60pwpAGVh3Uxl75dM46Bbmg4A9zfsUKibl5hAxs6EDNKKicDzAibIjZL0RnicxQBIicqjve694dcBtia0LjbXJx5LdUlNJI/640?wx_fmt=jpeg&from=appmsg)

##  先把空间账算对，但不要只算空间

在只看数据片段的理论模型里，三副本存同一份逻辑数据，需要三份原始空间；4+2 纠删码把数据分成四片、再加两片校验，原始片段合计是逻辑数据的 1.5 倍。这个比较没有计入元数据、预留空间、放置不均、恢复余量和实际实现开销，也不是等可靠性或等性能比较。

纠删码节省理论保护空间，但编码、跨节点通信、部分写和故障恢复的代价与工作负载有关。Ceph 的纠删码池可用于某些 RBD、CephFS 数据场景，但需满足覆盖写等条件，元数据仍须放在副本池；不能把“支持纠删码”直接读成“所有随机写都适合”。

容量讨论还应把“可售空间”和“故障后必须保留的空位”分开。若理论节省的空间全部卖给业务，恢复目的地不足，故障后就可能长时间停留在保护不足状态。比率只帮我们筛候选，不能直接给采购清单定容量。

![图2：三副本与 4+2 纠删码的 3 倍和 1.5 倍只是理论片段开销。](https://mmbiz.qpic.cn/sz_mmbiz_jpg/LF0nGncJCdWwCp10p91hhO6oDR89OicpNM6TqWHHw541fs3dc4Fa0fJcM068dgvmretsXhZ1JIH6xOOSzLUMh4AwzDFvEJTUs9cTyBzgg3vE/640?wx_fmt=jpeg&from=appmsg)

## 副本或校验片要跨过真正的故障边界

如果多份保护单元落在同一主机，失去主机可能同时失去多份；如果集中在同一机架，失去机架的结果又不同。Ceph 的 CRUSH 层级和规则可按主机、机架等故障域放置副本或纠删码片段。设计时先明确要承受哪一级共同故障，再检查拓扑是否真的有足够独立目标。

即便数量满足要求，仍要分别问三个问题：数据理论上还能否重建？集群在当前状态和配置下还能否继续读写？业务时延与可用性是否仍达标？三者不会自动得到同一个答案。副本池的 size 和 min_size、纠删码配置及当前 PG 状态会影响服务条件，不能只看“丢了几个节点”。

![图3：保护单元必须按目标故障域放置，数量相同不代表故障结果相同。](https://mmbiz.qpic.cn/mmbiz_jpg/LF0nGncJCdWR2BozNNmNtqcHV5jsNoYX8YjEqhzhLhUaCusHtvXiakc5icyO1lFLbic0icrTIUnmzbEfdP0t3tHaHXo1h1QVHkeJq4Zh0Lk7JN8/640?wx_fmt=jpeg&from=appmsg)

## 故障后还有一笔恢复账

保护尚可读，不代表已经回到安全状态。重建或回填要有目标位置、可用空间、网络带宽和时间窗口，还要与前台业务争资源。若扩容计划把空间用到很满，故障后可能找不到足够目标来恢复保护级别；若只验证健康时性能，恢复期间的尾时延也可能超出业务边界。

因此测试至少覆盖健康、一个目标故障域失效、恢复进行中三种状态。记录可用容量、PG 状态、读写结果、前台尾时延与恢复进度。演练前应明确停止条件和回滚准备，不在生产中为验证一个假设随意拔掉共同故障域。

![图4：健康、故障和恢复中三种状态，都要同时看业务与保护余量。](https://mmbiz.qpic.cn/mmbiz_jpg/LF0nGncJCdUjGjL6Q4Ka02nMHVaYy4yl7R2g8p8mT91n31stawiau0z19hqmdnverlf5syJDtXQSpubu7yibvdeJk48ug7NUSdbDYhUwkRLuA/640?wx_fmt=jpeg&from=appmsg)

## 两类负载，先给出待验证的候选

下表只给出设计讨论的起点，不能替代目标集群测试：

  

  
  
  
---  
  
  
---  
  
  
  
---  
负载| 候选与原因| 放置和服务条件| 恢复验收与否决条件  
---|---|---|---  
数据库卷，频繁小写| 优先验证副本池；关注写入尾时延| 跨目标主机或机架；核对 size、min_size 与实际 PG 状态| 故障和回填时交易仍满足要求；若容量或写时延不达标，重做设计  
大型归档对象，顺序写读为主| 可验证纠删码池；评估空间收益| 按目标故障域放置 k+m 片段；检查接口与元数据池约束| 故障后仍可读写，余量和恢复时间可接受；否则放弃该组合  
  
  

![图5：两类假设负载的候选不同，必须把故障域、服务条件和恢复验收写进表中。](https://mmbiz.qpic.cn/mmbiz_jpg/LF0nGncJCdWyicEl0nlna2BCOc3jgNA6GlRfvOIlUJB5gaE4SoYkeJHtJ3exXt5jPrkxqZSn4pze4j6nItHPbbARWFuQr6al8tZZicqdoKRNo/640?wx_fmt=jpeg&from=appmsg)

还要留一道独立问题：误删、污染、勒索或应用写坏数据，副本与纠删码都可能忠实保留错误版本。它们承担设备或故障域保护，备份、版本与恢复点设计应另做。不要把“能承受两个片段失效”翻译成“无需备份”。

**真正的选择不是挑一个最省空间的数字，而是证明目标业务在正常、故障和恢复时都能守住约定边界。** 当负载、拓扑或恢复预算尚未量清，结论应写“优先验证哪种候选”，而不是宣布全集团统一用某个参数。理论容量倍数不包含所有系统开销，副本数、最低服务条件与编码参数还要结合实际故障拓扑和恢复结果验证。

![图6：最终决定由工作负载、故障域、服务条件与恢复资源共同约束。](https://mmbiz.qpic.cn/sz_mmbiz_jpg/LF0nGncJCdVMCjwpNibo72ibbYq9ctVH0eF0r4icHAnmSpbcMibkBu3ogicibN50FBmF7dDLZMMQoWQceIV8aNWrhIRzp2dnBdSn6a4wJ0zKekVMo/640?wx_fmt=jpeg&from=appmsg)

  

有具体选型场景拿不准？回「**进群** 」进『存储 100 问』同行群 —— 群里有选型答疑，也欢迎你带着真实场景来聊，我 1v1 帮你拆。

![联系方式](https://mmbiz.qpic.cn/sz_mmbiz_jpg/LF0nGncJCdVv2DHjCWrIWPHyYJ6CTXNjbXUWuxiaEGq7HI40oibBRQIOiaia3HSl6Nb7qwCvxcJ35xh1Gxp6darKlySdeYialDQtq5DwS70GXcSk/640?wx_fmt=jpeg&from=appmsg)
