# Q022：文件锁、缓存一致性与协议选择有什么关系？

> 来源：存储罗盘（微信公众号）  
> 原文链接：https://mp.weixin.qq.com/s/Iw9Ros6h_6ZwJSgvvge_ew
> 发表时间：
> 迁移时间：2026-10-25

两个部门的内容管理团队分别在不同主机上编辑同一份设计稿目录。某天合并时发现一周的工作被覆盖。运维查了存储日志，文件都在，权限也没问题。团队怀疑"存储有 bug"，但实际上两台主机从来没有互相协调过谁先写、谁后写——两边的应用各自打开、各自保存，存储只是忠实地执行了最后一次写入。文件锁和缓存一致性是协议提供的机制，不是自动生效的保证。协议选择决定了有哪些机制可用、机制的行为边界是什么；但"多个写入者不冲突"这件事，始终需要应用正确地获取锁、遵循缓存可见性规则。三句话概括：![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdV7gEQibBqIHLSmZviaw7AqiaQnVHfWZtc0JxrYOey54ITZEC8x0ia7yRo7r8fxl33JAQofZHUI5cyWxSxw1RYa67CmgRqQ7PHiaVXE/640?wx_fmt=png&from=appmsg)

  * 多写者并发编辑同一文件 → 必须用显式锁，协议选择决定锁的类型和恢复语义
  * 读多写少的共享文件树 → 缓存一致性模型决定"何时能看到对方的修改"，协议选择决定模型
  * 跨平台混合访问 → 锁和缓存在 NFS 和 SMB 之间的语义不对等，身份映射影响锁归属

# 文件锁管的是什么

锁有不同的粒度和强度。字节范围锁锁定文件中的一段，其他端可以读或写未锁区域。NFSv4 的 LOCK/LOCKU 操作和 SMB 的 byte-range lock 都属于这一类。字节范围锁允许两个进程同时写同一文件的不同区域，前提是它们各自锁定了不重叠的区间。共享访问模式控制文件能否被同时打开用于读或写。SMB 的 share access 分读、写、删除三种共享位，组合后可以表达"允许别人读但不允许写"或"独占打开"等策略。NFSv4 的 open share reservation 也有类似能力，但使用方式不同——它在 OPEN 操作中声明 share_access 和 share_deny，由服务端检查是否与已有打开冲突。建议锁和强制锁的区别在于执行力度。建议锁只对主动检查锁的程序有效——如果应用不调用加锁操作，锁不会阻止它写入。强制锁在每次 I/O 时由系统或协议层拦截，不需要应用主动配合。大多数网络文件协议的锁是建议性的，这解释了开篇的覆盖问题：两边应用都没有请求锁，存储协议层面没有阻止最后一次写入覆盖前一次。实际部署中，应用是否获取锁、获取什么类型的锁，决定了协议的锁能力是否真的在生效。一个不调用锁操作的协作工具，换到任何协议上都不会自动获得冲突保护。![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdWcKvPMu15ZTuMmqRCVeMHdoYQ9bmX9rgYBDx0bf6XQ0pjypubibB8oIMKbj7R0OGtQKCEBxJvAMiarUZ6hC15m4BYEbiaRS7XmVI/640?wx_fmt=png&from=appmsg)

# 缓存一致性：同一路径不等于同一时刻同一内容

网络文件协议都允许客户端缓存文件数据和元数据。不同协议的区别在于"缓存何时与服务端重新对齐"——这被称为缓存一致性模型。NFS 使用 close-to-open 模型。客户端关闭文件时把修改写回服务端，下次打开时检查文件是否被他人改过。两次打开之间的窗口里，客户端缓存可能过期，但协议不主动通知。这意味着：客户端 A 写入并关闭文件后，客户端 B 打开时能看到新内容；但如果 A 写入后没有关闭，B 打开后读到的可能是旧版本。![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdVqkTwflv3MXCvdg4y936YK37iaRCEVOb6WzThuR6ydVbJPj7R2wGDenFVFODHaMfDvQTYL8qDPlqC44FzeX5wZDTrfYyK1SHUY/640?wx_fmt=png&from=appmsg)SMB 使用 oplock（opportunistic lock）和 lease 机制。客户端持有租约时可以本地缓存数据；当另一个客户端请求冲突访问时，服务端先发租约中断，通知持有方刷新或降级缓存再让新写入者进入。租约中断是推送式的，延迟比 NFS 的被动检查更低，但依赖连接可达——网络分区时租约可能无法及时中断，持有方在不知情的情况下继续写缓存。![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdVBNhnql0U6xALXQdntN17TSVnu1icHQPFdGbqaPa8TV99hOVTVAmicZ042RWvwelZPhBhNh5ic0URUy6iaPciciab8OCkAYCdxZ7Wico/640?wx_fmt=png&from=appmsg)两种模型回答的是同一个问题：客户端何时能看到其他客户端的修改。它们都不保证修改实时同步。close-to-open 在打开边界对齐；oplock/lease 在租约中断时对齐。理解模型差异后，应用可以据此设计发布和切换策略——比如配置发布时显式关闭文件触发写回，而不是覆盖后期待所有节点立刻看到新版本。

