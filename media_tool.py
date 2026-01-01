#!/usr/bin/env python3
"""
Media Tool - MP4 to MP3 Converter & YouTube Downloader
Supports batch conversion and multi-format downloads
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import yt_dlp


class MediaTool:
    def __init__(self):
        self.check_dependencies()
    
    def check_dependencies(self):
        """Check if required dependencies are installed"""
        try:
            subprocess.run(['ffmpeg', '-version'], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL, 
                         check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("[ERROR] ffmpeg is not installed!")
            print("Install it with: sudo apt update && sudo apt install ffmpeg -y")
            sys.exit(1)
    
    def convert_mp4_to_mp3(self, input_file, output_dir=None, bitrate='192k'):
        """Convert a single MP4 file to MP3"""
        input_path = Path(input_file)
        
        if not input_path.exists():
            return f"[ERROR] File not found: {input_file}"
        
        if not input_path.suffix.lower() in ['.mp4', '.mkv', '.avi', '.mov', '.flv', '.webm']:
            return f"[SKIP] Skipping non-video file: {input_file}"
        
        # Determine output path
        if output_dir:
            output_path = Path(output_dir) / f"{input_path.stem}.mp3"
            output_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            output_path = input_path.with_suffix('.mp3')
        
        try:
            print(f"[CONVERT] Converting: {input_path.name} -> {output_path.name}")
            
            # FFmpeg command for complete audio extraction
            cmd = [
                'ffmpeg',
                '-i', str(input_path),
                '-vn',  # No video
                '-acodec', 'libmp3lame',
                '-b:a', bitrate,
                '-map', '0:a:0',  # Map first audio stream
                '-write_xing', '0',  # Disable Xing header for accurate duration
                '-fflags', '+bitexact',  # Ensure exact conversion
                '-y',  # Overwrite output file
                str(output_path)
            ]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
                print(f"[OK] Successfully converted: {input_path.name} -> {output_path.name}")
                print(f"[OK] Output file size: {output_path.stat().st_size} bytes")
                return f"[OK] Successfully converted: {output_path.name}"
            else:
                error_msg = result.stderr[-500:] if result.stderr else "Unknown error"
                print(f"[ERROR] MP4->MP3 FFmpeg failed for {input_path.name}")
                print(f"[ERROR] Command: {' '.join(cmd)}")
                print(f"[ERROR] Return code: {result.returncode}")
                if output_path.exists():
                    print(f"[ERROR] Output file size: {output_path.stat().st_size} bytes")
                print(f"[ERROR] FFmpeg stderr: {error_msg}")
                return f"[FAIL] Failed to convert: {input_path.name}"
                
        except Exception as e:
            return f"[ERROR] Error converting {input_path.name}: {str(e)}"
    
    def convert_mp3_to_mp4(self, input_file, output_dir=None, image_path=None):
        """Convert a single MP3 file to MP4 with optional background image"""
        input_path = Path(input_file)
        
        if not input_path.exists():
            return f"[ERROR] File not found: {input_file}"
        
        if not input_path.suffix.lower() in ['.mp3', '.m4a', '.aac', '.wav', '.flac', '.ogg']:
            return f"[SKIP] Skipping non-audio file: {input_file}"
        
        # Determine output path
        if output_dir:
            output_path = Path(output_dir) / f"{input_path.stem}.mp4"
            output_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            output_path = input_path.with_suffix('.mp4')
        
        try:
            print(f"[CONVERT] Converting: {input_path.name} -> {output_path.name}")
            
            # FFmpeg command for conversion with full audio preservation
            if image_path and Path(image_path).exists():
                # With custom image - loop image for full audio duration
                cmd = [
                    'ffmpeg',
                    '-loop', '1',  # Loop the image
                    '-framerate', '25',  # 25 fps for compatibility
                    '-i', str(image_path),
                    '-i', str(input_path),
                    '-c:v', 'libx264',
                    '-preset', 'ultrafast',
                    '-tune', 'stillimage',
                    '-c:a', 'aac',
                    '-b:a', '192k',
                    '-pix_fmt', 'yuv420p',
                    '-shortest',  # End when audio ends
                    '-fflags', '+shortest',
                    '-max_interleave_delta', '100M',
                    '-movflags', '+faststart',  # Better compatibility
                    '-y',
                    str(output_path)
                ]
            else:
                # With solid color background matching exact audio duration
                # Use 25 fps for better compatibility with media players
                cmd = [
                    'ffmpeg',
                    '-i', str(input_path),  # Audio input FIRST
                    '-f', 'lavfi',
                    '-i', 'color=c=black:s=1280x720:r=25',  # 25 fps for compatibility
                    '-map', '1:v',  # Map video from color filter (input 1)
                    '-map', '0:a',  # Map audio from file (input 0)
                    '-c:v', 'libx264',
                    '-preset', 'ultrafast',  # Fast encoding
                    '-c:a', 'aac',
                    '-b:a', '192k',
                    '-pix_fmt', 'yuv420p',
                    '-shortest',  # Match audio duration
                    '-movflags', '+faststart',  # Better compatibility
                    '-y',
                    str(output_path)
                ]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # Check if conversion was successful
            if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
                print(f"[OK] Successfully converted: {input_path.name} -> {output_path.name}")
                print(f"[OK] Output file size: {output_path.stat().st_size} bytes")
                return f"[OK] Successfully converted: {output_path.name}"
            else:
                error_msg = result.stderr[-500:] if result.stderr else "Unknown error"
                print(f"[ERROR] MP3->MP4 FFmpeg failed for {input_path.name}")
                print(f"[ERROR] Command: {' '.join(cmd)}")
                print(f"[ERROR] Return code: {result.returncode}")
                print(f"[ERROR] Output file exists: {output_path.exists()}")
                if output_path.exists():
                    print(f"[ERROR] Output file size: {output_path.stat().st_size} bytes")
                print(f"[ERROR] FFmpeg stderr: {error_msg}")
                print(f"[ERROR] FFmpeg stdout: {result.stdout[-500:] if result.stdout else 'None'}")
                return f"[FAIL] Failed to convert: {input_path.name} - Check logs for details"
                
        except Exception as e:
            print(f"[ERROR] Exception in MP3->MP4 conversion: {str(e)}")
            return f"[ERROR] Error converting {input_path.name}: {str(e)}"
    
    def batch_convert(self, input_paths, output_dir=None, bitrate='192k', max_workers=4, 
                     conversion_type='mp4_to_mp3', image_path=None):
        """Convert multiple files concurrently (supports both MP4→MP3 and MP3→MP4)"""
        files = []
        
        # Collect all files
        for path in input_paths:
            path_obj = Path(path)
            if path_obj.is_file():
                files.append(path_obj)
            elif path_obj.is_dir():
                if conversion_type == 'mp4_to_mp3':
                    # Find all video files in directory
                    video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.flv', '.webm']
                    for ext in video_extensions:
                        files.extend(path_obj.glob(f'*{ext}'))
                        files.extend(path_obj.glob(f'*{ext.upper()}'))
                else:  # mp3_to_mp4
                    # Find all audio files in directory
                    audio_extensions = ['.mp3', '.m4a', '.aac', '.wav', '.flac', '.ogg']
                    for ext in audio_extensions:
                        files.extend(path_obj.glob(f'*{ext}'))
                        files.extend(path_obj.glob(f'*{ext.upper()}'))
        
        if not files:
            file_type = "video" if conversion_type == 'mp4_to_mp3' else "audio"
            print(f"[ERROR] No {file_type} files found!")
            return
        
        print(f"\n>> Found {len(files)} file(s) to convert")
        print(f"🚀 Using {max_workers} parallel workers\n")
        
        # Convert files concurrently
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            if conversion_type == 'mp4_to_mp3':
                futures = {
                    executor.submit(self.convert_mp4_to_mp3, str(file), output_dir, bitrate): file 
                    for file in files
                }
            else:  # mp3_to_mp4
                futures = {
                    executor.submit(self.convert_mp3_to_mp4, str(file), output_dir, image_path): file 
                    for file in files
                }
            
            for future in as_completed(futures):
                result = future.result()
                print(result)
        
        print(f"\n>> Batch conversion complete!")
    
    def download_youtube(self, url, output_dir='.', format_type='video', quality='best', progress_callback=None):
        """Download YouTube video or audio with progress tracking"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Progress hook for tracking download
        def progress_hook(d):
            if progress_callback and d['status'] == 'downloading':
                # Extract progress information
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                speed = d.get('speed', 0)
                eta = d.get('eta', 0)
                
                # Call the callback with progress info
                progress_callback({
                    'downloaded_bytes': downloaded,
                    'total_bytes': total,
                    'speed': speed,
                    'eta': eta,
                    'percent': (downloaded / total * 100) if total > 0 else 0
                })
        
        # Configure yt-dlp options
        if format_type == 'audio' or format_type == 'mp3':
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': str(output_path / '%(title)s.%(ext)s'),
                'quiet': False,
                'no_warnings': False,
                'progress_hooks': [progress_hook] if progress_callback else [],
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-us,en;q=0.5',
                    'Sec-Fetch-Mode': 'navigate',
                },
            }
        else:
            # Video download
            if quality == 'best':
                format_str = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            elif quality == '1080p':
                format_str = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]'
            elif quality == '720p':
                format_str = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]'
            elif quality == '480p':
                format_str = 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]'
            else:
                format_str = 'best'
            
            ydl_opts = {
                'format': format_str,
                'outtmpl': str(output_path / '%(title)s.%(ext)s'),
                'merge_output_format': 'mp4',
                'quiet': False,
                'no_warnings': False,
                'progress_hooks': [progress_hook] if progress_callback else [],
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-us,en;q=0.5',
                    'Sec-Fetch-Mode': 'navigate',
                },
            }
        
        try:
            print(f">> Downloading from: {url}")
            print(f">> Output directory: {output_path.absolute()}")
            print(f">> Format: {format_type} | Quality: {quality}\n")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'Unknown')
                print(f"\n[SUCCESS] Downloaded: {title}")
                
        except Exception as e:
            print(f"[ERROR] Download failed: {str(e)}")
    
    def batch_download(self, urls, output_dir='.', format_type='video', quality='best'):
        """Download multiple URLs"""
        print(f"\n>> Downloading {len(urls)} item(s)\n")
        
        for i, url in enumerate(urls, 1):
            print(f"\n{'='*60}")
            print(f"[{i}/{len(urls)}] Processing: {url}")
            print('='*60)
            self.download_youtube(url, output_dir, format_type, quality)
        
        print(f"\n>> All downloads complete!")


