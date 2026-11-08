import sys, subprocess, asyncio
from playwright.async_api import async_playwright
FPS=30; DUR=31.0
async def main(mode):
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(viewport={'width':1080,'height':1920})
        await pg.goto('file:///home/claude/short/short.html'); await pg.wait_for_timeout(2500)
        await pg.evaluate("document.getAnimations().forEach(a=>a.pause())")
        async def at(t):
            await pg.evaluate(f"document.getAnimations().forEach(a=>{{a.currentTime={t*1000}}})")
        if mode=='preview':
            for t in [2,7,12,17,22,29]:
                await at(t); await pg.screenshot(path=f'prev_{t}.jpg',type='jpeg',quality=80)
        else:
            ff=subprocess.Popen(['ffmpeg','-y','-f','image2pipe','-framerate',str(FPS),'-c:v','mjpeg','-i','-','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-r',str(FPS),'tmp_short.mp4'],stdin=subprocess.PIPE,stderr=subprocess.DEVNULL)
            n=int(DUR*FPS)
            for i in range(n):
                await at(i/FPS); ff.stdin.write(await pg.screenshot(type='jpeg',quality=92))
            ff.stdin.close(); ff.wait(); print('rc',ff.returncode)
        await b.close()
asyncio.run(main(sys.argv[1]))
