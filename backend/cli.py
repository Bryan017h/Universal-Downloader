import argparse
import json
import sys
import os
from core import *
from downloaders import DownloaderMixin

# Mock class to replace the Tkinter UI "self"
class HeadlessDownloader(DownloaderMixin):
    def __init__(self):
        self.stop_event = type('obj', (object,), {'is_set': lambda: False})
        self.ffmpeg_path = "./ffmpeg.exe" if os.path.exists("./ffmpeg.exe") else "ffmpeg"
        self.handbrake_path = "./HandBrakeCLI.exe" if os.path.exists("./HandBrakeCLI.exe") else "HandBrakeCLI"
        
        # Determine actual paths for binaries
        if not os.path.exists(self.ffmpeg_path):
             # Try looking in the same folder as this script
             local_ff = os.path.join(os.path.dirname(__file__), "ffmpeg.exe")
             if os.path.exists(local_ff): self.ffmpeg_path = local_ff

        if not os.path.exists(self.handbrake_path):
             local_hb = os.path.join(os.path.dirname(__file__), "HandBrakeCLI.exe")
             if os.path.exists(local_hb): self.handbrake_path = local_hb

    # Override UI updates to print JSON instead
    class MockVar:
        def set(self, val): pass # We don't use the Tkinter vars
    
    class MockBar:
        def set(self, val): pass
        def configure(self, **kwargs): pass
        def start(self): pass
        def stop(self): pass
        def get(self): return 0

    def after(self, delay, func): 
        # In headless mode, we just run the 'finish' function immediately
        func()

    # The Core "Emit" Function
    def emit_status(self, type, data):
        print(json.dumps({"type": type, "data": data}), flush=True)

    # Override the progress hook from your original code
    def progress_hook(self, d):
        if d["status"] == "downloading" and d.get("total_bytes"):
            percent = d["downloaded_bytes"] / d["total_bytes"]
            self.emit_status("progress", percent)
            
    # Override finish methods to just emit JSON
    def finish_success(self):
        self.emit_status("success", "Download Complete")
    
    def finish_fail(self, message):
        self.emit_status("error", message)

    # Redefine the task runner to use our emit_status
    def run_headless(self, args):
        self.status_var = self.MockVar()
        self.progress_bar = self.MockBar()
        self.status_label = type('obj', (object,), {'configure': lambda **k: None})
        self.download_btn = type('obj', (object,), {'configure': lambda **k: None})
        self.format_switch = type('obj', (object,), {'configure': lambda **k: None})
        self.res_menu = type('obj', (object,), {'configure': lambda **k: None})
        self.hb_checkbox = type('obj', (object,), {'configure': lambda **k: None})
        self.trim_checkbox = type('obj', (object,), {'configure': lambda **k: None})
        self.audio_fmt_menu = type('obj', (object,), {'configure': lambda **k: None})
        
        # Map CLI args to your original function arguments
        self.run_download_manager(
            url=args.url,
            folder=args.folder,
            mode=args.mode,
            res=args.res,
            audio_fmt=args.audio_fmt,
            use_hb=args.use_hb,
            hb_preset=args.hb_preset,
            trim_on=args.trim_on,
            t_start=args.trim_start,
            t_end=args.trim_end
        )

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--folder", required=True)
    parser.add_argument("--mode", default="Video + Audio")
    parser.add_argument("--res", default="Best Available")
    parser.add_argument("--audio_fmt", default="mp3")
    parser.add_argument("--use_hb", action="store_true")
    parser.add_argument("--hb_preset", default="Auto (Smart Match)")
    parser.add_argument("--trim_on", action="store_true")
    parser.add_argument("--trim_start", default="")
    parser.add_argument("--trim_end", default="")

    args = parser.parse_args()
    
    app = HeadlessDownloader()
    
    # Monkey-patch the progress hook in the mixin to use our JSON emitter
    # (This is a trick to avoid rewriting downloaders.py entirely)
    def json_progress_hook(d):
        if d["status"] == "downloading" and d.get("total_bytes"):
            percent = d["downloaded_bytes"] / d["total_bytes"]
            print(json.dumps({"type": "progress", "data": percent, "text": f"{int(percent*100)}%"}), flush=True)
        elif d["status"] == "finished":
            print(json.dumps({"type": "status", "data": "Processing conversion..."}), flush=True)

    # We inject this hook into the options inside run_download_task logic
    # But for now, let's rely on the main class logic running.
    try:
        app.run_headless(args)
    except Exception as e:
        print(json.dumps({"type": "error", "data": str(e)}), flush=True)