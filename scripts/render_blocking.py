"""Use the retained renderer with optional schematic coordinate labels.
python render_blocking.py scene.json -o scene.png
"""
import argparse
import importlib.util
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('blocking_original', root / 'assets/scene-blocking-toolkit/scene_blocking_tool.py')
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('config')
    ap.add_argument('-o', '--out', required=True)
    ap.add_argument('--camera', action='append', default=[], help='Only render matching camera ID/name prefixes, e.g. C2')
    ap.add_argument('--shots', help='Shot IDs shown in a focused-view subtitle, e.g. S03 or S11/S15')
    ap.add_argument('--hide-moves', action='store_true', help='Hide movement paths in a static shot focus view')
    args = ap.parse_args()
    cfg = json.loads(Path(args.config).read_text(encoding='utf-8-sig'))
    if args.camera:
        wanted = tuple(value.strip().casefold() for value in args.camera if value.strip())
        cameras = [
            camera for camera in cfg.get('cameras', [])
            if camera.get('name', '').casefold().startswith(wanted)
            or str(camera.get('id', '')).casefold() in wanted
        ]
        if not cameras:
            available = ', '.join(camera.get('name', '?') for camera in cfg.get('cameras', []))
            raise ValueError(f'No camera matched {args.camera!r}. Available: {available}')
        cfg['cameras'] = cameras
        camera_ids = ' / '.join(camera.get('name', '?').split()[0] for camera in cameras)
        meta = cfg.setdefault('meta', {})
        source_title = meta.get('title', '场景调度图')
        title_suffix = source_title.split('｜', 1)[-1]
        meta['title'] = f'分镜调度聚焦｜{title_suffix}'
        shot_text = f'适用 {args.shots}｜' if args.shots else ''
        meta['subtitle'] = f'{shot_text}仅显示当前机位 {camera_ids}｜非实测、非比例'
        meta['footer'] = '由场景总图派生 · 人物与固定锚点保持一致 · 完整机位见全场图'
        cfg['tips'] = [
            f'本图只显示{(" " + args.shots + " 使用的") if args.shots else "当前分镜使用的"} {camera_ids}；',
            '人物、道具、轴线与场景总图保持一致；',
            '其他机位见全场图，距离与 FOV 待场景资产校准。',
        ]
    if args.hide_moves:
        cfg['moves'] = []
    for c in cfg.get('crowds', []):
        if c['n'] <= 0 or c['w'] <= 1.2 or c['h'] <= 1.2:
            raise ValueError('Crowd requires n > 0 and width/height > 1.2; omit empty groups.')
    labels = cfg.get('coordinate_labels', {})
    original_save = tool.plt.Figure.savefig
    def save(fig, *a, **kw):
        ax = fig.axes[0]
        if labels:
            ax.set_xlabel(labels.get('x', 'X（示意单位）→ 图面右'))
            ax.set_ylabel(labels.get('y', 'Y（示意单位）→ 图面上'))
            for t in ax.texts:
                if t.get_text() == '北 N':
                    t.set_text(labels.get('up', '图面上'))
                elif t.get_text().endswith(' m'):
                    t.set_text(t.get_text()[:-2] + ' ' + labels.get('unit', '示意单位'))
        return original_save(fig, *a, **kw)
    tool.plt.Figure.savefig = save
    try:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        tool.render(cfg, args.out)
    finally:
        tool.plt.Figure.savefig = original_save
    print('saved:', args.out)

if __name__ == '__main__':
    main()
