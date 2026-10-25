# Q055: 如何设计可复现的存储基准测试？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/RVgJC1SHjfTIjCp2yV_V1g
> 发表时间：
> 迁移时间：2026-10-25

假设两位工程师用同一台主机、同一条访问路径和同一个专用测试卷，先后运行同一份 fio 脚本，复测持续随机写。第二轮成绩与第一轮不同。两人核对了命令，又各跑一次，数字还是对不上。

问题出在这里：他们保存了脚本和成绩，却没有完整记录每轮开始前做过什么、成绩取自哪段运行过程。可复现的测试，要让别人按记录重建条件，检查结果能否重现，并追查差异来自哪里。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdW6ewdCsjicer34UwAruQRHyLc0LsHtopcXGyWYuyojicvWTUKJNK1ZvX4rgAyKxjVJzna41mxEEf9RHmtb58fqGrL1GcfRwibvW8/640?wx_fmt=png&from=appmsg)

# 先确认，两轮测的是同一件事

这次要回答的问题很具体：同一组持续随机写基线，能否被另一位工程师重做？先把工具版本、测试目标、请求大小、并发和写完成口径对齐。开始计时和认定完成的事件也要一致，否则同名的“写时延”可能量的是不同过程。

同一份脚本还可能引用不同的数据文件或外部配置。因此，交接时要留下实际生效的配置、访问路径和数据准备方法，不能只发一段命令。

# 脚本执行成功，这轮成绩就能比较吗？

还要看实际负载。比如 fio 里设了队列深度，I/O 引擎和系统限制却可能让它达不到目标。输出中的深度分布需要核对，而且它反映的是工具侧在途请求，不能直接当成设备内部队列。

出现报错、中断，或负载不满足预设条件，这一轮就要标明原因，保留记录后查证，不能照常拿吞吐数字比较。如果压测主机先成为瓶颈，成绩仍能说明这条路径的表现，却不足以证明存储的能力上限。

所以我会先检查这一轮是否有效，再讨论数字差多少。即使负载对上了，两轮也可能从不同状态开始。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdXP0kQEIxWuXNiaMliaAicbPjoM3mZiaKwN0356vcUKSEkibblYornMnHsyeUy7y5uEUg7osZLTHjPjat17D7IdxGIBZwv8qh2PUKgo/640?wx_fmt=png&from=appmsg)

# 上一轮测试，已经改变了下一轮的起点

回到两位工程师的记录。假如第一轮开始前，测试卷刚完成数据准备；第二轮开始前，它已经承受了一段持续写入，两轮的写入历史就不同。这是一条需要验证的假设，不能仅凭第二轮变慢就认定原因。

存储会被测试本身改变。以 NAND SSD 为例，此前的使用状态会影响后续性能；垃圾回收等后台过程也可能利用空闲时间开展工作。因此，连续重跑和等待一段时间再跑，未必具有相同起点。重新启动 fio，并不会把这些状态一起复原。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdVgB1pMZy4ibS52CMfb2MVcneWmSbA89N1h7mNVjVib2kNEstWQXPkibtBtgMFdjDjD0yCC4dJibKwlaqLvszfjgIRynKjYXohP0TA/640?wx_fmt=png&from=appmsg)

要补齐的，是一段准备过程：测试范围是否已经真实写入数据、占用空间是多少、此前运行过什么负载、两轮之间如何安排。温度、后台任务和各层缓存状态也应留下记录。准备方法必须对应测试目标，写入操作只在确认可覆盖的专用测试卷上进行。

接着把准备、预热和正式采样分开。fio 的预热时间只是让负载先运行一段时间，再开始统计；时间到了，并不能单独证明存储已进入稳态。

对这次持续性能测试，应事先规定观察窗口和判定方法，检查连续窗口中的趋势与波动，再决定能否按稳态口径报告。运行到约定上限仍未满足条件，就注明“未达到稳态”。不能看完曲线，才挑最平坦的一段当成绩。

这里真正要复原的，是进入测量阶段的过程。没有这段过程，两个看似相同的平均值，也可能来自完全不同的运行阶段。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdWiaf8tEoyyUcfKia9YydRwKos3Haibtd6w72Hd5J1zF7fTtQ5QelJ3RLjnHV1yLpict32jrIGTZcBSMTfMictmUthLia6ZgubYdrrT8/640?wx_fmt=png&from=appmsg)

# 再跑几轮，看结果和波动能否重现

补齐准备方法后，再按同样的规则复测。每轮都保留实际负载、时间序列、错误和汇总结果，比较典型水平、趋势与波动。前一轮留下的状态仍要处理和记录，不能把连续点击“运行”视为条件已经一致。

如果每轮都出现类似的周期性抖动，这也是需要解释的结果。可复现、性能稳定和业务达标，是三个不同判断。把抖动反复测出来，可能恰好帮助我们识别一个需要继续调查的问题。

测试时长、轮数和容许差异要结合目标与测量波动确定，没有适用于所有存储的统一数字。比较方法应提前约定；若差异仍解释不了，就保留这个结论，继续找证据。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdXM0YJyZMph9gz45JPy3F2SggT0YsqUPoTofMENV7QXxC5RmfukVxIiccaZTcdHfolyoduHjSm5WajpTmC12iaHHqxa3pibMS1WDg/640?wx_fmt=png&from=appmsg)

# 把过程交给下一位工程师

两位工程师下一次交接时，除了脚本，还应带上环境、数据与状态准备方法、执行和采样顺序，以及各轮完整结果。请对方按记录重做，缺什么条件，就补什么条件。

这会增加准备时间和写入成本，却能让一次跑分成为可以复核的证据。结论也应说清：在什么条件下观察到了怎样的表现，哪些差异已经解释，哪些仍需验证。至于这组负载能否代表生产，还要回到业务本身判断。SSD 设备级的稳态方法不能直接套用到所有阵列或分布式系统，状态准备须随测试对象调整。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdXBVCUxs20Jx07HQcgC4aGLnLXdbND9W6zuZJOpuoJHAkQjlIjMyILOqRt9ND3tohm3qArF1NBiau6tDMxOE4erd177nIiaflVS8/640?wx_fmt=png&from=appmsg)

想为存储测试补齐机制基础，可以读张冬《大话存储（终极版）》第 19 章，先弄清被测请求经过哪些层，再设计能够复核的对照实验。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdX1hxGcZ5HSXicKvTtsQ77a2etOjvkXFQnwiazs3AzVt7ZCibNFicuRZYWY8xBLMMGwatl6A9eYwEy3HlFOoxy9dFgFFc3usQ1DQbk/640?wx_fmt=png&from=appmsg)
