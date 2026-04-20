import subprocess
import logging
import os
import shutil

logger = logging.getLogger(__name__)

class MediaMerger:
    """
    Ez az osztály felel a letöltött videó és audio stream-ek egybefűzéséért (muxing)
    az FFmpeg segítségével, vagy a hibás formátumok (pl. TS) átkonvertálásáért MP4-be.
    """
    def __init__(self, ffmpeg_path: str = None):
        """
        :param ffmpeg_path: opcionálisan megadható az ffmpeg bináris elérési útja,
                            egyébként a rendszer $PATH-ból veszi.
        """
        self.ffmpeg_path = ffmpeg_path or shutil.which("ffmpeg")
        if not self.ffmpeg_path:
            logger.warning("FFmpeg nem található a rendszeren. A Post-Processor nem fog működni!")

    def merge_audio_video(self, video_path: str, audio_path: str, output_path: str) -> bool:
        """
        Összefűzi a videót és a hangot egy új fájlba.
        Veszteségmentes másolást (-c copy) alkalmaz.
        """
        if not self.ffmpeg_path:
            logger.error("FFmpeg hiányzik, nem lehet összefűzni a fájlokat.")
            return False

        if not os.path.exists(video_path) or not os.path.exists(audio_path):
            logger.error("A megadott bemeneti fájlok nem találhatóak.")
            return False

        command = [
            self.ffmpeg_path,
            "-i", video_path,
            "-i", audio_path,
            "-c", "copy",
            output_path
        ]

        logger.info(f"Összefűzés indítása: {video_path} + {audio_path} -> {output_path}")

        try:
            process = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            logger.info("Összefűzés sikeresen befejeződött.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg hiba a fűzés során:\n{e.stderr}")
            return False

    def convert_ts_to_mp4(self, ts_file_path: str, output_mp4_path: str) -> bool:
        """
        Átkonvertálja a .ts fájlt (ami gyakran lejön m3u8-ból) egy normál .mp4 fájlba.
        Újrakódolás nélkül (stream copy), csak konténert cserélve.
        """
        if not self.ffmpeg_path:
            logger.error("FFmpeg hiányzik, nem lehet konvertálni.")
            return False

        if not os.path.exists(ts_file_path):
            logger.error(f"A bemeneti TS fájl nem található: {ts_file_path}")
            return False

        command = [
            self.ffmpeg_path,
            "-i", ts_file_path,
            "-c", "copy",
            output_mp4_path
        ]

        logger.info(f"Konvertálás indítása: {ts_file_path} -> {output_mp4_path}")

        try:
            process = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            logger.info("Konvertálás sikeresen befejeződött.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg hiba a konvertálás során:\n{e.stderr}")
            return False
