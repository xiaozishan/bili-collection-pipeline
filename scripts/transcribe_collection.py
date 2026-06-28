#!/usr/bin/env python3
"""
Batch transcribe a Bilibili collection: download → extract audio → Whisper → .md.

Usage:
    python3 transcribe_collection.py collection.json --output ./transcripts --model small
    python3 transcribe_collection.py collection.json --output ./transcripts --model large-v3 --device cpu
    python3 transcribe_collection.py collection.json --output ./transcripts --skip-download
"""
import sys, os, json, argparse, subprocess, re, glob
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except:
    pass


def find_latest_mp4(output_dir):
    """you-get saves by title; find the most recently downloaded MP4"""
    files = [f for f in os.listdir(output_dir)
             if f.endswith('.mp4') and not f.endswith('.download')]
    if not files:
        return None
    files.sort(key=lambda f: os.path.getmtime(os.path.join(output_dir, f)), reverse=True)
    return os.path.join(output_dir, files[0])


def run_cmd(args, timeout=300):
    """Run command with binary capture (avoid GBK encoding issues)"""
    try:
        result = subprocess.run(args, capture_output=True, timeout=timeout)
        stdout = result.stdout.decode('utf-8', errors='replace') if result.stdout else ''
        stderr = result.stderr.decode('utf-8', errors='replace') if result.stderr else ''
        return result.returncode, stdout, stderr
    except subprocess.TimeoutExpired:
        print(f'  [WARN] Command timed out after {timeout}s: {" ".join(str(a) for a in args[:3])}')
        return -1, '', 'timeout'
    except FileNotFoundError as e:
        print(f'  [ERROR] Command not found: {e}')
        return -1, '', str(e)


def transcribe_video(v, output_dir, model, device, downloader, skip_download, temp_dir):
    """Process one video: download → WAV → Whisper → .md"""
    bvid = v['bvid']
    title = v.get('title', bvid)
    duration = v.get('duration', 0)
    duration_str = f'{duration // 60}分{duration % 60}秒' if duration else ''

    print(f'\n  [{bvid}] {title[:50]} ({duration_str})')
    renamed = os.path.join(temp_dir, f'{bvid}.mp4')
    wav_path = os.path.join(temp_dir, f'{bvid}.wav')

    # --- 1. Download ---
    if not skip_download and not os.path.exists(renamed):
        url = f'https://www.bilibili.com/video/{bvid}'
        if downloader == 'you-get':
            rc, _, err = run_cmd(['you-get', '-o', temp_dir, url], timeout=600)
            if rc != 0:
                # Try AVC format
                rc, _, err = run_cmd([
                    'you-get', '-o', temp_dir, '--format=dash-flv360-AVC', url
                ], timeout=600)
            mp4 = find_latest_mp4(temp_dir)
            if not mp4:
                print(f'  [FAIL] Download failed')
                return False
            # Rename to BVID for consistency
            if mp4 != renamed:
                if os.path.exists(renamed):
                    os.remove(mp4)
                else:
                    os.rename(mp4, renamed)
        elif downloader == 'yt-dlp':
            rc, _, err = run_cmd([
                'yt-dlp', '-o', renamed, '-f', 'bestaudio[ext=m4a]',
                f'--postprocessor-args', 'ffmpeg:-vn -acodec pcm_s16le -ar 16000 -ac 1',
                url
            ], timeout=600)
            if rc != 0:
                print(f'  [FAIL] yt-dlp failed')
                return False

    # --- 2. Extract WAV ---
    if os.path.exists(renamed) and not os.path.exists(wav_path):
        rc, _, _ = run_cmd([
            'ffmpeg', '-y', '-i', renamed,
            '-vn', '-acodec', 'pcm_s16le',
            '-ar', '16000', '-ac', '1',
            wav_path
        ], timeout=300)
        if rc != 0:
            print(f'  [FAIL] ffmpeg failed')
            return False

    # --- 3. Transcribe ---
    txt_path = os.path.join(temp_dir, f'{bvid}.txt')
    if os.path.exists(wav_path) and not os.path.exists(txt_path):
        # Use faster-whisper directly
        rc, stdout, stderr = run_cmd([
            sys.executable, '-c', f'''
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from faster_whisper import WhisperModel
model = WhisperModel("{model}", device="{device}", compute_type="float16" if "{device}"=="cuda" else "int8")
segments, info = model.transcribe(r"{wav_path}", beam_size=5, vad_filter=True)
for seg in segments:
    print(seg.text)
'''], timeout=3600)
        text = stdout.strip() or stderr.strip()
        if text:
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f'  [OK] Transcribed: {len(text)} chars')
        else:
            print(f'  [FAIL] Transcription empty')
            return False
    elif os.path.exists(txt_path):
        with open(txt_path, 'r', encoding='utf-8') as f:
            text = f.read()
        print(f'  [OK] Already transcribed: {len(text)} chars')
    else:
        print(f'  [FAIL] No audio file')
        return False

    # --- 4. Save as .md ---
    safe_title = re.sub(r'[\\/:*?"<>|]', '', title[:50]).strip()
    if not safe_title:
        safe_title = bvid
    md_file = os.path.join(output_dir, f'{safe_title}.md')
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(f'# {title}\n\n')
        f.write(f'> BVID: {bvid}')
        if duration:
            f.write(f' | 时长: {duration_str}')
        f.write('\n\n')
        with open(txt_path, 'r', encoding='utf-8') as tf:
            f.write(tf.read())

    print(f'  [OK] Saved: {os.path.basename(md_file)}')

    # --- 5. Cleanup ---
    for p in [renamed, wav_path]:
        try:
            if os.path.exists(p):
                os.remove(p)
        except:
            pass

    return True


