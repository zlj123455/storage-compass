# Q011：IOPS、吞吐量和时延应如何一起理解？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/oatIoZW26SxbT_pSTXJLYA
> 发表时间：
> 迁移时间：2026-10-25

PoC 验收会，厂商演示完一轮压测，PPT 翻到那页大字：50 万 IOPS。业务方很满意，觉得系统肯定快。存储团队的人举手问了一句："这个 50 万 IOPS 是用什么块大小、什么读写比例、什么队列深度跑出来的？"厂商沉默了一下，说：4KB 随机读，队列深度 32，纯读。存储团队说："那这个数字不能直接用来判断我们的数据库会不会快。"![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdWB4oJ1EBZxiaehD99BbCwUTYUUQ5JUPhY445QwAhibzP2u2nibPsmwTNH5ibxhWXicrvNvkIPdYS5m6cJTp7icCYzgEo8Rb0czeQJE8/640?wx_fmt=png&from=appmsg)IOPS、吞吐量和时延不是三张独立的成绩单，而是同一份 I/O 工作负载在同一运行点的三个观察面。

# 一个 I/O 是什么

业务方问：50 万 IOPS，换算一下不是将近 2GB/s 了吗？存储团队在白板上写了一行：

  * 

[code]
    带宽 ≈ IOPS × 单次 I/O 大小
[/code]

50 万 IOPS × 4KB ≈ 1.95GB/s——但前提是每次 I/O 只搬运 4KB。换一个场景：1,000 次/秒的 1MB 大块 I/O，IOPS 只有前者的五百分之一，带宽却是 1,000MB/s，反而更高。前者 IOPS 漂亮，后者搬运的数据更多。两者没有谁天然"性能更好"，因为它们服务的工作负载不同。这也是规格表最常见的省略：只写 IOPS，没有同时写块大小、读写比例、顺序/随机和测试并发。脱离这些条件，IOPS 只是一个请求计数器，不能直接映射到数据库提交、文件打开或备份窗口。![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdVznnn4pKGy9ibhErKfZlVibBWibCsVrA1Nibh6h925ZZTblqMPibDJMmUVOmoZHClWhmfRtKOvTadwKsIRLord3UMfzdYcibQib9Fviag/640?wx_fmt=png&from=appmsg)一句话理解：IOPS 回答"完成了多少次"，吞吐量回答"搬运了多少数据"，必须先知道每次 I/O 是什么。

# 时延藏在哪里

业务方又问：PoC 报告里写了平均时延 0.8ms，是不是说明系统很快？存储团队说：平均值能藏住尾部。一个请求从应用发出到完成，要经过文件系统、块层、网络、多路径、控制器和介质。任何一层资源暂时无法接收新请求，请求就进队列排队。Linux 的多队列块层就区分软件暂存队列和硬件派发队列：资源不足时，请求会等待后续派发，而不是立刻由设备服务。在运行稳定的近似条件下，可以用排队论的关系理解：

  * 

[code]
    在途 I/O 数 ≈ IOPS × 时延
[/code]

例如系统维持 10,000 IOPS、每个 I/O 平均 1ms，则大约有 10 个 I/O 同时在途。当到达速率接近系统处理能力，新请求开始排队。此时总 IOPS 可能还没明显下降，平均时延也尚可，但尾部请求已经开始等待——P99 会先变差。![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdUwPjibfjAOdTunS2uh2icuyTibIe6c8tLSAdb769AiaXwunJhYTN2bVe4jzicAF8V1CCzvGaecE72UrefSJOOzThLHrYTFfHI3UCBM/640?wx_fmt=png&from=appmsg)架构师补了一句：厂商演示时把队列深度从 1 拉到 32，IOPS 翻了好几倍。但这不等于业务体验更好。它可能只是让更多请求同时挂在系统里等待。对必须等写入完成的事务提交，单个慢请求就是用户可见的卡顿。不提供这个视角：厂商报一个平均时延数字，业务方以为"很快"，上线后偶发超时却找不到原因——因为尾部延迟被平均值藏住了。![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdWurlJxFk379xZt8CVY4WmpPYSoA85La1pfAyaG5vicDkqmPqqhpL4iaHCRaeGzHNc9xcgjowFIeU1NlWFOCuS9rqLHT1NYOdibZ8/640?wx_fmt=png&from=appmsg)一句话理解：更高并发可以提高设备利用率，也可能把等待时间藏进队列；要同时看 P99，而不只看平均值。

