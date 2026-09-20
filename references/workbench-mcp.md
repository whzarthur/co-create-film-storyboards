# 电影工作台 MCP 接入

本文件只规定 `co-create-film-storyboards` 与 `film-workbench` MCP 的数据边界。创作判断、逐镜讨论和作者确认仍以主 `SKILL.md` 为准。

## 何时启用

- 用户给出或指向工作台项目，并要求基于已有剧本继续分镜：启用只读接入。
- 用户明确要求同步、写入或更新工作台：启用读写接入。
- 用户只提供独立剧本、只讨论分镜或只导出 HTML：不调用工作台 MCP。

调用本 Skill 不构成写入授权。只读请求不得调用写入工具；探索稿、待讨论镜头和未确认方案不得写入正式项目。

## 固定环节与定位

- `stage` 固定为 `storyboard`。
- 分镜是剧集级成果，必须确定真实的 `project_id` 和 `episode_id`。
- 标准输入与输出字段只以本次 `get_stage_contract` 返回值为准，不把当前 schema、模板或示例复制成长期规则。
- MCP 不负责运行 Skill、控制浏览器、执行工作流或替作者做确认。

项目或剧集不明确时，可先用 `list_projects` 查找。多个候选无法唯一确定时，向作者确认，不凭标题相似度猜测。上游剧本来源不满足当前契约时停止组装成果，并说明缺少的数据。

## 开始创作前

按以下顺序取得上下文：

1. 调用 `get_stage_contract({"stage":"storyboard"})`。
2. 完整阅读返回的 `contract_version`、`input_schema`、`output_schema`、`field_docs`、`template`、正反例、`dependency_capabilities` 与文件能力。
3. 调用 `read_stage_input`，传入确定的 `project_id`、`episode_id`、`stage:"storyboard"`；只在作者明确限定场次等范围时使用 `selectors`。
4. 检查 `data_status`、`warnings`、`context_hash`、标准输入和可复制的 dependency refs。向作者简要说明实际采用的剧本来源、revision 与本轮范围。

工作台输入是已登记事实，不是自动生成整套分镜的命令。仍需按主流程逐镜讨论，区分待讨论、修改中和已确认内容。

## 逐镜讨论与快照

- 逐镜协作期间在当前任务中维护讨论状态，不把每次对话都写成一个正式 revision。
- 工作台只接收完整快照，不接收 JSON Patch 或单镜补丁。
- 局部修改已有分镜时，先读取当前标准成果或环节输入，保留未在本轮修改的场景与镜头，只替换作者已确认的范围，再组装完整快照。
- 镜头 ID、场景 ID、顺序和依赖引用应保持稳定；只有实际新增、删除或重排时才改变。
- 候选成果只能引用本次确实采用的 `read_stage_input.dependencies`。不要把未使用的历史版本或资产写入依赖。

## 写入流程

仅在请求已有写入授权且约定范围内的镜头均已确认后执行：

1. 再次调用 `get_stage_contract`；每次生成待校验成果都重新发现契约。
2. 若上游数据可能已变化，再次调用 `read_stage_input`，用最新输入重建完整候选快照。
3. 严格依据实时 `output_schema`、模板和示例组装候选成果。`producer.skill_id` 使用本 Skill 的实际 ID `co-create-film-storyboards`；`skill_version` 只有存在真实版本时才填写，否则按当前契约允许的空值处理，不能虚构版本。
4. 不带文件时，将完整候选成果传给 `validate_stage_output`。带主分镜图或调度图时，先调用 `begin_stage_upload`，只在返回的一次性会话目录中写 `artifact.json` 与 `files/`，再用 `upload_session_id` 校验。
5. 校验失败时修正候选成果，不写正式项目。只有校验成功后，才把同一长生命周期 MCP 进程签发的 `validation_token` 传给 `write_stage_output`。
6. 写入成功后调用 `get_artifact`，核对服务端最终 `artifact_id`、revision、路径、hash、数据状态和警告。只有回读一致后才向作者报告同步成功。

文件上传只使用当前契约声明支持的类型。不得传 base64 大文件，不得直接写工作台正式项目目录，也不得复用其他进程或过期会话的校验令牌。

## 失败与变化处理

- 收到 `STALE_CONTRACT`：重新查询契约、重新读取输入并重建候选成果，不绕过校验。
- 上游剧本 revision 在讨论期间变化：先告知作者差异；未经确认，不自动把已确认镜头换绑到新剧本。
- 校验或写入失败：保留本地讨论结果和 HTML，不声称工作台已更新，报告具体错误和可恢复步骤。
- 用户撤回写入要求：停止在校验前或校验后均可；未调用 `write_stage_output` 就不产生正式成果。

## 完成标准

只读接入完成时，应能说明所用项目、剧集、剧本 revision、读取范围与警告。读写接入完成时，还必须取得写入回执并用 `get_artifact` 回读确认；最终向作者报告成果 ID、revision、hash 和未解决警告。