def main():
    parser = argparse.ArgumentParser(description='Batch transcribe Bilibili collection')
    parser.add_argument('videos_json', help='Video list JSON from fetch_collection.py')
    parser.add_argument('--output', '-o', default='./transcripts', help='Output directory')
    parser.add_argument('--model', default='small',
                        choices=['tiny', 'base', 'small', 'medium', 'large-v3'],
                        help='Whisper model size')
    parser.add_argument('--device', default='cuda', choices=['cuda', 'cpu'],
                        help='Compute device')
    parser.add_argument('--downloader', default='you-get',
                        choices=['you-get', 'yt-dlp'],
                        help='Video downloader')
    parser.add_argument('--temp-dir', default='./.temp',
                        help='Temp directory for downloads/WAV')
    parser.add_argument('--progress', default='progress.json',
                        help='Progress JSON file (resume support)')
    parser.add_argument('--skip-download', action='store_true',
                        help='Skip download (use existing .wav files)')
    parser.add_argument('--limit', type=int, default=0,
                        help='Max videos to process')
    args = parser.parse_args()

    # Load video list
    with open(args.videos_json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    videos = data.get('videos', [])
    if not videos:
        print('No videos in JSON')
        sys.exit(1)

    print(f'Loaded {len(videos)} videos from {data.get("collection", {}).get("name", "unknown")}')
    total_s = sum(v.get('duration', 0) for v in videos)
    print(f'Total duration: {total_s//3600}h{total_s%3600//60}m')

    os.makedirs(args.output, exist_ok=True)
    os.makedirs(args.temp_dir, exist_ok=True)

    # Load progress
    done = {}
    if os.path.exists(args.progress):
        with open(args.progress, 'r') as f:
            done = json.load(f)
    done_set = set(done.get('done', []))

    processed = 0
    for i, v in enumerate(videos):
        if args.limit and processed >= args.limit:
            break

        bvid = v['bvid']
        if bvid in done_set:
            print(f'[{i+1}/{len(videos)}] {bvid} skipped (already done)')
            continue

        ok = transcribe_video(v, args.output, args.model, args.device,
                              args.downloader, args.skip_download, args.temp_dir)
        if ok:
            done_set.add(bvid)
            done['done'] = list(done_set)
            done['last'] = bvid
            with open(args.progress, 'w') as f:
                json.dump(done, f)
            processed += 1
        else:
            print(f'[WARN] {bvid} failed, continuing...')
            # Save progress even on failure to allow retry
            done['failed'] = list(set(done.get('failed', [])) | {bvid})
            with open(args.progress, 'w') as f:
                json.dump(done, f)

    print(f'\nDone: {len(done_set)}/{len(videos)} transcribed')
    print(f'Output: {args.output}')


if __name__ == '__main__':
    main()
