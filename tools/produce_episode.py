r"""Produce a Second Chapter Love Short end to end from an episode spec (JSON).

Usage: python3 -I tools/produce_episode.py media/second-chapter-love/episodes/<name>.json

Spec fields:
  name, voice_id, narration (lines separated by \n), hook (top text, \N for line break),
  cast: {Tag: "path/to/reference.png"},
  scenes: [{image: prompt using @Tag, motion: prompt, lines: [narration line indexes]}]
          or {reuse: <scene index>, lines: [...]} for a slow zoom on an earlier scene image.
Keys come from the session proxy (Runway, ElevenLabs); placeholders are sent here.
"""
import base64, json, os, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RW = "https://api.dev.runwayml.com/v1"
RW_H = ["-H", "Authorization: Bearer key_" + "0" * 124, "-H", "X-Runway-Version: 2024-11-06", "-H", "Content-Type: application/json"]
EL_H = ["-H", "xi-api-key: sk_" + "0" * 48, "-H", "Content-Type: application/json"]
MUSIC = os.path.join(ROOT, "media/what-life-carries/What_Life_Carries_01_Texting_Without_Plans.mp4")
FONT = "Inter Display"
STYLE = (" Photorealistic cinematic film still, vertical 9:16, warm natural color, natural skin texture. "
         "Keep each tagged person's face, hair and body exactly the same as their reference image.")


def sh(args, **kw):
    return subprocess.run(args, capture_output=True, text=True, **kw)


def rw(method, path, body=None):
    a = ["curl", "-sS", "-X", method, RW + path] + RW_H
    if body is None:
        return json.loads(sh(a).stdout)
    return json.loads(sh(a + ["--data-binary", "@-"], input=json.dumps(body)).stdout)


def rw_task(path, body, out):
    r = rw("POST", path, body)
    if "id" not in r:
        raise SystemExit(f"Runway error: {r}")
    while True:
        t = rw("GET", f"/tasks/{r['id']}")
        if t.get("status") in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
        time.sleep(5)
    if t["status"] != "SUCCEEDED":
        raise SystemExit(f"Runway task failed: {t}")
    url = t["output"][0]
    for _ in range(4):
        if sh(["curl", "-sS", "-o", out, "-w", "%{http_code}", url]).stdout == "200":
            return url
        time.sleep(15)
    raise SystemExit(f"download failed: {out}")


def data_uri(path):
    return "data:image/png;base64," + base64.b64encode(open(path, "rb").read()).decode()


