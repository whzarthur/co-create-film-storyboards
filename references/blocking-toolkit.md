# 使用现成调度图工具包

作者提供的工具包已原样保存于 assets/scene-blocking-toolkit/：

- [原工具](../assets/scene-blocking-toolkit/scene_blocking_tool.py)
- [JSON 模板](../assets/scene-blocking-toolkit/scene_template_泰山玉皇顶.json)
- [成品参考图](../assets/scene-blocking-toolkit/模板图_泰山玉皇顶_v1.png)
- [原 README](../assets/scene-blocking-toolkit/README.md)

生成前查看参考图并阅读 JSON/README。默认复用它的平面网格、人物方向箭头、机位视场扇形、道具、虚线动线及右侧信息表；调度图保留功能性色彩，主分镜图使用作者已经确认的项目画风，两者无需视觉同风格。

运行入口优先使用 [轻量适配器](../scripts/render_blocking.py)，仍调用原渲染器：

```text
python <skill>/scripts/render_blocking.py <项目场景配置.json> -o <项目调度图.png>
```

为分镜卡派生单机位聚焦图时，使用一个或多个 `--camera` 过滤机位名称/ID；不需要动线的静态镜头加 `--hide-moves`。该操作只修改内存中的副本，不覆盖场景总 JSON：

```text
python <skill>/scripts/render_blocking.py <场景总图.json> -o <聚焦图.png> --camera C2 --shots S03 --hide-moves
```

同一机位服务多个镜头时共用一张聚焦图。场景总图仍保留全部机位，并由该场或状态首次出现的分镜卡提供“查看全场机位”入口。

依赖 matplotlib、numpy 和可用中文字体。原 README 的本机 Python 路径只在实际存在且可运行时使用，不作为跨环境必需依赖。

复制 JSON 到项目输出目录再改，不覆盖原模板。替换所有示例人物、道具、场地尺寸和提示文字；无需的 sky_arrow/fence/entrance 删除。原模板矩形道具 x/y 是左下角，圆形为圆心；朝向向量与机位角度分开。angle 0 向图面右、90 向图面上，逆时针；未确认 FOV 时标为示意扇形，不当作光学参数。

无真实尺寸时加入 coordinate_labels，例如：

```json
{"coordinate_labels":{"x":"X（示意单位）→ 图面右","y":"Y（示意单位）→ 舞台方向","up":"舞台方向","unit":"示意单位"}}
```

同时在 meta.subtitle/footer 标注“草稿、非实测、待资产校准”，勿仅改轴标签却保留右侧“米/北”。无该字段时保留原工具米制方位，只有依据足够时才这样使用。

panel 字段是手写摘要，不会自动跟随 x/y/moves 的值更新。必须同步数字与说明；原示例动线的 panel 有取整差异，不继承。布局右栏为固定行距，长文本/人数多时缩短说明或按阶段拆图，渲染后检查遮挡与越界。人群散点只是固定 seed 的示意，不用于精确座位排布；固定座位应使用 persons/props 指定位置。

资产校准时改同一场级 JSON，保存版本与锚点差异，再运行工具重新生成总图和受影响的机位聚焦图，更新 HTML 引用。保留可编辑 JSON 和 PNG，HTML 可嵌入 PNG；无须另画相同的 SVG。导出时让对应分镜卡以缩略图引用聚焦 PNG，点击后查看完整聚焦图；首次出现的卡片另以紧凑入口打开总图。多个镜头共用一张 PNG 时只嵌入一次图像数据，不重复渲染或重复写入 base64。原工具没有自动读图或恢复三维空间能力，锚点必须按 scene-blocking.md 校验。
