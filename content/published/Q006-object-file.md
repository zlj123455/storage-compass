# Q006：块、文件、对象，别先问谁更快

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/MTMubgjKPpJe3P1rKiO9GQ
> 发表时间：
> 迁移时间：2026-10-25

新项目启动会，存储选型是议程的第三项。有人带了一张对比表：块、文件、对象，三列参数，从 IOPS 到时延到单价，排得整整齐齐。"先别比参数。"架构师把表翻过去，"先告诉我，每种数据，你希望谁来管。"![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdVznKIV5hMWcV57au1sda2AHSQd9H9w4E34ibZudTF6PFvH7xic2eCLLOpcicicU86iayNicvuucDwqDz5OicNBlycXezuttIRLHxJPa8/640?wx_fmt=png&from=appmsg)

# 不是三种容量套餐，而是三份责任合同

桌上摆着三个业务系统的需求：数据库要高性能读写，设计团队要共享素材目录，日志归档要长期保存且可追溯。三个团队的数据量差不多，但"谁来管数据"的答案完全不同。数据库团队说：我们自己管，给我们一块裸空间就行。设计团队说：我们不想管文件系统，只要大家能看到同一套目录和权限。运维团队说：日志我们不想管目录，按时间保存、到期删除就行。存储接口决定的，不只是数据怎么进来，更是"谁负责把数据管好"。把它们都塞进同一个"大存储"，这些差别不会消失，只是被藏起来了——直到出问题的时候才暴露。

# 块：把一块可读写的空间交给主机

数据库团队拿到了他们要的块空间。像是一块"还没有整理好的硬盘空间"，不自带文件夹和文件名。![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdXUCf3yhBp7AQpVqa2bnxsWTff1Tgicfiaj4dJ21pxbibAMHntUpTFiaD06eFx66ibRQicZOMRuXHrXSaSWYQP3V6L20nzvVRic7zt7jw/640?wx_fmt=png&from=appmsg)上面的文件系统怎么建、数据库怎样写入、故障后怎样恢复，都由主机上的系统和应用去负责。正因如此，块接口常用于数据库或虚拟机这类已经知道如何管理自己数据的场景。但架构师在会上提了一个问题："两台服务器都能看到同一块空间，能像共用网盘一样一起写吗？"不能。谁有写入权、异常时怎样防止旧服务器继续写，必须先定义清楚。块接口给的是控制权，不是协作能力。一句话理解：块接口给你更多控制，也把更多管理责任留给你。

# 文件：交付一套大家共同遵守的目录规则

轮到设计团队。他们要的不是裸空间，而是一个"共同的文件柜"。![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdWwelCvAEMls47G6gvojIkbzQeepQkenWddllMWcH6pFiaO8ooLPrWsyic8VGwRLjVEfliaNtVyZDiaTeSwCh8AJEjrbsmQkV94yUE/640?wx_fmt=png&from=appmsg)目录、文件名、权限，以及多人同时访问文件时应遵守的规则，都是这项服务的一部分。设计团队不需要关心文件系统怎么建——他们关心的是：同一个文件能否被正确打开、修改、重命名；权限变更后是否马上按预期生效；网络短暂中断后，客户端会怎样恢复。架构师提醒："文件多，不等于文件接口一定合适。但只要业务强依赖共享目录和文件协作，文件语义就是不能跳过的要求。"一句话理解：文件接口替团队维护共同的目录秩序。

# 对象：把数据当作可管理的独立"件"

最后是运维团队的日志归档。他们不想挂载磁盘，也不想维护目录树——他们要的是把每份日志连同名标、版本和保留规则，作为一个独立对象来管理。![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdVyzFBAMiao94ssXPnfYicRhy5F9Q9YicAyMMgdaUlCEevAe6vfJ72TkxGXUt4ZBiba1EvqAUkXnANHiaicUtiannzkCtRKiaQ1yeDPxKE/640?wx_fmt=png&from=appmsg)对象接口不强调把数据"挂载成一块盘"。应用通过接口把一份数据连同它的名称、标签、版本和保留规则一起写入。备份副本、归档资料、图片视频、日志和大批量处理结果，常适合这种方式。但架构师敲了一个重点："对象不是更大的共享文件夹。"如果应用依赖在原文件上做小修改、多个客户端即时共享同一目录，或者依赖文件锁，就不能只把路径换成对象名称——必须确认应用是否真的适配。一句话理解：对象接口适合把数据按"独立的、可追踪的一件件资产"来管理。

# 选型会前，先把这四个问题问清

会开到这儿，那张对比表已经被翻过去了。架构师在白板上写了四个问题，让每个团队回去填。![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdWFbVtl0Jju5jy7ibT2IQGdwQnpwMSSTIYlJgn4lB114VDEmxulVmLmTPm7C0vc8O4gp1LraJedyhgxwIYrwAL1tyJowfeEe8mo/640?wx_fmt=png&from=appmsg)

  1. 业务是否依赖多人共享同一目录、文件名和权限？
  2. 如果交付的是块空间，谁负责文件系统、写入权和故障后的恢复？
  3. 如果按对象管理，覆盖、误删、版本和保留规则是否已经说清？
  4. 业务真正怕的是什么：慢、多人协作冲突、误删后找不回，还是故障后恢复不确定？

当这四个问题有答案后，再比较产品、协议和报价，讨论才会落在业务需要的地方。块、文件、对象没有谁天生更高级。它们只是把不同的责任，交给了不同的一方。
