# Q051：勒索软件防护在存储层需要哪些能力？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/uGQ1Kgncsw04ARvdS4eMxQ
> 发表时间：
> 迁移时间：2026-10-25

假设周一 10:20，文件共享里开始出现无法打开的文档；10:30，异地复制已经把这些变化同步过去。管理员准备回到本地快照，却发现近七天的快照被人用一个高权限账号删掉。昨夜的备份任务仍是绿色，但调查又发现，异常改写可能在三天前就已开始。

此时团队不是没有副本，而是不知道哪一份还干净，也不能确定恢复后会不会把攻击者一起带回来。

存储层无法阻止所有勒索软件进入，但必须让攻击者难以同时改写生产数据、删除历史版本、降低保留策略并控制恢复系统。真正要守住的不是某一份数据，而是企业仍然拥有可信的恢复选择。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdX7ibQdMpTCwhJNzDpt0FGN0N8rzn5UZyqQXQ0JPv8PicVlVMkVEtzvIIn88eYcbRqNAQtS3BlBUOLYSPvleGmEqxen3GSgCEWxo/640?wx_fmt=png&from=appmsg)

# 攻击者为什么能让三份数据一起失守？

勒索程序通过应用或文件协议写入时，存储系统看到的可能仍是一次经过授权的修改。复制也不会天然理解业务意图：源端文件被加密、覆盖或删除，远端当前副本可能忠实地跟随变化。它解决的是另一处有没有新状态，不负责判断新状态是不是企业想要的。

攻击者还会寻找恢复系统。生产、存储和备份若共用高权限账号，或者快照保留策略能被同一个管理员随时关闭，那么攻破一个身份，就可能同时失去生产数据和历史版本。把副本放到异地，却仍使用同一身份体系和管理入口，也没有真正跨越这个故障域。

所以，存储防勒索不能只问“有几份”，还要问攻击者拿到哪一种权限后，能破坏到哪一层。

# 第一层能力，是把几种权力拆开

能够改写生产卷的应用身份，不应同时拥有删除快照的能力；日常存储管理员不应单独缩短不可变保留期；备份服务账号也不应成为生产环境的通用管理员。关键操作还需要多因素认证、临时授权、双人审批或独立安全角色。

这种分离并不会让攻击消失，但能增加攻击者一次清空所有恢复路径的难度。审计日志也要保存在攻击者难以同时修改的位置，否则事后只剩下“任务失败”，却无法回答谁改了策略、什么时候删除了恢复点。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdVMbTYvnGxCyyp5qQMrsnHJknV4pI902AOIibZRicPLdVEpkibOEiboRIwviavGZgOcROgUzEzcTox9BOHlGDM82FVPj2aP1Gfn5ATI/640?wx_fmt=png&from=appmsg)

权限隔离的代价是操作不再那么方便。紧急扩容、批量清理和故障处理都需要更明确的流程。但勒索防护本来就在用管理便利性，交换一次攻击后的恢复机会。

# 第二层能力，是留下删不掉的历史

不可变快照、保留锁定、对象版本和写入后不可改的备份介质，都可以在保留期内限制修改或删除。真正需要核对的不是产品页面上有没有“不可变”三个字，而是谁能开启它、谁能改变保留期、最高权限能否绕过，以及保护范围是否覆盖元数据和恢复目录。

还要记住：不可变不等于干净。如果攻击已经潜伏三天，今天锁定的副本可能只是把受污染状态永久保存下来。不可变能力保护恢复点不再被改写，无法替团队判断攻击从什么时候开始。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdVkMC6b5vEIz6Q5ianfSDNnlErHrpqOcVpzpNEMEyY6Mqum9H9NWPRHWxbeK5ys1geBZrwK5TEL5HLDVWeR0M8AmD4aWZUYTIss/640?wx_fmt=png&from=appmsg)

本地不可变历史也不一定足够。阵列、站点或管理域整体失守时，还需要独立系统、跨账号副本，或者平时不可直接访问的离线与隔离副本。它们如何取舍，留到 Q052 再展开；在这里，关键是避免所有恢复路径依赖同一设备、网络和身份。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdU3TAAXM8oALQTL7ibZv3t39B20m2flic1MkicicPbcuFib2vNPjibcy6dBmGaibPyBYyz3jiakrZV0Qicw4IkHBA57Pw4qicF9fXwnQbubQ/640?wx_fmt=png&from=appmsg)

# 第三层能力，是找到最后一个可信时点

批量改名、压缩率异常、短时间大量覆盖、快照删除和容量突变，都可以成为调查线索，但不能仅凭一个阈值自动宣布“这是勒索软件”。正常的数据迁移、加密项目和批处理也可能产生类似现象。

存储告警、文件完整性、应用日志、身份审计和备份目录需要拼成一条时间线：异常最早何时出现，哪些卷和目录受影响，复制何时追上，哪一个恢复点早于攻击。发现问题后，还要谨慎停止继续覆盖历史的操作，并保护现场证据。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdVRzdukuAOguhtJhkS1jXLl9MMvM2Pn7Xx9U7uaeib8qbD2MVqwNl0fDkTCTia5lAdRmExojh2ehY6pI8hLK1ld2ChoDh8jW6zpQ/640?wx_fmt=png&from=appmsg)

候选恢复点还必须满足应用一致性。文件能读、卷能挂载，不代表数据库事务、配置和依赖关系完整。真正的“干净”既包括没有已知恶意修改，也包括应用能够从这个时点正确启动。

# 恢复不能直接覆盖回生产环境

更稳妥的做法是在隔离环境恢复候选副本，同时重置受影响的管理身份、密钥和连接凭据。安全团队检查恶意文件和持久化机制，应用团队启动数据库或业务系统，核对关键记录、事务边界和访问结果。确认可信后，才逐步恢复对外服务。

这也是为什么“备份任务成功”不是防勒索验收。演练必须真的走完恢复点选择、目标环境准备、数据恢复、应用启动和业务确认，并记录实际丢失了多少数据、用了多久、哪些权限曾经成为阻碍。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdVv1F5hsYC6dfoiaap7dqS8sma7iaNxibWpiasNTFysMDhdDw1gfsDibZoSI2HLaqQIicKKlEeHEOlibA97DZ1FDyv2WlziaKibufo1Z7Sk/640?wx_fmt=png&from=appmsg)

# 验收时，我会追问六件事

谁能改生产？谁能删历史？谁能降低保留策略？恢复副本是否跨越账号、设备和站点故障域？团队如何找到最后一个可信恢复点？能否在不信任原生产环境的情况下恢复并验证应用？

如果这些问题没有明确答案，再多快照、复制和备份图标也只是“看起来有保护”。存储层防勒索的价值，是在生产已经失守之后，攻击者仍无法同时夺走历史、权限和恢复路径。恢复副本的保护还需配合身份治理、事件响应与环境清理；不可变和隔离不能撤回已经发生的数据外泄。

想把快照、备份与恢复副本的关系理清，可以读张冬《大话存储（终极版）》第 16 章，补齐数据保护的底层概念，再检查自己的恢复路径。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdX1hxGcZ5HSXicKvTtsQ77a2etOjvkXFQnwiazs3AzVt7ZCibNFicuRZYWY8xBLMMGwatl6A9eYwEy3HlFOoxy9dFgFFc3usQ1DQbk/640?wx_fmt=png&from=appmsg)
