# Q053：如何设计跨机房灾备而不盲目追求双活？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/d5KXYIo7nmAxp61Jl_Zj9Q
> 发表时间：
> 迁移时间：2026-10-25

假设一套订单系统的主机房突然失电。故障前，备机房的复制状态一直显示正常。值班人员准备把流量切过去，可用户仍无法提交订单。会上马上有人问：如果当初做了双活，是不是就不会停？

这个问题问早了。备站有数据，不等于它能独立完成一笔订单；两地都在运行，也不等于链路断开时都能安全接单。

设计跨机房灾备，应从一笔业务在故障后怎样恢复出发，先定可接受的数据损失和停服时间，再选备站与复制方式。双活只解决其中一部分服务连续性问题，不能代替完整的恢复路径。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdUlbzVr2MT9wibvJwYI7tOibXN02mBVBdNFsJlRLiciayG23ZWJRFXjVFicW80vDwsUzULRK1IEicibuZq7PkWVDP36HnPELAlvoDbuJg/640?wx_fmt=png&from=appmsg)

# 先别切流量：这笔订单停在哪？

主机房失电前，最后一笔向用户显示“提交成功”的订单，备站里有没有？如果使用异步复制，主站可能已经确认写入，变更却还在路上。此时要找的是备站最后一个可共同恢复的业务时点，而不只是复制界面显示的“延迟几秒”。

还要看订单、库存、支付记录是否能对得上。它们可能分布在不同数据库或消息队列里；分别恢复到各自“最新”的时刻，不一定能拼成一致的交易状态。对缺失或未完成的订单，是补录、重放、对账，还是让用户重试，必须由业务规则决定。

这就是 RPO 的实际含义：故障后最多接受丢失多少已发生的业务数据。RTO 则问从故障到订单功能重新可用，业务最多能等多久。两者都应按具体故障场景约定，并用演练测量；不能把存储复制周期直接当作业务恢复承诺。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdU6bSBGfOk3wgHCkTgzPjcz2X2alhecjDfmJzGoL9GicWAUHnSyd0vYLQQ0nXRxKdL2ykdqoYaykYACHcqPpOzku7lVKXRibEr9k/640?wx_fmt=png&from=appmsg)

# 数据到了，为什么还是接不了单？

值班人员在备站启动数据库，应用却登录失败：身份认证仍指向主机房。把认证服务补上之后，证书或密钥可能取不到；应用起来了，入口流量还指向旧地址；页面能打开，支付接口却没有从备站访问的路径。

沿着这一笔订单走，就能发现灾备不只是复制存储卷。备站要有足够的计算容量、可用的身份和密钥、配置与网络入口，还要按依赖顺序启动。数据库可恢复，不代表跨库事务一致；虚拟机都亮了，也不代表用户可以下单。

因此，设计时我会先画一条“最小可用订单”的依赖链：用户入口、认证、应用、订单库、库存、支付或消息处理。逐项标明备站是否独立、谁负责切换、故障时能否降级。若两地共用同一个会随主站失效的控制入口，机房虽然分开，关键依赖仍是单点。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdWibwj7Kkn6TGFGmiavsbSbLdLwVlcmKXicbM77rAX73fV5w97znlWYQ5jvjyzQZe1mGoYrbIYHdJYCStm2cHuRmJp0FY3ssqCPCY/640?wx_fmt=png&from=appmsg)

# 走到这里，才谈要不要双活

如果业务允许明确的数据损失和恢复窗口，主站服务、备站待命的架构可能已经够用。备站可以只保留数据和少量核心组件，也可以保持一套缩小规模的应用常驻；常备得越充分，接管动作通常越少，日常投入也越高。选择要由实际 RPO、RTO 和演练结果倒推。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdXQsAPb4Ukd68Wq0oFqjpVvTYB5KqUXolDfiaEuflJ90W7QwWGZSKKXtnxcLKfmFlP3MV7obqg1jaI1ic7DuAsDiblUNtIOMnS2pU/640?wx_fmt=png&from=appmsg)

若这笔订单必须在任一机房失效后几乎不中断，才值得评估两地同时承载服务。但“双活”还要回答：同一笔订单可以从两地入口提交吗？谁拥有写入权？两站都活着、跨站链路却断了，哪一站继续接单？如果两边都独立写，同一订单或库存可能出现无法自动合并的冲突；如果为防止分叉而暂停一侧，业务也并非始终无感。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdUNh53ntx6suw7QPYWo2xq26Hm0vOSCEm0HTPsxfQXJiazvLLiaeLY4yDvzlSrW4NabNs6bkf2iblBOxZLHdSMPkmAmbGqywgfLjU/640?wx_fmt=png&from=appmsg)

同步复制可以缩小特定条件下已确认写入的丢失风险，却把跨站确认带入写入路径；异步复制通常减轻前台对跨站往返的依赖，但需要处理未送达的变更。它们解决数据何时到备站，不会自动解决认证、应用路由和订单对账。误删或错误发布还可能被一起复制，所以独立备份仍要保留。

# 第一笔订单成功后，还要能回去

演练不能停在备站页面打开。要从宣布故障开始计时，确认一笔新订单能提交、库存和支付状态能核对、未完成订单有处理办法，并记录最终使用的恢复点。主站整体失效与两站仅链路失联，也应分开测：前者考验接管，后者考验仲裁和写入所有权。

主机房恢复后，权威数据已经在备站。此时原站不能一上线就重新接单；要先确认哪份数据为准，重新建立保护、补齐差异，验证应用与入口，再安排回切。只证明“切得过去”，没有证明“切得回来”，灾备路径仍只走了一半。

回到开头，故障前那盏绿色的复制灯，只回答了数据路径的一小段。真正的验收是：故障后最后哪笔订单可信，下一笔订单何时能成功，期间哪些交易需要处理，以及恢复后能否安全回切。这些问题有了可重复的答案，再决定是否值得为双活付出跨站协调的成本。冷备、热备和双活的名称口径可能不同，最终仍要核对业务可用状态、写入归属与实际恢复结果。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdXTnZLiaLuTNzEQXwp9JgoogBEkgqMDaLIg2Ou2zmnQLNXbvfRyDgBJdYSkXcKmVYfP3JGmuuIGCvCSPucUEZ6FdPnz0tiaIfrGk/640?wx_fmt=png&from=appmsg)

想补齐跨机房复制与容灾的基础，可以读张冬《大话存储（终极版）》第 17 章，再回到自己的业务路径检查接管与回切条件。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdX1hxGcZ5HSXicKvTtsQ77a2etOjvkXFQnwiazs3AzVt7ZCibNFicuRZYWY8xBLMMGwatl6A9eYwEy3HlFOoxy9dFgFFc3usQ1DQbk/640?wx_fmt=png&from=appmsg)
