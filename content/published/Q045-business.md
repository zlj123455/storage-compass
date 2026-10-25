# Q045：如何画出一个业务的端到端 I/O 路径？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/Y2medoWtv2DJsi2ZYebelw
> 发表时间：
> 迁移时间：2026-10-25

假设数据库提交出现尾延迟。应用、虚拟化、网络和存储团队各自拿出一张拓扑图：每张都正确，却没人能说明这次提交经过了哪个虚拟磁盘、主机设备、网络路径和阵列卷。

问题不是少了一张架构图，而是缺少一条能被证据验证的业务路径。

可用的端到端 I/O 路径图，必须从一个明确业务操作出发，标出每层对象映射、完成语义、排队点、故障域和责任人，并能用运行数据与故障演练验证。本文以块存储写入为主；文件、对象和云盘可以沿用方法，但接口与确认语义要重新核对。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdWJvv6viaQAX18ujtXjMsKqfayUhIDiarjVqk38IUib2DYrBTHdcvQ1529KBGE64ZmlianHYQzVTSllvGxgkKThXb7xwKUQWpcdCXw/640?wx_fmt=png&from=appmsg)

# 先选一个业务操作

不要从“整个核心系统”开始画。先选一个动作，例如数据库日志同步写、虚拟机读取启动盘，或者备份软件读取一个文件。写清入口、结束事件、读写方向、正常时段和异常时段。

OpenTelemetry 将 Trace 定义为请求经过系统的路径，Span 则记录一个操作的父子关系、起止时间和事件。它适合确定应用在等哪一次调用；但未被埋点的文件系统、块层、交换网络和阵列内部，不会因为有了 Trace 就自动透明。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdUTUiblu35hz8FsPVV56BMYRGYxyqV1HcZiaRicJmia7RF9WY4WXJGzguw4cs3yqwgmjG6ic8kW55QlzpB8LibhZRPTVialSichKOkibiapM/640?wx_fmt=png&from=appmsg)

# 主图只画真正经过的数据面

沿请求方向依次追问：应用调用了哪个文件或设备？是否经过客户机和虚拟化层？主机看到哪个逻辑卷或多路径设备？请求走什么协议、端口与路径？存储前端把它交给哪个卷、池、控制器和介质？

不经过的层不要为了“完整”硬塞进去。读缓存命中、写缓存确认、文件协议和块协议本来就会形成不同路径。主图应是一条能从左到右讲清的请求链，而不是产品组件清单。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdWwKjxib8Mwg1V7M9iah4ib0fPsOQWBHaxz6l0Biaa0qJds4z6l6Ao5MxICsn9sGCa2GtChjbYEHrdqv0VEnxM4tWveiazCaH5j4ria4/640?wx_fmt=png&from=appmsg)

# 用稳定标识连接相邻层

设备名会变，界面别名也可能重复。图旁边应保留一张映射表：业务或数据库对象、文件与挂载点、虚拟磁盘、主机设备、LVM 逻辑卷、多路径 WWID、阵列卷以及后端池分别是什么。

Red Hat 文档显示，DM Multipath 会把多个底层路径组织成一个设备，multipath -ll 可以同时看到 WWID、路径组、H:C:T:L 和设备节点。LVM 又会在物理卷之上形成卷组与逻辑卷。只写 /dev/sdb 或“生产卷”，无法稳定连接这些层。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdVg00HHttZicRbHdntjOiaTCUjxCuFjsCOQyI53kIwVJC42I6f3nx5cGLQYtg0broDxl6Ac4JBn5nKVnx4IlrNuvFoqYgprEIwM8/640?wx_fmt=png&from=appmsg)

# 把“完成”画成检查点

写请求尤其不能只画箭头。write() 返回、文件系统刷新、设备确认、阵列缓存受保护、远端副本完成和备份可恢复，是不同检查点。Linux 手册也明确说明，write() 成功并不保证数据已经提交到持久介质；需要按要求核对 fsync() 等语义。

图中应标明业务究竟等待到哪一点，后续保护是同步还是异步。否则两支团队都说“写成功”，承诺的却不是同一件事。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdX1B3lje5dBISsBJrhPEAMAwUL3g64NsZzs5Tiagqp7kVaBnzIHtPCoqq2oQfN5xTEjaZOfChZGJJJuSibicVuicjKLAgEkU3YnAO8/640?wx_fmt=png&from=appmsg)

# 在可能等待的地方标时间戳和队列

Linux blk-mq 包含软件暂存队列和硬件派发队列；设备资源不足时，请求可能继续等待。块设备统计还能提供完成量、在途请求和 I/O 时间，但这类聚合值不能直接代表某一次提交。

我会在图上标出应用 Span、文件系统同步点、主机队列、多路径切换、网络重传、存储端口、控制器队列和后台任务，并要求各系统时钟对齐。健康期与异常期放在同一时间轴上，才能判断等待从哪一层开始增加。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdXluIas6TObovu2TACG9qm34XuQ7ibp8YYWp8sEQb9oCPhzsFpELZxgcF4g49GPFmzLcufzCq1TkLIQma2GP6sF9dk0PySQwkK0/640?wx_fmt=png&from=appmsg)

# 复制、备份和控制面要画成旁路

主图描述前台请求。同步复制如果属于确认条件，应接入完成检查点；异步复制、快照、备份和分层迁移则从对应对象分叉，并标出延迟与资源竞争。创建卷、修改策略、故障切换命令属于控制面，不要混成前台数据箭头。

这样画的好处是，团队能看出哪些步骤决定本次响应，哪些步骤决定之后的恢复能力，也能看出后台保护为何会影响前台队列。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdXHuoOO4k5icwrqYmA2cataQjWy9ysGmWwqrsLwEj8PqUWcNqY3evdOyT4vc4MEclo0jxrU6JWAEqNQU5ml0yoL5poX6vqEsKr4/640?wx_fmt=png&from=appmsg)

# 最后补上故障域和责任人

路径连通不等于风险已经清楚。要继续标出哪些对象共享主机、交换机、控制器、资源池、电源和站点；再给每一层写上负责提供配置、指标和故障证据的团队。

验证时从健康状态开始，随后执行授权范围内的路径故障、控制器切换、队列压力和恢复演练。每次核对对象映射是否仍正确、完成语义是否改变、P99 从哪里上升、告警是否到达责任人。图与现网不一致时，先修图或修配置，不能继续把它当作排障依据。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdUxjTwduHKuEbpuDkQWZ8NN7v4PHSvYjMGtvJPMjiadE5dMc3saIIicdUNiabzIwGIaG6xnqJAd6SHwqicCbtGMtz2lQtMve7I5oiac/640?wx_fmt=png&from=appmsg)

我的验收标准是：任意一条线都能由配置、命令、日志或监控证明；任意一个“完成”都有明确承诺；任意一个共享故障域都有人负责。这样的图才是运行资产，而不是会议结束后失效的装饰。
