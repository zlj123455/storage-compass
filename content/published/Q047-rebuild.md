# Q047：磁盘重建窗口为什么是可靠性风险？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/a4b7ix5lJqXv9xSveMQepA
> 发表时间：
> 迁移时间：2026-10-25

假设一块成员盘在业务高峰前失效。阵列仍然在线，热备也开始接管，于是团队认为 RAID 已经消化了故障，只要等待进度条走到 100% 就行。

真正危险的恰恰是这段等待时间。

重建窗口不是单纯的复制耗时，而是存储从失去一部分保护能力，到重新获得完整冗余之间的风险暴露期。窗口越长，系统越久地处在容错边界收紧、后台负载升高和潜在错误被集中触发的状态。判断可靠性时，必须同时观察剩余容错能力、前台业务影响和恢复全过程，而不能只问“重建需要几小时”。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdVXvswMqqnvMQURicBxjApuY3Xmgia66lLLL3T3Eap0S7Z84AFxtsdVWwubtmyg9EmYB1f9ia0gU1KfM8uqK4PHIjjkqxttMq7Jjk/640?wx_fmt=png&from=appmsg)

# 风险窗口不从更换磁盘开始

第一块盘失效后，系统可能先经历告警发现、故障确认、备件定位、现场更换，再进入重建和一致性检查。即使有在线热备，自动重建也只是缩短了其中一段。

我会把窗口定义为：冗余能力下降开始，到数据重新达到预期保护等级并完成校验为止。Linux MD 将recover定义为替换或重建成员盘，将check、repair与恢复状态分开，说明“数据已经复制完”和“冗余已经验证”本来就是不同检查点。

# 第一次故障会改变第二次故障的后果

健康状态下，RAID 5 的一份校验、RAID 6 的两份校验和 RAID 10 的镜像对提供不同保护。第一块盘失效后，剩余边界随布局改变：RAID 5 不再有额外整盘容错；RAID 6 仍保留一层；RAID 10 则要看第二次故障是否落在同一镜像对。

因此，风险不能写成一个脱离布局的“第二块盘故障概率”。更有用的问题是：当前已经失去什么保护，下一种介质错误、盘故障、控制器异常或误操作会影响哪些数据？

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdUwia5cIkMibXt3RjvP1LoTIPt7uDMFgAMpMDDMwibzpG5zqHfwxAicC092OJInyV336sY7qErbia212QSxVX0qgcQ0I0e2aoyWrFSY/640?wx_fmt=png&from=appmsg)

# 重建会主动读取原本沉睡的数据

校验 RAID 通常需要读取其余成员上的条带并重算缺失内容，镜像布局也要读取存活副本。这个过程会访问大量平时未必被业务读到的数据。

FAST ’10 的现场数据研究指出，潜在扇区错误往往要到对应扇区被访问时才会暴露，并可能在 RAID 重建期间造成数据损失。后台巡检可以提前发现并利用尚存冗余修复部分问题，但不能把风险降为零。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdXrepiaGzdXPrEl8fKBpKqpc1gziaGicdvQkhoG8XAHicNmKacyLct6oldXUca98hW1rXhzAek5Ujel6r3vX13fu7xiaGgyNF6cASicY/640?wx_fmt=png&from=appmsg)

# 重建越快，不代表业务越安全

重建与前台 I/O 会争用介质带宽、控制器、网络和队列。把恢复优先级调高，保护能力可能更快恢复，却可能推高业务 P99；过度保护前台，则会把风险窗口拉长。

Linux MD 暴露实际同步速度和进度；Ceph 的 mClock 也分别调度客户端请求与后台恢复，并明确提示修改恢复、回填限制可能产生意外性能结果。

所以我不会把“最高重建速度”单独写进验收指标。需要寻找的是业务延迟和冗余恢复时间都能接受的运行点。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdUJkQlU2Gg1viaEOFFSBJEUEHFkBDfYHjtoPibtYrvUcibxRib7k1aicrETcDMiaTqFYVJ5icB21dMqJ4vLbOXOL0pwA52G5icicw42by2c/640?wx_fmt=png&from=appmsg)

# 预计完成时间会不断变化

用磁盘容量除以标称带宽，算不出真实窗口。有效数据量、前台负载、随机访问、重建限速、后台巡检、剩余盘状态和替换后的回拷都会改变进度。

现代分布式 RAID 还能把备用区域和重建写入分散到多块盘，绕开单一热备的写入瓶颈。它通常可以缩短恢复，但也会把恢复流量扩散到更大的资源池；具体结果仍要看目标产品的数据布局和调度策略。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdUZCt6ibplKJKuehgZkL0lAQIquKb7xNiam0a4kXjDbSJxtVI9upUAUyW4k9cA018jibBpYyicbwwF8fpSJq80yUukLnE5yrUhkMdw/640?wx_fmt=png&from=appmsg)

# PoC 要记录完整时间线

测试应从正常状态开始，在授权环境中触发成员故障，并持续到冗余恢复和校验完成。至少记录故障发生、告警到达、热备接管或人工更换、重建开始、保护等级恢复和校验完成六个时间点。

每个阶段同时采集业务 P50/P99、吞吐、队列、重建速度、剩余容错、介质错误、备用空间和告警状态。还要验证重启、控制器切换和重建暂停后的行为；第二故障边界只应在具备回滚和独立备份的测试环境演练。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdUhzUW5E4crTq7vBL5IO3OOJrTDo8s9iaicE5AfqToyQT5SduG6A3AUe2F5UVZFdn7ZyLay6WMBpIyC1ttkLAVwibTEvo94zNNeUw/640?wx_fmt=png&from=appmsg)

我的验收标准是：团队说得清风险窗口从何时开始、何时真正结束，知道期间还能承受什么故障，也证明前台业务没有因恢复策略失去目标。缩短重建时间只是手段，尽快恢复可验证的完整保护才是目的。
