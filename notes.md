# Get audio file from youtube link
 
$ youtube-dl -f bestaudio -x --no-playlist --external-downloader aria2c --external-downloader-args "-x 16 -s 16 -k 10M" --audio-format wav -o "<OUTPUT_FILE>.%(ext)s" "<YOUTUBE_LINK>"

Note: it seems download speed drastically speeds up by increasing "-k" (buffer size) setting. Default is 1M.

# Get segment of audio file
$ ffmpeg -i {input_file}.wav -t 00:10:00 {output_file}.wav


# Downsampling
1) Turn into mp3 (3mb) instead of wav (100mb)
$ ffmpeg -i {input_file}.wav -codec:a libmp3lame -qscale:a 7 {output}.mp3

