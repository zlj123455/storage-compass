# Q056: P99 时延为什么比平均时延更值得关注？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/XjSTPTmq8CN9njzpAwVQjg
> 发表时间：
> 迁移时间：2026-10-25

假设一位工程师排查数据库提交偶尔卡住的问题。存储监控显示，平均 I/O 时延没有明显异常。他准备据此排除存储，另一位工程师却问：那些卡住的请求，究竟等了多久？

平均值描述整体水平，不能说明每一笔请求的等待。对有响应时限的在线业务，P99 更值得关注，是因为它能揭示平均值容易掩盖的长等待。但它既不能替代所有性能指标，也不能单独证明卡顿来自存储。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdWIhsDwTvIdvd6bHgg3pyN7hLm4UEWN5vZfHwzlAua8sw8aJCgP4qMCK6k1MpegwY02lb7ibZcg17oK1CRqPkbAqibib2FjOnlWw8/640?wx_fmt=png&from=appmsg)

# 平均不到 3 ms，为什么仍有人等了 100 ms？

做一个纯算术示例，不代表任何产品实测。假设同一窗口、同一计时口径下记录了 10,000 个已完成的 I/O：9,800 个耗时 1 ms，另外 200 个耗时 100 ms。平均时延只有 2.98 ms，慢请求却并没有因此变快。

把这组耗时从小到大排列，P99 看的是 99% 分位位置。在这个示例里按排序位置取值，第 9,900 个样本已经落入那组慢请求，P99 就是 100 ms。

P99 的定义不是最大时延，也不是“最慢 1% 的平均时延”；这组样本中它们恰好都是 100 ms，并不意味着指标相同。实际工具可能采用插值或直方图估计，读数字前还要看计算口径。这个例子只是提醒我们：大量快请求，能把少量长等待稀释在平均值里。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdWvryHD5ZHJRl4nfuGnbdszcKYkQRSQ3vEd1DmZeMTyaovvJqyWb0ofVpBd0V2X10RHpgBY4zI2txtRe3raZ4sTyemjSmpPVIo/640?wx_fmt=png&from=appmsg)

# 业务等待的，不是“平均那一笔”

回到数据库提交。假如这次提交必须等一次同步日志写完成，恰好遇到慢 I/O，就不能因为其他写入很快而提前结束。这里说的是一种待验证的机制，不是已经确认的根因。

一笔操作若串行等待多个步骤，等待会累计；若同时发出多个分支，并且必须等它们全部返回，最慢的分支就可能拖住整体完成。慢请求出现在关键依赖上，影响才会沿着这条链传给业务。

所以，设备 I/O 的 P99 不等于事务的 P99，各层 P99 也不能直接相加。事务可能包含锁等待、计算、网络和多次 I/O；需要结合对应请求的记录，判断究竟在哪一步花了时间。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdUpujnMR0iazGJmAx1ZrAx5DRvzFibdGOdIuyDbogE6mRicfNz8ZFxBB7WTpve0XScRicnzeV0CmKzhsiat0p8NB0JibWlzCEia3pJic2A/640?wx_fmt=png&from=appmsg)

# 这张报表，到底把谁算进去了？

两张都叫 P99 的报表，未必能直接比较。读请求和写请求混在一起，可能遮住其中一类的长等待；fio 的提交、完成和总时延，也量着不同的时间段。

我会先问：量的是哪类请求，从哪里开始计时，在哪里认定完成，统计了多长时间、多少个样本？少量样本算出的高分位，可能随单个慢请求大幅跳动。

这个数字也不告诉我们慢请求何时发生。它们零散出现在一天里，还是集中在一段提交卡顿中，对排查的意义不同。因此还要保留时间序列，观察问题时段，不能只看全天汇总。

还要看超时请求是否进入统计。假如报表只统计成功请求，最慢的一批已经超时退出，显示的 P99 反而可能下降。用户遇到的失败却增加了。P99 变好，不能抵消错误和超时变多。

同样，不能把各节点或各时间窗口的 P99 直接求平均，得到所谓“整体 P99”。需要整体值，就从同口径原始样本，或可兼容汇总的直方图重新计算。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdXK7YCZibdcEGTyyXib61L6QUvGVRlicjE6bCPUSEoJ8IlMc7iaudkblPVm8D599aOxZHUbcvGt8GBm3ic81uQKiajujZW5x7Ians1bA/640?wx_fmt=png&from=appmsg)

# 看见 P99 上升，还没有找到根因

两位工程师应把业务卡顿与对应 I/O 的长等待放到同一时间线上，再沿请求记录追查。排队、调度、网络和后台任务，都可能是候选位置；时间重合只能提供线索。

如果存储侧 P99 升高，却找不到它拖住这笔提交的证据，就不该直接归因于存储。反过来，P99 正常也不能排除更稀有的严重长等待；必要时补看更高分位、超时和失败记录，更高分位还需要足够样本支撑。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdUY13qp8ChU04b22c2d1NYZ45hLRCfolJBzT6qkd9tHZUoQiaH4lLLicVS1eiaGdFIt0HEf3xWIQic54bg3VMYQQibibHEBBdiabFoEjI/640?wx_fmt=png&from=appmsg)

# 最后要问：目标负载下，能否按时完成？

选型时，我不会只拿两台设备各自最好看的 P99 比高低。应在相同请求组成、完成条件和计时口径下，逐级增加负载，同时看实际吞吐、P99、错误，以及业务请求的完成时间。业务有响应期限时，还应直接统计超期与失败的比例，不能用设备分位数代替。

如果减少负载后 P99 降下来了，只能说明它在这个负载下更快，不能证明它在目标吞吐下也达标。反过来，追求更高吞吐，也可能让关键请求付出更长等待，需要用测试验证取舍。

平均值仍值得保留；顺序批处理也可能更关注总完成时间和吞吐。只是对这次提交卡顿，应该换一个问题：在业务需要的负载下，长等待发生在哪里，又让哪些请求没能按时完成？

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdVickQZ7KyF51WPgJRS9UoyJKjbV5s4oV0mfYFBe78Ixn47NmQ9IKEib2OgUctEoMv1dXoGKWof14bHOlLmW5oFbu74SeshNTxRA/640?wx_fmt=png&from=appmsg)

想进一步理解请求为什么会等待，可以读张冬《大话存储（终极版）》第 19 章，从 I/O 路径和性能诊断入手，再回到业务中观察尾时延。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdX1hxGcZ5HSXicKvTtsQ77a2etOjvkXFQnwiazs3AzVt7ZCibNFicuRZYWY8xBLMMGwatl6A9eYwEy3HlFOoxy9dFgFFc3usQ1DQbk/640?wx_fmt=png&from=appmsg)
