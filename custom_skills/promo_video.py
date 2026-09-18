import os
import asyncio
import subprocess
import datetime
import traceback


def _project_dir(project_path):
    if project_path and os.path.exists(project_path):
        return project_path

    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.normpath(os.path.join(here, "..", "promo-video")),
        os.path.normpath(os.path.join(here, "..", "..", "promo-video")),
        os.path.normpath(os.path.join(here, "promo-video")),
    ]
    for cand in candidates:
        pkg = os.path.join(cand, "package.json")
        if os.path.exists(pkg):
            return cand

    repo_root = os.path.dirname(os.path.dirname(here))
    fallback = os.path.normpath(os.path.join(repo_root, "promo-video"))
    if os.path.exists(os.path.join(fallback, "package.json")):
        return fallback

    return None


def _schedule(coro):
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(coro)
    except Exception:
        pass


def run(parameters, update, context):
    variant = str(parameters.get("variant", "landscape")).strip().lower()
    if variant not in ("landscape", "portrait"):
        variant = "landscape"
    with_music = str(parameters.get("with_music", "true")).strip().lower() in ("1", "true", "yes", "on")
    project_path = parameters.get("project_path") or ""

    project_dir = _project_dir(project_path)
    if not project_dir:
        return "Error: Could not find the promo-video project. Pass 'project_path' (the directory containing promo-video/package.json)."

    composition = "Promo-Landscape" if variant == "landscape" else "Promo-Portrait"
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    video_name = f"promo-{variant}-{stamp}.mp4"
    out_dir = os.path.join(project_dir, "out")
    os.makedirs(out_dir, exist_ok=True)
    video_path = os.path.join(out_dir, video_name)

    chat_id = getattr(update.effective_chat, "id", None)
    if chat_id is not None:
        _schedule(context.bot.send_chat_action(chat_id=chat_id, action="typing"))
        _schedule(context.bot.send_message(
            chat_id=chat_id,
            text=f"🎬 Rendering promo video ({composition}, 60s)... this can take a minute or two.",
        ))

    try:
        render_cmd = f'npx remotion render "{composition}" "{video_path}"'
        result = subprocess.run(
            render_cmd,
            cwd=project_dir,
            shell=True,
            capture_output=True,
            text=True,
            timeout=1800,
        )
        if result.returncode != 0 or not os.path.exists(video_path):
            tail = (result.stderr or result.stdout or "")[-1500:]
            return f"Error: Remotion render failed.\n{tail}"

        final_name = f"promo-{variant}-final-{stamp}.mp4"
        final_path = os.path.join(out_dir, final_name)
        music_bed = os.path.join(project_dir, "audio", "music-mix.mp3")
        used_music = False

        if with_music and os.path.exists(music_bed):
            mux_cmd = (
                f'npx remotion ffmpeg -y -i "{video_path}" -i "{music_bed}" '
                f'-c:v copy -c:a aac -b:a 192k -shortest -pix_fmt yuv420p "{final_path}"'
            )
            mux = subprocess.run(
                mux_cmd,
                cwd=project_dir,
                shell=True,
                capture_output=True,
                text=True,
                timeout=1800,
            )
            if mux.returncode == 0 and os.path.exists(final_path):
                send_path = final_path
                used_music = True
            else:
                send_path = video_path
        else:
            send_path = video_path

        async def deliver():
            try:
                with open(send_path, "rb") as f:
                    await context.bot.send_video(
                        chat_id=chat_id,
                        video=f,
                        filename=os.path.basename(send_path),
                        caption=f"🎬 {composition} ({variant}, 60s) — {'with music bed' if used_music else 'no audio track'}",
                        timeout=600,
                    )
            except Exception as e:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"Render finished but sending failed: {e}\nFile saved at {send_path}",
                )

        _schedule(deliver())
        audio_note = "music bed muxed" if used_music else "no music bed found — sent silent video"
        return f"Success: Rendered {composition} and queued delivery to Telegram ({audio_note}). Video saved at {send_path}."

    except subprocess.TimeoutExpired:
        return "Error: Renders timed out after 30 minutes. The project may have a broken composition."
    except Exception as e:
        return f"Error rendering promo video: {e}\n{traceback.format_exc()}"