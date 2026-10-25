# Q017：SMB 是什么，和 NFS 的主要差异是什么？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/XQ6iHVszJ1CRoTFZr_Sx5Q
> 发表时间：
> 迁移时间：2026-10-25

一个工程团队把素材目录共享出来：设计人员在 Windows 上修改图纸和文档，Linux 服务器上的渲染、转码和批处理程序再去读取。目录映射成功后，最初看起来没有区别：都能打开文件，也都能复制。真正的分歧常在协作发生后才出现。Windows 用户说文件“正在被占用”，Linux 任务却已经开始读取旧内容；设计人员在共享盘里改了权限，服务账号突然无权写入；网络短暂闪断后，应用是重试、报错，还是继续拿着一个过期的文件状态？这不是 NAS 容量不够，是文件协议在替业务协调身份、文件状态和缓存。![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdXp6SSz9eb8yiaKG9GQpolotibY0cBFSlicE68Bb2OCBGfvRMy7lvRddrpIotxPc4E88fr4tvjMBtPH2XWnFswPKMonsB8hYRH92k/640?wx_fmt=png&from=appmsg)

# 核心结论

SMB 和 NFS 都是网络文件访问协议：服务端提供文件树，客户端通过网络进行目录遍历、打开、读写、改名和权限检查。它们的主要差异不在客户端归属，也不在谁天然更快；差异在于它们与客户端生态、身份与权限、文件锁、缓存和故障恢复如何配合。因此，Windows、Active Directory 与 Windows ACL 为主的协作文件业务，通常应先验证 SMB；Linux/Unix 为主、身份体系可以统一的共享目录，通常应先验证 NFS。混合环境不能只因为两端“都能挂载”，就默认把同一后端目录同时交给两种协议使用。

# SMB 交付的不是一个盘符

SMB 的典型使用体验是访问 `\\\文件服务器\\\共享名`，随后把共享映射为盘符。但盘符只是入口。一次访问背后还包括用户认证、会话建立、连接到特定共享、打开文件并取得文件句柄；后续的读写、改名和锁都围绕这个状态继续进行。这也是为什么“文件被占用”不是一个简单的客户端提示。SMB2 定义了字节范围锁，锁与具体文件句柄关联；客户端可请求读、写或句柄缓存租约，服务端需要在其他客户端的操作可能改变可见性时协调这些状态。![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdUGNgeicrq39SVf5Fa5oDuibOJIXyNFXICYYZGzibuLSDnRYNtdmz8aL9usiceYPbwoUC6NJfzhr60ow1zAiaBTqNhdUfVFkKqxlANs/640?wx_fmt=png&from=appmsg)对业务来说，SMB 的价值在于 Windows 客户端、域身份、共享权限和常见桌面文件操作通常能在同一套语义下被设计、配置和排查。具体是否适合，仍取决于服务端实现及应用对锁、改名、临时文件和断线重连的实际用法。

# NFS 也不是“没有状态的 Linux 目录”

NFS 在 Linux/Unix 业务中常被挂载到一个路径下，因而很容易被误当成本地文件系统的延伸。但 NFSv4.x 同样要处理打开、字节范围锁、客户端身份和缓存状态。协议规范专门定义了状态管理、锁、客户端缓存与回调等内容；Linux 客户端文档也说明，NFSv4 的打开和锁状态与客户端标识关联，若标识在重启后随意变化，状态恢复就可能失去可靠前提。所以，NFS 适合 Linux/Unix 业务，并不意味着它可以回避并发写入或故障恢复设计。它只是让 Linux/Unix 文件访问语义成为系统的主要假设。多个客户端修改同一文件时，锁与应用协同仍要明确；网络或服务端短暂中断后，应用也必须能处理超时、重试和状态恢复。![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdVBGMKdECSXTMSuCKQIoJD0icBqjF9ErYpJs6kEsxurgm6S2McnUQ9vpxIicBnIuveicBDhibv33636tib5Qk02eUCYIibZVmLdOcNCM/640?wx_fmt=png&from=appmsg)

# 真正难的不是协议，而是身份和权限

