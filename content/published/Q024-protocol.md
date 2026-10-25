# Q024：小 IO、大 IO、顺序与随机访问如何影响协议表现？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/y_hdDi9OA7Xs5r1iaxWRpg
> 发表时间：
> 迁移时间：2026-10-25

假设一次性能复盘：同一套存储、同一条网络，备份任务能够持续传输大文件，数据库业务的带宽却不高，查询偶尔还是很慢。有人据此判断，数据库使用的协议性能不行。

这个结论下得太早。备份和数据库虽然都在“读写数据”，提交给存储的工作并不相同。前者可能连续读取大块数据，后者可能从一个大文件的不同位置读取小块数据。协议处理的请求数量、排队方式和网络往返随之改变。

小 IO、大 IO、顺序和随机描述的是两个独立维度。它们先改变请求数量与访问局部性，再通过客户端、协议、网络、控制器和介质表现为不同的 IOPS、吞吐与时延。评价协议表现，必须先说明在哪一层观察请求。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdXpdV8fX9UlfJhvApR9JQ1FvCdpqMEBica8JicHVib70atyTrQX9DDTDLad1PISwgnqmvxkuC4UiatwbibJnUvqzwt3ZHDgh90HcXn4/640?wx_fmt=png&from=appmsg)

# 同样处理 100 GiB，存储收到的工作量并不相同

先忽略缓存、合并和协议开销，只做一个数量级比较：100 GiB 数据若按 1 MiB 请求传输，需要约 10 万次请求；若按 4 KiB 请求传输，则需要约 2621 万次。两者搬运的数据量相同，完成请求的次数相差 256 倍。

每次请求都不只有有效数据。它还可能经历系统调用、文件系统或客户端处理、请求分配、队列等待、协议封装、网络收发、服务端解析和完成通知。请求越小，这些固定工作的占比通常越高。因此，小 IO 负载可能带宽不高，却先耗尽 IOPS、CPU、队列或协议处理能力。

大 IO 更容易提高吞吐，但单个请求占用链路和后端资源的时间也更长。当大请求与低时延的小请求共享队列时，还可能放大后者的等待。不能仅凭“大块传输效率高”，推导出它适合所有业务。

这里还要区分小 IO 与小文件。数据库可以在一个数 TB 的数据文件中产生 8 KiB 随机读取；一个 8 KiB 文件则可能在读取内容前先触发路径查找、权限检查、属性查询和打开操作。两者的数据量接近，协议工作却不是一回事。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdVicwVjwTArsKT2Tpic6YTiaY2AFekkWnSwhpIegzONwutPpMXDfEyRRX2dBocpO9spAQ2RibFicI1GeGfHEp968ZQibiaBRBTB3tKCD4/640?wx_fmt=png&from=appmsg)

# 顺序与随机，说的是相邻请求访问哪里

顺序访问是连续请求落在相邻的文件偏移或逻辑块地址；随机访问则不断跳到分散位置。它描述的是地址关系，不代表请求必须按提交顺序完成，也不等于“小 IO 就是随机、大 IO就是顺序”。

四种组合都可能存在：日志扫描可能是小块顺序读，数据库页读取可能是小块随机读，备份常见大块顺序读写，分析程序也可能从不同位置读取较大的数据块。

顺序访问更容易触发预读，也给相邻请求合并留下机会。Linux 块层可以把相邻扇区的请求合并，减少需要单独处理的请求数；Linux 页缓存的预读则可能在应用明确请求前，把后续页面读入缓存。

随机访问缺少这种局部性。对 HDD，它还会放大寻道和旋转等待；对 SSD，机械寻道消失了，但请求处理、闪存映射、垃圾回收、队列竞争和尾延迟仍然存在。全闪只能缩短部分路径，不能消除大量小请求带来的软件与协议成本。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdWPkhCwpYO7hYsExKxtmLOGLbTCtuQsmv4zGyf4pDM95BMxRujsxfLlwdpCaeT94qmWQX82ztDatPaQJ9SGWlsKBtJVG2H6xW0/640?wx_fmt=png&from=appmsg)

