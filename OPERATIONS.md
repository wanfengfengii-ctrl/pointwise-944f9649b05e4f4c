# 日结作业：现有业务与发布接口

## 当前可运行项目
Python 3.11+ 标准库及 SQLite；目标运行机为已有 Python 的 macOS。无需第三方依赖、解释器打包、签名或公证。核心业务已经可用，本轮不增加数据字段、计算规则或查询页面。

运行清单中的 verify 执行 python3 checks.py normal，demo 执行 python3 manual.py demo。两者都核对或展示真实业务，不需要创建持久文件。python3 manual.py fixture INPUT.json 可生成完整春季样本。任意持久库的手动调用为：
python3 manual.py run DB INPUT JOB BINDING DAY START END SCALE_PPM

INPUT 是 UTF-8 JSON 数组，每行 [id,rev,at,station,value,deleted]。时间为 UTC 整数秒，值为整数原始计量单位；输入可含历史修订。pipeline.calculate 先按 id 取最高修订，再按 [START,END) 筛选未删除记录，按站点汇总。结果 stations 每行 [station,count,numerator,denominator]，金额为原始和乘 SCALE_PPM/1000000 的最简分数，空窗口输出空 stations。示例和完整校验逻辑分别在 samples.py、pipeline.py。

Store.publish 接收 JOB、BINDING、原始行和计算参数；结果与请求摘要在同一 SQLite 事务提交。同 JOB 同完整请求返回原回执，异请求报 JOB_CONFLICT，失败不留新结果。Store.read 返回按 JOB 排序的完整回执数组。不得更改这个业务模块、已有样本或 checks.py 中的断言；可以新增发布包装与验证文件。

## 发布入口约定
新增 ops.py，以下为从仓库调用的 argv；安装包也接受相同的子命令。成功向 stdout 输出一个 JSON 值；失败非零退出，并给出可读原因。

- python3 ops.py build CONFIG OUT
- python3 ops.py install ROOT PACKAGE EXPECTED NOW REQUEST
- python3 ops.py tick ROOT INPUT NOW LIMIT
- python3 ops.py status ROOT
- python3 ops.py read ROOT
- python3 ops.py agent ROOT INPUT OUT

build 将当前发布实现、pipeline.py 与 CONFIG 制成一个可由 python3 执行的归档 OUT。CONFIG 形如 release-r1.json；release 为非空显示名，timezone 仅取 UTC 或 Europe/Berlin，start_day 为 ISO 日期，scale_ppm 为正整数。只处理一个站点计划，首次安装固定 timezone、start_day，后续包必须与其相同；只有校准参数与包内容可以变化。相同源文件内容及配置重复构建须字节相同，不受文件时间和构建目录影响。归档含可供安装前核对的内容清单，坏成员、缺成员或内容摘要不符均应拒绝。无需抵抗拥有 ROOT 写权限的人伪造完整新包。

ROOT 是独立运行目录，不是源码目录；各路径可含空格。PACKAGE 是 build 产出的归档。初始代次为0，首装成功为1。install 的 EXPECTED 为预期当前代次，NOW 为 UTC 整数秒，REQUEST 为非空发布请求号。请求绑定包内容摘要、EXPECTED 和 NOW，不绑定包所在路径。相同请求重放返回原发布回执，不增加代次；异内容拒绝。不同请求只能在预期代次匹配时切换，完整切换增加一个代次；首装采用该包覆盖 start_day 起的全部待补日期。后续成功切换以 NOW 为界，仅严格晚于 NOW 到期的日期受新包影响，等于 NOW 的日期仍归旧包。同一秒的多次成功切换，未来日期归该秒最后一个成功代次。不能让发布时间早于 ROOT 已观测的最大 NOW；这种请求拒绝且不改线上。安装返回 {"generation":整数,"package_sha256":字符串}。

 tick 的 NOW 可取 UTC 整数秒，或 clock 表示运行时读取系统时间；LIMIT 为1至32。一次调用先取 max(NOW,已观测时刻)，按日期顺序接纳至多 LIMIT 个已到期但未接纳的日期，再处理至多 LIMIT 个未完成日结。已有未完成日结即使没有新到期日期也要续跑。单个 ROOT 最多积压400天，历史切换不超过8次；有限输入、后续 tick 足够时应完成所有到期日结。这里只做每日计划，不支持计划编辑或通用 cron 表达式。