SMB 环境里，身份通常围绕 Windows 域账户、组和 ACL 管理；NFS 环境则常见 UID/GID，也可以采用 Kerberos 和更完整的 ACL 能力。不要把这种差异理解成“SMB 有权限、NFS 没权限”——两者都可以做访问控制；难点在于，同一个人或服务账号能否在每一台客户端、每一个身份源和每一项权限判断中被识别成同一个主体。在 Windows 与非 Windows 的混合环境中，需要规划 AD、LDAP 或映射文件，并选择 AUTH_SYS 或 Kerberos 等认证方式。这解释了很多“文件明明存在，却只有某台机器没有权限”的问题：通常不是协议随机失效，而是用户、组、服务账号或 ACL 的映射并没有形成同一份事实来源。![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdWNadckBAGibJ9pu0iaRVnx40jzczNDtHeWvtKRIhDeTajPqRnM9YKwLdsembfZtMcug4W1tLeWzMFGJOF79f28djFcxFxI5JpP4/640?wx_fmt=png&from=appmsg)

# 缓存与锁都存在，不能假设“另一端立刻看到”

SMB 的租约与 NFS 的缓存、委托机制，目的都是减少每次读写都跨网络往返的成本。性能因此更好，但可见性与冲突处理就不能只靠直觉。两种协议都会在特定版本和实现下协调缓存与锁；它们都不等于“任何客户端一写完，所有客户端在任意时刻都自动看到完整且可修改的最新状态”。生产上应把问题说得更精确：谁写？谁读？是否会同时改同一文件？应用在何时关闭、改名或发布文件？如果流程是“先写临时文件，校验完成后原子改名发布”，读取方又只消费发布后的名称，冲突面会比多人直接覆盖同一文件小得多。具体怎么写、怎么改名、什么时候让读者看到新版本，仍要由应用和发布流程来定。

# 选择前，先填这张表

![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdUNTmpC0IzomcePDH4tVTYbcFtlObEC2lLUTo8iayyGDI4lpianTWfjD7K8ia3HcWeriaGEXc4WDJdJFvZlXH0hckicic606GfbN0EAE/640?wx_fmt=png&from=appmsg)要确认的问题| 更偏向 SMB 的信号| 更偏向 NFS 的信号| 仍需验证的事  
---|---|---|---  
主要客户端与工具链| Windows 桌面、Office/CAD、域账户协作| Linux/Unix 主机、批处理与工程流水线| 是否存在跨平台客户端与第三方实现  
身份与权限| 已有 AD、组策略、Windows ACL 管理流程| 已统一 UID/GID，或已规划 Kerberos/目录服务| 服务账号、组成员关系和权限继承是否一致  
文件协作方式| 依赖 Windows 应用的文件占用、改名和共享行为| 多主机读共享目录，且写入责任清晰| 是否多人并发改同一文件；锁冲突如何处理  
缓存与发布| 客户端需要按 SMB 语义处理文件状态| 应用已按 NFS 挂载与刷新行为设计| 写完后何时对读者可见；是否采用临时文件再改名  
故障恢复| Windows 客户端、会话和映射盘的恢复流程明确| Linux 挂载、超时和重试策略明确| 网络闪断、服务端重启后应用怎样恢复  
这张表的作用是把“我们想共享一个目录”改写为可验证的问题：身份是否一致、协作语义是否一致、故障时谁来恢复。

# 上线前不要只测试复制速度

至少做五类测试：一是用真实用户与服务账号分别创建、修改、删除和改名；二是模拟两台客户端同时打开或修改同一文件；三是观察大量小文件和深层目录下的元数据行为；四是演练网络闪断、服务端重启与客户端重启；五是从备份或快照恢复后，检查内容、目录、权限和业务处理状态是否一起恢复。数据库日志、虚拟机磁盘等对持续同步写、时延和故障语义有严格要求的负载，不应因为“共享文件夹能挂上”就默认部署在 SMB 或 NFS 上。先确认应用、虚拟化平台、文件服务实现的支持边界，再用 PoC 复现真实负载与故障条件。

# 适用边界

SMB 与 NFS 的选择不能简化成操作系统二选一或一次跑分。Linux 可以访问 SMB，Windows Server 也可以提供或访问 NFS；但“能够互通”不等于身份、ACL、锁、缓存和恢复语义已经统一。当一个目录要被不同系统共同使用时，先选定谁是主要客户端、谁是身份权威、谁负责写入，以及故障后如何恢复。协议的名称只是起点；最终决定架构的，是这些选择能不能在故障和增长压力下被业务验证。
