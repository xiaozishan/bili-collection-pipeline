#!/usr/bin/env python3
"""
Fetch Bilibili collection (播单/合集) video list via API.

Usage:
    python3 fetch_collection.py <bilibili-video-url> -o collection.json
    python3 fetch_collection.py BV1GeDSYhEVZ -o collection.json
"""
import sys, os, json, argparse, urllib.request, re, time
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except:
    pass

BAPI = 'https://api.bilibili.com'

def api_get(url, retries=3):
    """B站API GET请求"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0',
        'Referer': 'https://www.bilibili.com/',
    }
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
            else:
                raise

def extract_bvid(url_or_bvid):
    """从URL或纯BVID提取BVID"""
    bvid = url_or_bvid.strip()
    if bvid.startswith('http'):
        m = re.search(r'(BV[a-zA-Z0-9]+)', bvid)
        if m:
            bvid = m.group(1)
    return bvid if bvid.startswith('BV') else None

def fetch_collection_info(bvid):
    """通过B站API获取合集信息"""
    # 第一步：获取视频信息，包括 season_id
    view = api_get(f'{BAPI}/x/web-interface/view?bvid={bvid}')
    data = view.get('data', {})

    # 尝试获取合集信息
    ugc_season = data.get('ugc_season', {})
    season_id = None

    if ugc_season:
        season_id = ugc_season.get('id')
        season_name = ugc_season.get('title', '')
    else:
        # 尝试从视图数据获取 season_id
        season_id = data.get('season_id')

    if not season_id:
        print(f'错误: 该视频不属于任何合集')
        sys.exit(1)

    # 第二步：获取合集全部视频
    season_info = api_get(f'{BAPI}/x/web-interface/season?season_id={season_id}')
    season_data = season_info.get('data', {})

    episodes = []
    for ep in season_data.get('episodes', []):
        episodes.append({
            'bvid': ep['bvid'],
            'title': ep.get('title', ''),
            'duration': ep.get('duration', 0),
            'url': f'https://www.bilibili.com/video/{ep["bvid"]}',
            'page': ep.get('page', 1),
        })

    if not episodes:
        # 尝试 season_archive_list (分页合集)
        page = 1
        while True:
            arch = api_get(f'{BAPI}/x/web-interface/season/archive?season_id={season_id}&page={page}')
            arch_data = arch.get('data', {})
            arch_list = arch_data.get('archives', [])
            if not arch_list:
                break
            for a in arch_list:
                episodes.append({
                    'bvid': a['bvid'],
                    'title': a.get('title', ''),
                    'duration': a.get('duration', 0),
                    'url': f'https://www.bilibili.com/video/{a["bvid"]}',
                    'page': page,
                })
            if page >= arch_data.get('page', {}).get('count', 1):
                break
            page += 1
            time.sleep(1)

    up_name = season_data.get('up_name', data.get('owner', {}).get('name', ''))
    up_mid = season_data.get('up_mid', data.get('owner', {}).get('mid', ''))

    result = {
        'collection': {
            'id': season_id,
            'name': season_name or season_data.get('name', ''),
            'up_name': up_name,
            'up_mid': up_mid,
        },
        'videos': episodes,
        'total': len(episodes),
        'total_seconds': sum(e['duration'] for e in episodes),
    }

    return result

def main():
    parser = argparse.ArgumentParser(description='Fetch Bilibili collection video list')
    parser.add_argument('input', help='B站视频URL或BVID')
    parser.add_argument('-o', '--output', default='collection.json', help='输出JSON文件')
    args = parser.parse_args()

    bvid = extract_bvid(args.input)
    if not bvid:
        print('错误: 无法解析BVID')
        sys.exit(1)

    print(f'正在获取视频 {bvid} 的合集信息...')
    info = fetch_collection_info(bvid)

    c = info['collection']
    total_h = info['total_seconds'] // 3600
    total_m = (info['total_seconds'] % 3600) // 60
    print(f'\n合集: {c["name"]}')
    print(f'UP主: {c["up_name"]} (mid={c["up_mid"]})')
    print(f'集数: {info["total"]} 集')
    print(f'总时长: {total_h}h{total_m}m')
    print(f'\n按BVID排序的视频列表:')

    for i, v in enumerate(info['videos'], 1):
        m = v['duration'] // 60
        s = v['duration'] % 60
        print(f'  [{i:3d}] {v["bvid"]}  {v["title"][:50]:50s}  {m}:{s:02d}')

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    print(f'\n已保存: {args.output}')

if __name__ == '__main__':
    main()
