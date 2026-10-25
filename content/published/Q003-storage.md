# Q003：一个 I/O 请求进入存储系统后发生了什么？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/HCJYjuj7qTVH_QWNEBPu4w
> 发表时间：
> 迁移时间：2026-10-25

数据库提交突然变慢，虚拟机偶尔卡顿，备份窗口越拖越长。团队打开监控，却发现存储带宽没有跑满、SSD 也不像“很忙”。于是有人说：问题应该不在存储。这个判断并不可靠。业务等待的不是一条链路搬了多少数据，而是一个请求从发出到满足“完成条件”用了多久。小块随机 I/O、同步写、元数据更新、队列等待、网络重传、路径切换和后台重建，都可能先推高 P99，却不一定把总带宽打满。所以，理解存储性能的第一步，不是背某块盘的 IOPS，而是把一次 I/O 当成一条端到端的请求链来观察。![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdXHliaMpMGP6xCZdaQTJWibEeFXYYdXicQRicWtc7N20vibfxdyd3INia1gcVuPibs9rTMUK5pnPh2dZzct4iaw6pzibAYcgvTYIGw3c04I/640?wx_fmt=png&from=appmsg)

# 先别急着看盘：应用到底在等什么？

同样是“读数据”，数据库读页、文件服务读文件、虚拟机读块，产生的请求大小、顺序性和并发度都不同。更关键的是，应用记录的耗时里可能还混着线程池排队、文件锁、事务锁、超时重试，甚至根本没有走到存储设备。因此，排查 I/O 之前先问四件事：读还是写？数据还是元数据？请求多大、并发多少？应用把哪个事件定义为完成？如果这些问题没有答案，单独比较 IOPS 没有意义。

# 读请求：先经过缓存判断

读请求命中页缓存时，数据可能直接从内存返回，设备根本没有收到 I/O；未命中时，才继续穿过文件系统、块层、协议和设备。这意味着两件事：应用变快，不一定是盘变快了，也可能只是工作集进入缓存；设备没有 I/O，也不代表应用没有等待，它可能正卡在锁竞争、缓存填充或别的线程上。![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdWqZianhPJcebrXgRs4hicXnspVyASx5kwfAIdAAOdibJdO6xVqGmPvT3IeXCBwu3lzpXPkVLHwv3rzuzymgcj2qm7Oz3L4AGgLics/640?wx_fmt=png&from=appmsg)

# 写请求：先说清“成功”是哪一种成功

写路径最容易产生误解。`write()` 返回成功，通常只表示数据已被某一层接受，并不自动等于数据已经稳定写入最终介质。`fsync()`、块层 flush/FUA、设备写缓存、阵列缓存、远端副本和备份完成，对应的是不同的时间点。也就是说，“应用已返回”“断电后不丢”“节点故障后仍有副本”“可以从备份恢复”是四种不同承诺。把它们混成一个“写成功”，性能测试会更好看，但恢复设计会留下空洞。![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdXib83WHbJfxtGV0y4DVI3AYKCc3gIf4VUra4DzuEQrMYr9KjEddpyTyNUoxlMD0Lv5sbjhczIiactNJEngu42GDVuYicT0QfwH1A/640?wx_fmt=png&from=appmsg)

# 一次业务操作，为什么会变成许多底层 I/O？

业务写入的不是“一个磁盘块”。一次数据库事务可能同时修改数据页、事务日志和元数据；一次文件创建也可能带来目录项、权限、时间戳和日志更新。文件系统把业务语义转换为数据块、元数据和日志，块层又可能拆分、合并并重新排队。因此，业务侧的一次操作与设备侧的一次 I/O 通常不是一一对应。只看设备平均块大小，很难反推出究竟是哪类业务制造了压力；反过来，只看业务 TPS，也无法知道底层形成了多少写放大和同步点。![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdWiaiaGRI2AgibJqnafR0rMhiamNBnPpxvEp2Tzn6J6zM1xoicziaU9YLTW58JaBfqTBBZkibj12olW1DDZhic6dXRBC8rxfjZazbWPsns/640?wx_fmt=png&from=appmsg)

# 队列深度不是越大越好