#  协议选择如何影响锁和缓存行为

NFSv4 的锁是租约制。客户端必须定期向服务端续租，租约过期后服务端可以回收锁并分配给其他客户端。网络中断恢复后，锁状态需要客户端发起恢复流程；恢复有时间窗口（由租约期决定），超时后锁不再属于原持有者。这意味着短暂的网络抖动可能导致锁丢失，应用需要处理"锁已经不在自己手里"的情况。![](https://mmbiz.qpic.cn/sz_mmbiz_png/LF0nGncJCdWOE7Lzw9wtZ1cjey2iak7aeknOFNiaic4kuaYAIt2jvqCGhO4Y1rc3hXsiaIXKibGfOISuXh94Ag3PtLibgQweN3rvSOibu5v5ianrnMA/640?wx_fmt=png&from=appmsg)SMB 的 oplock/lease 是推送制。服务端主动通知缓存失效，延迟更低，但依赖连接可达。SMB 3.x 引入了持久会话（durable handle）和租约恢复，允许客户端在短暂断线后恢复会话和锁状态，但要求客户端和服务端都支持相应能力。跨协议访问同一卷时，问题更复杂。NFS 客户端持有的锁，SMB 客户端不一定能看到；反之亦然。多协议 NAS 网关通常在内部做锁映射，把 NFS 的 byte-range lock 和 SMB 的 byte-range lock 关联起来，但映射的完整性取决于产品实现。有些产品能做到跨协议锁互斥，有些只做到"同协议内正确，跨协议尽力而为"。这一点必须在 PoC 中验证，不能假设多协议等于锁互通。身份映射也影响锁归属。NFS 用 UID/GID 标识锁的持有者，SMB 用 SID。如果两个协议的客户端被映射到不同的服务端身份，锁的归属判断可能出错——一个客户端的锁可能被另一个协议的客户端"冒领"或无法正确释放。跨协议访问要确保身份映射在服务端一致，且在 PoC 中覆盖锁的获取、释放和恢复路径。![](https://mmbiz.qpic.cn/mmbiz_png/LF0nGncJCdWWuiaic5y6eGOMY7H2icicfUxiaBqcg0bJvOAvTIH9EBOZ7C7vxiaMgJjd40KtUF1y2V8F7ibibpFCsjiclxyu47YEzkflIVeIsZpJ3qzo/640?wx_fmt=png&from=appmsg)

# 哪些业务场景要优先考虑锁和缓存一致性

多写者编辑同一文件是锁和缓存一致性最关键的场景。内容管理系统、协作工具、多人编辑同一设计稿目录，都属于这一类。应用必须用显式锁协调写入顺序，POC 要测锁竞争（两个客户端同时请求冲突锁时谁等待、谁获得）、锁释放（写入完成后锁是否正确释放）和锁恢复（持有锁的客户端崩溃后，其他客户端要等多久才能获得锁）。配置文件共享发布是读多写少的典型。应用集群从共享目录读取配置文件，运维覆盖新版本后，所有节点何时看到新内容取决于缓存一致性模型。NFS 的 close-to-open 模型要求写入端关闭文件触发写回，读取端下次打开时检查更新；SMB 的 lease 模型在租约有效期内可能缓存旧版本。发布策略要根据模型设计：显式关闭写入端、通知读取端重新打开、或用原子重命名（rename 到目标路径）让新版本在协议层面立即可见。数据库文件放在网络文件协议上要格外谨慎。数据库通常用 `flock` 或 `fcntl` 做文件级协调，但网络协议的锁语义和本地文件系统不完全等价。`flock` 在 NFS 上可能不生效或行为不同；`fcntl` 的字节范围锁在 NFSv4 中有对应，但锁的持久性和恢复语义与本地文件系统有差异。数据库厂商通常在支持矩阵中明确列出是否支持 NFS 或 SMB 后端，以及需要什么挂载参数——这应作为部署的硬性前提，不是可选验证。跨平台混合访问指 Linux 用 NFS、Windows 用 SMB 访问同一卷的场景。锁和缓存语义在两个协议之间不对等：NFS 的 close-to-open 和 SMB 的 lease 是两套独立的缓存一致性机制，各自维护各自的客户端缓存；锁的跨协议可见性取决于网关实现。写入冲突时行为可能不可预测——两个协议的客户端可能各自认为没有冲突，同时在同一区域写入。这类场景要么避免多写者跨协议访问同一文件，要么在 PoC 中验证网关的锁映射是否足够可靠。
