# Get audio file from youtube link

$ youtube-dl -x --postprocessor-args "-t 00:10:00" --audio-format wav -o "<OUTPUT_FILE.wav" "<YOUTUBE_LINK>"
