"""Rendu d'un Short Kit Pro (HTML animé -> MP4 1080x1920, 30 fps).

Usage :
  python3 modele-short-render.py <fichier.html> <sortie.mp4> [preview]

- La durée est lue dans l'attribut data-duration de <body> (en secondes), sinon 31 s.
- Taille : data-width / data-height de <body> (défaut 1080x1920 ; 1920x1080 pour une vidéo longue).
- "preview" écrit 6 images JPEG (preview_<t>.jpg) à côté de la sortie au lieu de la vidéo.
Les animations CSS sont figées puis avancées image par image (document.getAnimations / currentTime).
"""
import sys, os, subprocess, asyncio, pathlib
from playwright.async_api import async_playwright

FPS = 30

async def main(html, out, mode):
    html = pathlib.Path(html).resolve()
    out = pathlib.Path(out).resolve()
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={'width': 1080, 'height': 1920})
        await pg.goto(html.as_uri())
        w = int(await pg.evaluate("parseInt(document.body.dataset.width || '1080')"))
        h = int(await pg.evaluate("parseInt(document.body.dataset.height || '1920')"))
        if (w, h) != (1080, 1920):
            await pg.set_viewport_size({'width': w, 'height': h})
        await pg.wait_for_load_state('networkidle')
        await pg.evaluate("document.fonts.ready")
        await pg.wait_for_timeout(500)
        dur = float(await pg.evaluate("parseFloat(document.body.dataset.duration || '31')"))
        await pg.evaluate("document.getAnimations().forEach(a => a.pause())")

        async def at(t):
            await pg.evaluate(f"document.getAnimations().forEach(a => {{ a.currentTime = {t * 1000} }})")

        if mode == 'preview':
            for t in [1.5, dur * 0.2, dur * 0.4, dur * 0.6, dur * 0.8, dur - 1]:
                await at(t)
                await pg.screenshot(path=str(out.parent / f'preview_{t:.1f}.jpg'), type='jpeg', quality=80)
        else:
            tmp = out.with_name(out.stem + '.tmp.mp4')
            ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', str(FPS),
                                   '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18',
                                   '-pix_fmt', 'yuv420p', '-r', str(FPS), '-movflags', '+faststart', str(tmp)],
                                  stdin=subprocess.PIPE)
            for i in range(int(dur * FPS)):
                await at(i / FPS)
                ff.stdin.write(await pg.screenshot(type='jpeg', quality=92))
            ff.stdin.close()
            rc = ff.wait()
            if rc != 0:
                raise SystemExit(f'ffmpeg a échoué (code {rc})')
            os.replace(tmp, out)
            print('ok', out, f'{dur:.1f}s')
        await b.close()

if __name__ == '__main__':
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    asyncio.run(main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else 'video'))
