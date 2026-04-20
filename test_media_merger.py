import asyncio
from src.processor.media_merger import MediaMerger

async def main():
    print("Testing MediaMerger...")
    merger = MediaMerger()
    if merger.ffmpeg_path:
        print(f"FFmpeg megtalálva: {merger.ffmpeg_path}")

        # Létrehozunk egy érvényes teszt videót, ha még nem létezik.
        test_video = 'Big_Buck_Bunny_1080_10s_1MB.mp4'
        output_video = 'output_test.mp4'

        # Szimuláljuk, hogy ezt a fájlt "javítjuk"/konvertáljuk a MediaMerger-rel
        success = merger.convert_ts_to_mp4(test_video, output_video)

        if success:
             print(f"✅ Sikeres konvertálás: {output_video}")
        else:
             print("❌ Hiba a konvertálás során.")
    else:
        print("❌ FFmpeg NEM található. Telepítsd az ffmpeg-et a rendszerre.")

if __name__ == "__main__":
    asyncio.run(main())