def main():
    parser = argparse.ArgumentParser(
        description='Media Tool - Convert MP4 to MP3 & Download YouTube Videos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert single file
  python3 media_tool.py convert video.mp4
  
  # Convert multiple files
  python3 media_tool.py convert video1.mp4 video2.mp4 video3.mp4
  
  # Convert all MP4s in a directory
  python3 media_tool.py convert /path/to/videos/
  
  # Convert with custom output directory and bitrate
  python3 media_tool.py convert video.mp4 -o output/ -b 320k
  
  # Download YouTube video
  python3 media_tool.py download "https://www.youtube.com/watch?v=VIDEO_ID"
  
  # Download as MP3
  python3 media_tool.py download "https://www.youtube.com/watch?v=VIDEO_ID" -f mp3
  
  # Download multiple URLs
  python3 media_tool.py download url1 url2 url3 -f video -q 1080p
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Convert command
    convert_parser = subparsers.add_parser('convert', help='Convert between audio and video formats')
    convert_parser.add_argument('files', nargs='+', help='Input file(s) or directory')
    convert_parser.add_argument('-o', '--output', help='Output directory')
    convert_parser.add_argument('-t', '--type', choices=['mp4_to_mp3', 'mp3_to_mp4'],
                               default='mp4_to_mp3', help='Conversion type (default: mp4_to_mp3)')
    convert_parser.add_argument('-b', '--bitrate', default='192k', 
                               help='Audio bitrate for MP4→MP3 (default: 192k)')
    convert_parser.add_argument('-i', '--image', help='Background image for MP3→MP4 conversion')
    convert_parser.add_argument('-w', '--workers', type=int, default=4,
                               help='Number of parallel workers (default: 4)')
    
    # Download command
    download_parser = subparsers.add_parser('download', help='Download YouTube videos/audio')
    download_parser.add_argument('urls', nargs='+', help='YouTube URL(s)')
    download_parser.add_argument('-o', '--output', default='.', 
                                help='Output directory (default: current)')
    download_parser.add_argument('-f', '--format', choices=['video', 'audio', 'mp3'],
                                default='video', help='Download format (default: video)')
    download_parser.add_argument('-q', '--quality', 
                                choices=['best', '1080p', '720p', '480p'],
                                default='best', help='Video quality (default: best)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Initialize tool
    tool = MediaTool()
    
    # Execute command
    if args.command == 'convert':
        tool.batch_convert(
            args.files, 
            args.output, 
            args.bitrate,
            args.workers,
            args.type,
            args.image
        )
    
    elif args.command == 'download':
        tool.batch_download(
            args.urls,
            args.output,
            args.format,
            args.quality
        )


if __name__ == '__main__':
    main()

