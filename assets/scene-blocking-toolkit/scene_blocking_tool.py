# -*- coding: utf-8 -*-
"""
场景调度图工具（视频模型参考图生成器）
用法：
    python scene_blocking_tool.py <config.json> [-o 输出.png]

配置驱动：场地 / 道具 / 人物 / 人群 / 机位 / 动线 / 提示要点全部写在 JSON 里，
改配置即可出任意场景的俯视平面坐标调度图。字段说明见 README.md。
"""
import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Wedge, Ellipse, FancyArrowPatch
from matplotlib.ticker import MultipleLocator
import numpy as np

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# ---- 调色板（浅色图纸风） ----
C_MAIN = "#C62828"   # 主角红
C_SUP = "#EF6C00"    # 配角橙
C_NPC = "#6D4C41"    # NPC 棕
C_CAM = "#00796B"    # 机位青
C_CROWD = "#546E7A"  # 人群蓝灰
C_MOVE = "#8E24AA"   # 动线紫
FIVE_COLORS = ["#1565C0", "#C62828", "#F9A825", "#FAFAFA", "#424242"]


def draw_site(ax, cfg):
    w = cfg["canvas"]["w"]
    h = cfg["canvas"]["h"]
    # 边界（南缘留出入口）
    ent = cfg.get("entrance")
    ax.plot([0, w], [h, h], color="#424242", lw=2.5)
    ax.plot([0, 0], [0, h], color="#424242", lw=2.5)
    ax.plot([w, w], [0, h], color="#424242", lw=2.5)
    if ent:
        ax.plot([0, ent["x0"]], [0, 0], color="#424242", lw=2.5)
        ax.plot([ent["x1"], w], [0, 0], color="#424242", lw=2.5)
        d = ent.get("depth", 1.5)
        ax.add_patch(Rectangle((ent["x0"], -d), ent["x1"] - ent["x0"], d,
                               fill=False, ec="#8D8D8D", lw=1.0, hatch="//"))
        ax.text((ent["x0"] + ent["x1"]) / 2, -d - 0.8, ent["label"],
                fontsize=8, ha="center", color="#616161")
    else:
        ax.plot([0, w], [0, 0], color="#424242", lw=2.5)
    # 围栏（北缘影线）
    fen = cfg.get("fence")
    if fen:
        fy = fen["y"]
        ax.plot([0, w], [fy, fy], color="#8D8D8D", lw=1.0)
        for x in np.arange(0, w, 1.2):
            ax.plot([x, x + 0.7], [fy, fy + 0.9], color="#B0B0B0", lw=0.7)
        ax.text(0.8, fy - 0.9, fen["label"], fontsize=8, color="#757575")
    # 画面外入场箭头（如九龙来向）
    sa = cfg.get("sky_arrow")
    if sa:
        ax.annotate("", xy=tuple(sa["to"]), xytext=tuple(sa["from"]),
                    arrowprops=dict(arrowstyle="-|>", color="#B71C1C", lw=2.6,
                                    linestyle=(0, (6, 4)), mutation_scale=22), zorder=5)
        ax.text(sa["label_xy"][0], sa["label_xy"][1], sa["label"], fontsize=9,
                color="#B71C1C", zorder=7,
                bbox=dict(boxstyle="round,pad=0.2", fc="#FFEBEE", ec="#EF9A9A", lw=0.8))


def draw_prop(ax, p):
    t = p["type"]
    if t == "ring5":  # 五色环高台
        r = p["r"]
        for i, c in enumerate(FIVE_COLORS):
            ax.add_patch(Wedge((p["x"], p["y"]), r, i * 72 - 90, (i + 1) * 72 - 90,
                               width=0.9, fc=c, ec="none", alpha=0.9, zorder=2))
        ax.add_patch(Circle((p["x"], p["y"]), r - 0.9, fc="#EFEBE9", ec="#6D4C41",
                            lw=1.6, zorder=2))
    elif t == "circle":
        ax.add_patch(Circle((p["x"], p["y"]), p["r"],
                            fc=p.get("fc", "#C8E6C9"), ec=p.get("ec", "#2E7D32"),
                            lw=1.4, zorder=3))
    elif t == "rect":
        ax.add_patch(Rectangle((p["x"], p["y"]), p["w"], p["h"],
                               fc=p.get("fc", "#BDBDBD"), ec=p.get("ec", "#616161"),
                               lw=1.2, zorder=3))
    # 标签
    if p.get("label_inside"):
        ax.text(p.get("lx", p["x"] + (p.get("w", 0) / 2 if t == "rect" else 0)),
                p.get("ly", p["y"] + (p.get("h", 0) / 2 if t == "rect" else 0)),
                p["label"], fontsize=7.5, ha="center", va="center",
                color=p.get("label_color", "#424242"), zorder=4)
    elif p.get("label"):
        lx, ly = p.get("label_xy", [p["x"], p["y"] + p.get("r", 0) + 0.6])
        ax.text(lx, ly, p["label"], fontsize=8.5, ha="center", color="#4E342E",
                bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="#BCAAA4",
                          lw=0.6, alpha=0.9), zorder=7)