def narrate(spec, work):
    body = {"text": spec["narration"], "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.55, "similarity_boost": 0.8, "style": 0.25, "speed": 0.92}}
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{spec['voice_id']}/with-timestamps?output_format=mp3_44100_128"
    cache = f"{work}/align.json"
    if os.path.exists(cache) and os.path.exists(f"{work}/narr.mp3"):
        return json.load(open(cache))
    d = json.loads(sh(["curl", "-sS", "-X", "POST", url] + EL_H + ["--data", json.dumps(body)]).stdout)
    if "alignment" in d:
        json.dump(d["alignment"], open(cache, "w"))
    if "audio_base64" not in d:
        raise SystemExit(f"ElevenLabs error: {d}")
    open(f"{work}/narr.mp3", "wb").write(base64.b64decode(d["audio_base64"]))
    return d["alignment"]


def timings(al):
    ch, st, en = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
    lines, words, cur = [], [], None
    line_start = None
    for c, t0, t1 in zip(ch, st, en):
        if c == "\n":
            if cur: words.append(cur); cur = None
            if line_start is not None: lines.append((line_start, last)); line_start = None
            words.append(None)
            continue
        if line_start is None and c != " ": line_start = t0
        if c == " ":
            if cur: words.append(cur); cur = None
            continue
        if cur is None: cur = [c, t0, t1]
        else: cur[0] += c; cur[2] = t1
        last = t1
    if cur: words.append(cur)
    if line_start is not None: lines.append((line_start, last))
    return lines, words


def captions(words, hook, work):
    caps, buf = [], []
    def flush():
        if buf: caps.append((buf[0][1], buf[-1][2], " ".join(w[0] for w in buf))); buf.clear()
    for w in words:
        if w is None: flush(); continue
        if buf and len(" ".join(x[0] for x in buf)) + len(w[0]) > 22: flush()
        buf.append(w)
        if w[0][-1] in ".?!:": flush()
    flush()
    ts = lambda t: f"0:{int(t // 60):02d}:{t % 60:05.2f}"
    ev = []
    for i, (a0, a1, t) in enumerate(caps):
        end = caps[i + 1][0] if i + 1 < len(caps) and caps[i + 1][0] - a1 < 0.6 else a1 + 0.25
        ev.append(f"Dialogue: 0,{ts(a0)},{ts(end)},Cap,,0,0,0,,{t}")
    ev.append("Dialogue: 1,0:00:00.00,0:00:04.50,Top,,0,0,0,,{\\fad(200,400)}" + hook)
    hdr = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 720\nPlayResY: 1280\n[V4+ Styles]\n"
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
           f"Style: Cap,{FONT},50,&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,3.5,1.5,2,40,40,330,1\n"
           f"Style: Top,{FONT},44,&H0078C4F0,&H00FFFFFF,&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,3,1.5,8,50,50,150,1\n"
           "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    open(f"{work}/caps.ass", "w").write(hdr + "\n".join(ev) + "\n")


def endcard(work):
    from PIL import Image, ImageDraw, ImageFont
    W, H = 720, 1280
    im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
    for y in range(H):
        t = (y / H) ** 1.5
        d.line([(0, y), (W, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip((30, 12, 26), (120, 62, 48))))
    F = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
    def c(txt, y, size, col):
        f = ImageFont.truetype(F, size); w = d.textlength(txt, font=f); d.text(((W - w) / 2, y), txt, font=f, fill=col)
    c("SECOND CHAPTER", 500, 64, (255, 244, 228)); c("LOVE", 580, 64, (240, 196, 120))
    c("New stories Mon · Wed · Fri", 720, 34, (255, 244, 228)); c("Subscribe for the next one", 770, 34, (240, 196, 120))
    im.save(f"{work}/endcard.png")


def main(spec_path):
    spec = json.load(open(spec_path))
    out_dir = os.path.join(ROOT, "media/second-chapter-love", spec["name"])
    work = os.path.join(out_dir, "work"); os.makedirs(work, exist_ok=True)
    refs = [{"uri": data_uri(os.path.join(ROOT, p)), "tag": tag} for tag, p in spec["cast"].items()]

    al = narrate(spec, work)
    lines, words = timings(al)
    total = float(sh(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"{work}/narr.mp3"]).stdout)
    captions(words, spec["hook"], work)

    # scene images + clips
    for i, s in enumerate(spec["scenes"], 1):
        if "reuse" in s: continue
        img = f"{out_dir}/scene{i}.png"
        if not os.path.exists(img):
            used = [r for r in refs if "@" + r["tag"] in s["image"]]
            url = rw_task("/text_to_image", {"model": "gemini_2.5_flash", "ratio": "768:1344",
                          "promptText": s["image"] + STYLE, "referenceImages": used}, img)
            s["_url"] = url
        clip = f"{work}/clip{i}.mp4"
        if not s.get("still") and not os.path.exists(clip):
            rw_task("/image_to_video", {"model": "gen4_turbo", "promptImage": s.get("_url") or data_uri(img),
                    "promptText": s["motion"], "ratio": "720:1280", "duration": 5}, clip)

    # segments: each scene covers its lines, ending where the next scene starts
    segs = []
    for i, s in enumerate(spec["scenes"]):
        start = 0.0 if i == 0 else lines[s["lines"][0]][0] - 0.15
        end = total if i == len(spec["scenes"]) - 1 else lines[spec["scenes"][i + 1]["lines"][0]][0] - 0.15
        segs.append((start, end))
    files = []
    for i, (s, (a, b)) in enumerate(zip(spec["scenes"], segs), 1):
        dur = round(b - a, 2); seg = f"{work}/seg{i}.mp4"; fo = max(dur - 0.3, 0)
        if "reuse" in s or s.get("still"):
            src = f"{out_dir}/scene{s.get('reuse', i)}.png"; frames = int(dur * 30) + 2
            vf = (f"scale=1440:2520,zoompan=z='1.12-0.0006*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=720x1280:fps=30,"
                  f"trim=duration={dur},fade=in:st=0:d=0.3,fade=out:st={fo}:d=0.3,format=yuv420p")
            sh(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", src, "-vf", vf, "-t", str(dur), "-c:v", "libx264", "-crf", "19", "-preset", "fast", seg])
        else:
            f = min(dur / 5.04, 2.0)
            vf = (f"scale=720:1280,setpts={f}*PTS,fps=30,tpad=stop_mode=clone:stop_duration=10,trim=duration={dur},"
                  f"fade=in:st=0:d=0.3,fade=out:st={fo}:d=0.3,format=yuv420p")
            sh(["ffmpeg", "-v", "error", "-y", "-i", f"{work}/clip{i}.mp4", "-vf", vf, "-an", "-c:v", "libx264", "-crf", "19", "-preset", "fast", seg])
        files.append(seg)
    endcard(work)
    sh(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", f"{work}/endcard.png", "-vf", "fps=30,fade=in:st=0:d=0.4,format=yuv420p",
        "-t", "3", "-c:v", "libx264", "-crf", "19", "-preset", "fast", f"{work}/seg_end.mp4"])
    files.append(f"{work}/seg_end.mp4")
    open(f"{work}/list.txt", "w").write("".join(f"file '{p}'\n" for p in files))
    sh(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{work}/list.txt", "-c", "copy", f"{work}/body.mp4"])
    full = total + 3
    out = f"{out_dir}/{spec['name']}.mp4"
    fc = (f"[0:v]ass={work}/caps.ass[v];[2:a]volume=0.13,atrim=0:{full},afade=t=out:st={full - 2}:d=2[m];"
          f"[1:a]apad=pad_dur=3.2[n];[n][m]amix=inputs=2:duration=first:dropout_transition=0,volume=2[a]")
    r = sh(["ffmpeg", "-v", "error", "-y", "-i", f"{work}/body.mp4", "-i", f"{work}/narr.mp3", "-stream_loop", "-1", "-i", MUSIC,
            "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", str(full), "-c:v", "libx264", "-crf", "20",
            "-preset", "medium", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out])
    if r.returncode: raise SystemExit(r.stderr)
    print("DONE", out, round(full, 1), "sec")


if __name__ == "__main__":
    main(sys.argv[1])