现代 Linux 块层和 NVMe 设备可以并行处理多个请求。适当增加并发，能让设备获得更多可用工作，从而提高吞吐；但设备或控制器接近饱和后，新请求只会在队列里停留更久。这就是为什么“吞吐还在涨”与“业务已经超时”可以同时发生。平均延迟会把少量长尾掩盖掉，而数据库提交、交互式查询和虚拟桌面往往先被 P99/P99.9 击中。还要警惕一个测试误区：fio 中写了 `iodepth=32`，只代表测试工具希望维持的深度，不保证设备真的看到了 32 个在途请求。I/O 引擎、同步或异步模式、页缓存和作业数都会改变实际深度。测试时要同时核对 fio 的 depth distribution 与主机块层统计。![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdXicribXcSe8OD5r8mN1ORoiakzXLluHiaceucJmXDpsk3PuYyJJKCIyJt3dEopiab8wKrSJkVNPSGgzX5nBPBU1QL5VC9zbVCgx4xc/640?wx_fmt=png&from=appmsg)

# 网络存储的瓶颈，不只在“网速”

如果设备在网络另一端，请求还要经过主机发送队列、协议栈、交换网络、目标端接收队列、多路径软件和远端控制器。链路带宽决定可搬运的数据上限，却不承诺每个请求何时完成。少量丢包重传、短时拥塞或路径切换，可能只影响一小部分请求，所以平均带宽看起来依然正常，尾延迟却出现尖峰。此时只盯端口利用率，往往会错过真正的等待点。正确做法是把应用超时、主机队列、协议重传、多路径事件、交换机端口和存储端口放在同一条时间线上。如果各系统时钟都没对齐，“大家都正常”只是因为看的不是同一秒。![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdWnSicJIqLUz6C6kYxRXgLPDulqkmPqqjOiaVbNAACuJr58MibHGPeg0KoRzdicRgUgjbEmTe3C0icvwmbyr4NbyXciaZic2lM1d69l4E/640?wx_fmt=png&from=appmsg)

# 到了全闪阵列，也不等于请求立刻完成

请求进入阵列后，还可能经过控制器队列、缓存、压缩、去重、校验、条带化、镜像或纠删码布局，最后才到 SSD/HDD。与此同时，垃圾回收、快照整理、复制、迁移和重建会与前台 I/O 争用控制器、网络或介质资源。SSD 消除了机械寻道，但没有消除闪存转换层、垃圾回收、写放大、磨损均衡、温度限制和掉电保护；NVMe 提高了并行能力，也不代表主机 CPU、PCIe 链路和真实 workload 一定能把这种能力用起来。所以，“介质利用率不高”只能说明某个统计口径下设备没有满，不能证明请求没有在控制器、协议或数据布局层等待。![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdVDQzdPwFGlIcBPoTa0eAjMA30tAWpKr1xRT7WKh3iaMiaJnY4ibFdwvAt7lQXFd0KjsPhfa87yfyMghDdUVFcA4pAQ6rfyLEPQZc/640?wx_fmt=png&from=appmsg)

# 真正有效的排查，是还原一条请求时间线

面对“存储变慢”，不要先从某个设备指标开始猜。先选定一种业务请求，例如数据库日志同步写；再把应用发起、主机排队、协议发送、存储接收、持久化确认和应用完成串起来。然后比较健康期与异常期：等待时间从哪一层开始增加？队列是在上游堆积还是在下游饱和？有没有与路径切换、重传、缓存回收或后台重建同时发生？证据能在相邻两层互相印证，才接近根因。![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdVNUQOrCQHhTjvcJeX8eQ97H5ecJ2SU6b6AMiccHgsOJCNntQOVAmknIAwZQTtQGdLIGlbVLtlia3SBRgjozF3UCj97YPV2uBjB4/640?wx_fmt=png&from=appmsg)

# PoC 不该只回答“最高能跑多少”

一份有决策价值的存储 PoC，至少应该保留真实业务的请求大小、读写比例、顺序/随机特征、并发和完成语义；并逐级增加负载，记录吞吐、平均延迟、P99/P99.9 与实际队列深度。更重要的是，用同一组 workload 重复测试健康状态、路径切换、节点故障、重建与恢复阶段。若一套系统只在缓存温热、没有后台任务时表现优秀，我们验证到的只是最佳状态，不是业务真正购买的稳定性。![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdVDTfyUibMCT8vyoNN1LuUw7lFoqATZSibL8smLakXKRNdDBPhCDibFiagicD1m4H8aVPZicUgcAOjibt95zbHz0EvftojuXPktFBVeaU/640?wx_fmt=png&from=appmsg)

# 最后记住一句话

一次 I/O 不是“应用把数据交给磁盘”，而是一连串具有不同队列、缓存、协议和完成语义的状态转换。带宽没跑满，不能排除存储；设备很快，也不能证明业务会快。真正专业的判断，是先定义业务在等什么，再沿同一条时间线找到请求在哪一层等待，以及优化之后，队列究竟被消除了，还是只被搬到了别处。