def draw_crowd(ax, c):
    ax.add_patch(Ellipse((c["cx"], c["cy"]), c["w"], c["h"], fill=False,
                         ec=C_CROWD, lw=1.2, ls=(0, (4, 3)), alpha=0.75, zorder=3))
    rng = np.random.default_rng(c.get("seed", 0))
    pts = []
    while len(pts) < c["n"]:
        px_ = rng.uniform(c["cx"] - c["w"] / 2 + 0.6, c["cx"] + c["w"] / 2 - 0.6)
        py_ = rng.uniform(c["cy"] - c["h"] / 2 + 0.6, c["cy"] + c["h"] / 2 - 0.6)
        if ((px_ - c["cx"]) / (c["w"] / 2)) ** 2 + ((py_ - c["cy"]) / (c["h"] / 2)) ** 2 <= 0.8:
            pts.append((px_, py_))
    xs, ys = zip(*pts)
    ax.scatter(xs, ys, s=48, c=C_CROWD, edgecolors="white", linewidths=0.6, zorder=5)
    ax.text(c["cx"], c["cy"] + c["h"] / 2 + 0.5, c["label"], fontsize=8.5,
            ha="center", color="#37474F", zorder=7,
            bbox=dict(boxstyle="round,pad=0.2", fc="#ECEFF1", ec="#90A4AE", lw=0.6))


def draw_person(ax, p):
    star = p.get("role") == "star"
    color = p.get("color", C_MAIN if star else C_SUP)
    if star:
        ax.scatter([p["x"]], [p["y"]], marker="*", s=460, c=color,
                   edgecolors="white", linewidths=1.2, zorder=6)
    else:
        ax.scatter([p["x"]], [p["y"]], s=180, c=color, edgecolors="white",
                   linewidths=1.0, zorder=6)
    dx, dy = p.get("facing", [0, 1])
    ax.annotate("", xy=(p["x"] + dx * 1.7, p["y"] + dy * 1.7), xytext=(p["x"], p["y"]),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.8,
                                mutation_scale=14), zorder=6)
    lx, ly = p.get("label_xy", [p["x"] + 0.7, p["y"] + 0.7])
    ax.text(lx, ly, f"{p['name']} ({p['x']:g},{p['y']:g})", fontsize=9,
            color="#212121", zorder=8,
            bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="#BDBDBD",
                      lw=0.6, alpha=0.9))


def draw_camera(ax, c):
    ax.scatter([c["x"]], [c["y"]], marker="s", s=130, c=C_CAM,
               edgecolors="white", linewidths=1.0, zorder=8)
    ax.add_patch(Wedge((c["x"], c["y"]), c["len"], c["angle"] - c["fov"] / 2,
                       c["angle"] + c["fov"] / 2, fc=C_CAM, alpha=0.10,
                       ec=C_CAM, lw=1.0, zorder=2))
    lx, ly = c.get("label_xy", [c["x"] + 1.0, c["y"] + 0.6])
    ax.text(lx, ly, f"{c['name']} ({c['x']:g},{c['y']:g})\n{c['note']}",
            fontsize=8.5, color="#004D40", zorder=8,
            bbox=dict(boxstyle="round,pad=0.2", fc="#E0F2F1", ec="#80CBC4", lw=0.7))


def draw_move(ax, m):
    color = m.get("color", C_MOVE)
    ax.add_patch(FancyArrowPatch(tuple(m["p0"]), tuple(m["p1"]),
                                 connectionstyle=f"arc3,rad={m.get('rad', 0.0)}",
                                 arrowstyle="-|>", mutation_scale=17, lw=2.0,
                                 ls=(0, (5, 3)), color=color, zorder=4))
    lx, ly = m.get("label_xy", [(m["p0"][0] + m["p1"][0]) / 2 + 0.4,
                                (m["p0"][1] + m["p1"][1]) / 2 + 0.4])
    ax.text(lx, ly, m["label"], fontsize=8.5, color=color, zorder=8,
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec=color, lw=0.6,
                      alpha=0.9))