# 跑分高不代表业务快

业务方翻出 PoC 报告：4KB 随机读，50 万 IOPS，0.8ms 平均时延。为什么上线后数据库还是偶发超时？存储团队说：PoC 用 4KB 随机读、深队列跑出高 IOPS，证明的是在这个测试负载下能完成很多小读请求。而数据库高峰时，是以较低并发执行同步小写；日志确认要等写入路径完成；报表又在同一时间做大块顺序读。I/O 大小变了，读写比例变了，并发与完成语义也变了。原来的 IOPS 不能自动迁移到新场景。反过来也一样：顺序大块读写测出高 GB/s，只能证明批量搬运能力，不能证明小块随机写的尾时延。把"高 IOPS""高带宽""低时延"各挑一个最佳数字拼在一起，不是一个系统可同时兑现的运行点。架构师提了一个常见陷阱。压测报告写"队列深度 32"，不代表设备真的收到了 32 路并发——同步提交模式下请求排队等待，实际并发可能只有 1；数据走操作系统缓存时，请求也不会直接到达设备。参数是期望值，不是实际值。验收时必须看工具输出的实际并发分布，而不是配置文件里写了多少。![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdU8BLR9kTCCBZ9ibSOTykVJTtL4lLVPs8Or1bhK6GEH7Xia28GgkLCrSRJzcd3H6aXOlFicC3jiaSSWoqQEr9YJricopcu0sq4ib7p8E/640?wx_fmt=png&from=appmsg)一句话理解：跑分能证明某个工况，不会自动证明另一个工况；参数写了多少，不等于链路真正跑到了多少。

# 三项指标放回同一张验收表

架构师说，验收不该先问"最高多少 IOPS"，而应为每类关键负载写出一个运行点：业务场景| 必须提供的负载事实| 主要观察指标| 不能遗漏的条件  
---|---|---|---  
数据库提交| 块大小、同步写比例、并发、峰值时间| P99/P999 时延、业务超时、队列| 前台写入与后台任务并发  
批处理或备份| 顺序/随机、大块比例、数据量、完成窗口| MB/s、完成时间、失败与重试| 不得挤占关键交易窗口  
文件或共享目录| 小文件比例、元数据操作、客户端数| 操作时延、并发打开失败率| 缓存命中与权限/锁语义  
故障或恢复期间| 降级策略、恢复目标、前台优先级| P99、恢复进度、业务错误| 重建/复制与生产 I/O 同时发生  
验收记录应保留请求分布、实际队列深度、时延分位数、业务错误和测试时的系统状态。业务方问：那带宽和时延哪个优先级更高？架构师说：对可离线重跑、只关心批量完成时间的工作负载，带宽放首位；对交互式事务，先定义尾时延和超时边界。重点不是追求一张更漂亮的规格表，而是证明：在业务真正提交请求的方式下，系统仍能完成业务承诺。![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdVcwWUx19ibdUlkfXx9pgtMYyumr23HF0SWtBgWkEQGpGQJn1vfZOTsjTic2QvyogrAdeiaT4CMHURsibic2XS05CnicWqk45BSia0wmM/640?wx_fmt=png&from=appmsg)

# 怎么设计一个不骗自己的 PoC

业务方最后问：那 PoC 应该怎么跑？存储团队说，固定一个变量矩阵，而不是只跑一次"最大性能"：

  * 块大小：4KB、16KB、128KB、1MB 分别测
  * 读写模式：顺序读、随机读、顺序写、随机写分开，不把混合负载平均成一个数字
  * 队列深度：从 1、2、4、8、16、32 逐级增加，记录每级的 IOPS 和 P99
  * 先预热再记录稳态窗口，单独记录缓存命中和后台任务
  * 输出时延分位数、实际并发分布和设备层统计

验证的重点是找出"吞吐—P99"拐点：队列深度加到多少时，IOPS 不再增长而 P99 开始飙升。这个拐点来自哪一层——控制器、网络还是介质——才是选型的真正依据。![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdUKSVP71GajiaiajSVQzPrfLWhq4zVqeSZEiaTSHOQLkOb0FWWk2G7Ekj0QUSDmjxkjpS4yXv2uzH3nJPx3FgicbVtmC17a1Sh1Yys/640?wx_fmt=png&from=appmsg)没有实际深度和尾时延的测试，不足以支撑选型结论。