# 应用看到的顺序，到了后端可能已经改变

这是分析协议性能时最容易漏掉的一层。应用的一次read()或write()，未必对应一个网络请求，也未必对应一个设备请求。页缓存可能直接返回读取；客户端可能拆分或合并数据；块层也可能合并相邻请求并重新调度。

多客户端会让变化更明显。两台服务器各自顺序读取不同文件，从各自视角看都是顺序流；请求汇聚到共享服务端后，地址可能交错。阵列再经过缓存、条带化或数据布局，最终落到介质上的顺序性还会继续变化。

因此，“业务是顺序读”必须带上观察位置：是应用生成的文件偏移、客户端发出的协议请求、存储端看到的逻辑地址，还是介质实际执行的操作。不同层的结论可以同时成立，却不能互相替代。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdUa6ne9EphGpZFHmT5D6iaVcUibIl0xl1iaRA5c9ic2QoMKJppibC1NJicpUnKMUrFKzgX6q3I0icN6LmZ1kiaCcuV2smfh1HiaqqEztHxE/640?wx_fmt=png&from=appmsg)

# 请求形态怎样改变协议表现

文件协议处理的是文件和目录语义。NFS、SMB 访问小文件时，数据读取之外还可能出现查找、属性、权限、打开关闭与锁操作。客户端缓存命中时，有些操作不会到达服务端；缓存失效或多客户端协同时，元数据往返会变得突出。此时增加链路带宽，对打开文件的 P99 未必有明显帮助。

块协议把逻辑块设备交给主机，文件系统和缓存主要位于主机侧。iSCSI、FC 或 NVMe-oF 看到的是经过上层转换后的块请求。小块随机负载更依赖单请求时延、队列与并发；大块顺序负载更容易逼近链路或控制器吞吐上限。但传输协议名称本身，不能决定文件布局、缓存命中和业务完成条件。

对象接口的单位又不同。一次 API 请求可能读取整个对象或指定范围，还包含鉴权、元数据和 HTTP 处理。把块设备上的 4 KiB 随机写结果直接套到对象接口，同样没有可比性。

所以，不能问“哪种协议处理随机 IO 最快”，而应问：业务语义经过客户端后，服务端实际收到多少数据请求和元数据请求；每类请求多大、并发多少、需要几次往返，以及业务等待到哪个确认点。

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdW6Ue1OPlBrC14XpTPTldQicL1ibhAQJxRfO0Q3Vc70Rkbl6eoTjGsUUvjZuFGoicGTbYyvqoKoJ5CXFtU518oCrbVVicc2icdJYCq0/640?wx_fmt=png&from=appmsg)

# 怎样把四种访问形态测清楚

测试时先固定读写比例、并发、完成语义、数据集和缓存条件，再分别比较小块顺序、小块随机、大块顺序和大块随机。fio可以生成这些合成负载，但bs、rw和iodepth只是测试意图；缓存、I/O 引擎和操作系统限制可能让设备实际看到的请求发生变化，需要核对实际深度与主机、协议和存储端统计。

结果至少同时记录吞吐、IOPS、平均时延、P99/P99.9、实际请求大小分布和队列深度。文件业务还要记录打开、属性与目录操作；网络存储要检查客户端重传、网络包率和服务端请求分类。

![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdX9GoPEueqSkrJicgounx0vthMa6BCTRhictmVuYA2zbib8SYLhfyr62o6BM8g5v1EAjTLZeaAaiblCwicPj2sknCdia4WWtLLjHVndc/640?wx_fmt=png&from=appmsg)

回到开头的复盘：备份跑得快，只能证明大块顺序路径能够持续搬运数据；数据库偶发变慢，需要沿小块随机请求的时间线寻找等待。只有在相同负载、相同完成条件和相同观察层下，协议之间的性能比较才有意义。