def draw_panel(fig, cfg):
    px = fig.add_axes([0.65, 0.05, 0.335, 0.90])
    px.axis("off")
    T = px.text
    kw = dict(transform=px.transAxes, va="top", family="Microsoft YaHei")
    meta = cfg["meta"]
    T(0.0, 1.00, meta["title"], fontsize=14.5, color="#212121", weight="bold", **kw)
    T(0.0, 0.945, meta["subtitle"], fontsize=9.5, color="#616161", **kw)

    def block(y0, title, lines):
        T(0.0, y0, title, fontsize=11, color="#004D40", weight="bold", **kw)
        y = y0 - 0.036
        for txt, c in lines:
            T(0.0, y, txt, fontsize=9.2, color=c, **kw)
            y -= 0.0315
        return y - 0.012

    lines = []
    for p in cfg.get("persons", []):
        c = p.get("color", C_MAIN if p.get("role") == "star" else C_SUP)
        lines.append((p["panel"], c))
    for c in cfg.get("crowds", []):
        lines.append((c["panel"], "#37474F"))
    y = block(0.885, "【人物站位 · 朝向】", lines)

    lines = []
    for c in cfg.get("cameras", []):
        panel = c["panel"] if isinstance(c["panel"], list) else [c["panel"]]
        lines.append((panel[0], "#004D40"))
        lines += [(s, "#616161") for s in panel[1:]]
    y = block(y, "【机位 · 拍摄方向】", lines)

    y = block(y, "【走位动线】",
              [(m["panel"], m.get("color", C_MOVE)) for m in cfg.get("moves", [])])

    lines = [(p["panel"], "#4E342E") for p in cfg.get("props", []) if p.get("panel")]
    site = "｜".join(x["panel"] for x in (cfg.get("fence"), cfg.get("entrance"))
                    if x and x.get("panel"))
    if site:
        lines.append((site, "#4E342E"))
    y = block(y, "【道具锚点】", lines)

    if cfg.get("tips"):
        y = block(y, "【给视频模型的提示要点】",
                  [(t, "#B71C1C") for t in cfg["tips"]])
    if meta.get("footer"):
        T(0.0, 0.012, meta["footer"], fontsize=8, color="#9E9E9E", **kw)


def render(cfg, out_path):
    w = cfg["canvas"]["w"]
    h = cfg["canvas"]["h"]
    fig = plt.figure(figsize=(16, 9), dpi=150, facecolor="#FAFAF7")
    ax = fig.add_axes([0.035, 0.065, 0.60, 0.865])
    ax.set_facecolor("#FFFFFF")
    ax.set_xlim(-2.5, w + 2.5)
    ax.set_ylim(cfg["canvas"].get("y_bottom", -2.8), cfg["canvas"].get("y_top", h + 3.2))
    ax.set_aspect("equal")
    ax.xaxis.set_major_locator(MultipleLocator(10))
    ax.yaxis.set_major_locator(MultipleLocator(10))
    ax.xaxis.set_minor_locator(MultipleLocator(2))
    ax.yaxis.set_minor_locator(MultipleLocator(2))
    ax.grid(which="major", color="#BDBDBD", lw=0.8, alpha=0.55)
    ax.grid(which="minor", color="#E0E0E0", lw=0.5, alpha=0.5)
    ax.tick_params(labelsize=8, colors="#616161")
    ax.set_xlabel("X（米）→ 东", fontsize=10, color="#424242")
    ax.set_ylabel("Y（米）→ 北", fontsize=10, color="#424242")

    draw_site(ax, cfg)
    for p in cfg.get("props", []):
        draw_prop(ax, p)
    for c in cfg.get("crowds", []):
        draw_crowd(ax, c)
    for p in cfg.get("persons", []):
        draw_person(ax, p)
    for c in cfg.get("cameras", []):
        draw_camera(ax, c)
    for m in cfg.get("moves", []):
        draw_move(ax, m)

    # 北向标 + 比例尺
    ax.annotate("", xy=(w + 1.2, h + 1.9), xytext=(w + 1.2, h - 0.1),
                arrowprops=dict(arrowstyle="-|>", color="#424242", lw=1.6,
                                mutation_scale=14))
    ax.text(w + 1.2, h + 2.3, "北 N", fontsize=9, ha="center", color="#424242")
    sb = min(10, w / 4)
    ax.plot([1, 1 + sb], [1.2, 1.2], color="#424242", lw=1.6)
    ax.plot([1, 1], [1.0, 1.4], color="#424242", lw=1.6)
    ax.plot([1 + sb, 1 + sb], [1.0, 1.4], color="#424242", lw=1.6)
    ax.text(1, 0.3, "0", fontsize=8, color="#424242")
    ax.text(1 + sb - 0.8, 0.3, f"{sb:g} m", fontsize=8, color="#424242")

    draw_panel(fig, cfg)
    fig.savefig(out_path, facecolor=fig.get_facecolor())
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description="场景调度图工具（俯视平面坐标）")
    ap.add_argument("config", help="场景配置 JSON 路径")
    ap.add_argument("-o", "--out", default=None, help="输出 PNG 路径（默认与配置同名）")
    args = ap.parse_args()
    cfg_path = Path(args.config)
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    out = args.out or str(cfg_path.with_suffix(".png"))
    render(cfg, out)
    print("saved:", out)


if __name__ == "__main__":
    sys.exit(main())
