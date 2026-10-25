# Q061：分布式存储为什么能横向扩展？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/gL6nmw2Txws_Eo_s4C5vRw
> 发表时间：
> 迁移时间：2026-10-25

假设一个存储集群接入了新节点。看板上可用容量明显增加，应用吞吐却几乎没动，扩容当天的尾时延还升高了。团队开始怀疑：“横向扩展是不是只会加空间？”

**横向扩展能增加可参与服务的容量和处理资源；业务能得到多少收益，取决于数据与请求是否真的分散，以及迁移、网络和热点成本有没有吃掉收益。** 节点数量只是条件，不是结果。

![图1：新增节点提供资源，业务收益还要看数据、请求和瓶颈是否转移。](https://mmbiz.qpic.cn/mmbiz_jpg/LF0nGncJCdU0mbG8ZWNjxPUvDPAnXxdicayVGjLEYOjQKebXjO224jv6gklicuZHDzgoC2KyGKWnxweMcybpic9BQbiacRBLMicMBD2l5LeC61Ko/640?wx_fmt=jpeg&from=appmsg)

## 多一台机器，工作如何分过去

单个节点有盘、CPU 和网口的上限。分布式存储把数据拆成多个可放置的单元，交给不同节点；客户端或服务层据此找到目标，多个请求才有机会并行处理。新节点进入同一资源池，相当于多了一组可承担这些单元的设备。

以 Ceph 为例，数据对象归入池和放置组（PG），客户端结合集群 map 与 CRUSH 放置规则计算目标 OSD。它不要求每笔业务数据都穿过一台中央服务器。这里说的是 Ceph 的实现路径；其他产品可能采用不同的元数据或路由方式。

但“可分布”不等于“已分布”。如果新增资源没有纳入业务池的放置规则，或者对象仍集中在旧节点，业务就不会自动使用新机器。即便已经分布，一个热点对象、单个客户端或同一条出口链路，也可能继续限制吞吐。

![图2：数据经放置规则分散到节点，热点和共享链路仍可能限制请求。](https://mmbiz.qpic.cn/sz_mmbiz_jpg/LF0nGncJCdUbqBzoibXRukBiag9Gr4I9oZZIqHy4B0Fae7PawrovyehOttSwv8AibQkLQ3HfdAlBXI0zu5PGNgHwibZvAkSEljeanVQvJ6kbArs/640?wx_fmt=jpeg&from=appmsg)

## 扩容是一个过程，不是一次开关

新 OSD 加入 Ceph 后，放置结果变化会推动部分数据回填到新位置。数据搬动使用盘和网络，还要与前台读写争资源。扩容中观察到时延波动，不能只拿扩容前与刚上线的瞬间做对比，就宣布设计失败或成功。

同样，若只是给集群加了节点，却没有足够的数据迁入，稳定后的容量分布和负载分布也未必相同。容量是“能放多少”；吞吐是“单位时间完成多少请求”；单次请求的延迟还受客户端、网络往返、保护动作和排队影响。这三个指标应分开验收。

![图3：扩容前、回填中、稳定后三个阶段，要分别看业务和后台负载。](https://mmbiz.qpic.cn/mmbiz_jpg/LF0nGncJCdU1VtIKWprSPItnSNRZYfB3XquNCqRbH0JlMEqOS0wY0VvrBuJogZGCicibibCaJicXqxx6Z07qFpACWs1tsrTR6QW2xMoj4icsDj4g/640?wx_fmt=jpeg&from=appmsg)

## 用原瓶颈预测收益，再拿业务验证

假设原来是多个 OSD 持续繁忙，而客户端与交换链路仍有余量。新节点接过一部分对象和请求后，总吞吐可能上升。若原来卡在单客户端、网关或上联，新节点带来的空间仍是真收益，却不一定改变当前业务吞吐。

可以用一张小表逼自己写清楚假设。以下是扩容评估示例，不是实测结论：

  

  
  
  
---  
  
  
---  
  
  
  
---  
原瓶颈| 新资源怎样参与| 迁移期代价| 稳定后要验证  
---|---|---|---  
多个 OSD 忙，数据可分散| 新 OSD 承接部分对象与请求| 回填占用盘和网络| 同负载下总吞吐、尾时延与利用率分布  
单客户端或共享出口已满| 新节点主要增加可用空间| 数据搬动仍可能扰动业务| 客户端与出口是否仍满；不能预报吞吐同比增长  
单个热点对象占主导| 增加节点但热点可能仍集中| 迁移不一定消除热点| 热点是否可拆分或改变访问方式  
  
  

![图4：判断表把原瓶颈、资源参与、迁移成本和验收指标接起来。](https://mmbiz.qpic.cn/mmbiz_jpg/LF0nGncJCdUy0wy1EAGDNpXxtLRp08ws5cMHVzkHa1NUu8JxOQYWyQPlibxB2JbvjibcO5b9N11SdqOjqHxRQyGL5DgnSpyo47vuoSEXZ69Cs/640?wx_fmt=jpeg&from=appmsg)

## 观察总量，也要看受伤的请求

验收最好保留同一业务负载或可复现测试条件。分别记录扩容前、迁移中、稳定后的容量利用率、数据分布、后台迁移量、业务吞吐和尾时延。把前台请求与后台回填放在同一时间轴，才能解释“总吞吐上去了，为什么某些交易更慢”。

不要只看集群平均值。如果一个池、某个 PG 所在节点或一组业务请求持续偏热，平均利用率降低可能掩盖局部排队。也要检查故障域和保护规则：为了追求均匀，把副本都挤进同一机架，并不是可接受的扩容收益。

![图5：集群平均值改善时，热点请求与尾时延仍需单独检查。](https://mmbiz.qpic.cn/sz_mmbiz_jpg/LF0nGncJCdUuNvUOibWxHGyVQJTIrC4RjlXAssHngm67U7icWKznX5JNVKX2XNLWAhWNqk8cblPQzV8GxgpzWDGibTIicEZ4fRPcIRtp0zJYxsE/640?wx_fmt=jpeg&from=appmsg)

最后给扩容一个可回答的问题：它原本要解除哪个限制？若答案是容量，就用业务可用空间与保护余量验收；若答案是吞吐，就证明请求确实跨更多资源执行，且尾时延没有越过业务边界。**横向扩展的价值，要在稳定后的业务路径上看到，而不能从节点计数推出来。** 不同产品的路由、放置和迁移过程可能不同，扩展收益需要在稳定后的目标负载下实测。

![图6：以目标瓶颈和业务指标验收横向扩展，不用节点数代替结果。](https://mmbiz.qpic.cn/mmbiz_jpg/LF0nGncJCdVtHaObicpkJYEpZTaBL77LFXec0YYxDIT7uO2rJiaP1UPrNJR19U5zKBUUgRP955cRC4u3S8ciae7FoFygCH9lqTB80ooxRMgPfw/640?wx_fmt=jpeg&from=appmsg)

加机器容易，把活真的分出去难。

有具体场景，随时找我聊；想进同行群，回「进群」就行。

![联系方式](https://mmbiz.qpic.cn/sz_mmbiz_jpg/LF0nGncJCdW5y9L82LB39lrVbI07IC2Axzj69lre6LvlDyY7uibWCeU1w6yTvicvFxMZpCywwzEPZb1WLVQjtUibD9f0aL9NJsZqxQclyEXD2g/640?wx_fmt=jpeg&from=appmsg)
