# 场景调度图工具包 v1

给视频模型（即梦 / 可灵等）当参考图用的**俯视平面坐标调度图**生成器。
改 JSON 配置 → 跑一行命令 → 出 2400×1350 PNG（含站位朝向、机位 FOV、道具锚点、走位动线、坐标信息表）。

## 文件清单

| 文件 | 说明 |
|---|---|
| `scene_blocking_tool.py` | 渲染工具（配置驱动，无需改代码） |
| `scene_template_泰山玉皇顶.json` | 模板配置：完整示例场景，复制改坐标即可用 |
| `模板图_泰山玉皇顶_v1.png` | 模板配置渲染出的成品参考图 |

## 环境与运行

```bash
# 依赖：Python 3.10+ 与 matplotlib（pip install matplotlib）
python scene_blocking_tool.py <配置.json> -o <输出.png>
# 省略 -o 时输出与配置同名的 .png
```

本机已配置好的运行环境（免装）：
`C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe`

## 坐标约定

- 单位：米；原点：场地**左下角 (0,0)**；X→东，Y→北（上）
- 场地矩形 `canvas.w × canvas.h`，北缘可配 `fence`（围栏影线），南缘可配 `entrance`（出入口）
- 机位角度 `angle`：0=朝东，90=朝北，180=朝西，270=朝南（逆时针）；`fov` 为视场角，`len` 为扇形半径

## 配置字段速查

| 区块 | 关键字段 | 说明 |
|---|---|---|
| `meta` | title / subtitle / footer | 右侧信息表标题与页脚 |
| `canvas` | w / h / y_top / y_bottom | 场地尺寸与视图余量 |
| `fence` / `entrance` | y / x0,x1 / label / panel | 北缘围栏、南缘出入口 |
| `sky_arrow` | from / to / label | 画面外入场箭头（如九龙来向） |
| `props[]` | type: ring5 / circle / rect | 道具；`label_inside` 标签置中；`panel` 进信息表 |
| `crowds[]` | cx,cy / w,h / n / seed | 人群散布椭圆区，n=人数 |
| `persons[]` | x,y / facing / role / label_xy | 人物；`role:"star"` 为主角五角星；`facing` 为朝向向量 |
| `cameras[]` | x,y / angle / fov / len / note | 机位；`panel` 可写数组（第二行起为灰色注释） |
| `moves[]` | p0→p1 / rad / color | 走位动线虚线箭头；rad 控制弧度 |
| `tips[]` | 文本行 | 「给视频模型的提示要点」红色区块 |

## 使用建议

1. 复制模板 JSON，按实际剧本替换人物名单与坐标（label_xy 是标签位置，重叠时手动挪开）
2. 渲染后把 PNG 作为参考图 + 右侧信息表文字一并写进视频模型提示词
3. 主角放画面纵轴中心、人群两翼分列、焦点克制在一条连线上——实测模型跟随度最好