日期 D 的窗口为站点时区 D 零点至 D+1 零点；到期时刻为 D+1 当地02:30，按题面处理无效或重叠时刻。时区使用标准库 zoneinfo。可核对的边界：Berlin 的2026-03-28日结于2026-03-29T01:00:00Z到期；2026-10-24日结于2026-10-25T01:30:00Z到期。2026-03-29窗口长23小时，2026-10-25窗口长25小时。用春季样本，r1于2026-03-27T00:00:00Z首装、r2于2026-03-29T01:00:00Z切换，2026-03-30T00:30:00Z补跑到期日期，则03-27为north的4/1、03-28为south的6/1，均绑定r1；03-29为north的15/2及south的75/2，绑定r2。

输入生产者以原子替换 INPUT 的方式发布新快照，不就地改写已打开文件。一次接纳读取一个完整快照；同次新接纳的日期共用这些字节。先按业务规则验证完整输入，非法输入不产生接纳记录、不推进日期。接纳后原路径可消失或换成其他内容，已接纳日结照常恢复；本次没有新接纳日期时，不依赖 INPUT 仍然存在。重试使用原字节、原窗口、原校准参数。每个日结的 JOB 就是日期字符串，BINDING 为 package_sha256 + ":" + input_sha256，其中输入摘要针对冻结的原始字节计算；通过原 Store.publish 入账，read 原样输出 Store.read 的回执数组。调度元数据不得伪造业务回执。

 tick 输出 {"accepted":[本次新接纳日期],"completed":[本次确认完成日期]}，两个数组按日期排序。其他调用可能已经完成同一日期，确认完成可以重报，但业务库只能有一份回执。不同日期不要求按完成顺序可见。任务计算不得占用安装需要的全局锁或写事务；不要求并行计算不同日期。最多两个 tick 与一个 install 交错，不能因旧进程稍后恢复而改变已冻结绑定。包落盘、接纳落盘、业务提交与调度完成落盘之间均可能终止进程；下一次已安装入口或重放 install 必须能恢复。验证应覆盖真实进程终止以及提交成功但调用者没得到结果，不以人工改数据库模拟恢复成功。

status 输出 {"generation":整数,"clock":整数,"next_day":日期,"jobs":[...]}，next_day 为最早尚未接纳日期。每项有 day、release_generation、package_sha256、input_sha256、state；state 为 pending 或 complete，按 day 排序。业务已提交而调度尚未确认时可以暂为 pending，后续 tick 必须查证并完成，不能另用当前包覆盖它。无需实现删除历史包、输入回收、数据库格式迁移或源数据持续采集。

agent 生成 XML plist 到 OUT，使用绝对 ProgramArguments、RunAtLoad 和600秒 StartInterval，调用已安装入口的 tick，NOW=clock、LIMIT=32；不能通过 shell 启动。操作说明给出当前用户加载和卸载该 plist 的命令。常规安装和补跑无需注册系统服务；自启动验收在目标运行机加载生成文件，不能引用仓库路径。运行目录及发布包应能从空格路径运行；移走整个源码目录后，使用安装包仍可 status、read、tick 和继续发布。包与发布元数据之间未完成的切换可由重放恢复，但 install 成功回执发出后，已安装入口必须指向该完整代次。

## 已有材料的用途
release-r1.json 与 release-r2.json 只改变校准系数。它们不是两个计算引擎，也不涉及业务迁移。manual.py 提供直接核账入口；最终运行清单继续保留业务回归，并让 verify 核对安装运行的业务结果，demo 展示安装后实际产生的日结。发布验证可使用隔离临时目录，不自动向用户注册 LaunchAgent。自启动的加载、卸载与实际运行证据在操作说明中单列。
