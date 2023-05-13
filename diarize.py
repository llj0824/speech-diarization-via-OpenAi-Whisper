# Import necessary libraries and modules
import argparse
import os
from helpers import *
from whisper import load_model
import whisperx
import torch
import librosa
import soundfile
from nemo.collections.asr.models.msdd_models import NeuralDiarizer
from deepmultilingualpunctuation import PunctuationModel
import re
import time

# Initialize argument parser
parser = argparse.ArgumentParser()
parser.add_argument(
    "-a", "--audio", help="name of the target audio file", required=True
)
parser.add_argument(
    "--no-stem",
    action="store_false",
    dest="stemming",
    default=True,
    help="Disables source separation."
    "This helps with long files that don't contain a lot of music.",
)

parser.add_argument(
    "--whisper-model",
    dest="model_name",
    default="large",
    help="name of the Whisper model to use",
)

# Parse command-line arguments
args = parser.parse_args()

# Perform source separation if enabled
source_seperation_start_time = time.time()
if args.stemming:
    # Isolate vocals from the rest of the audio
    return_code = os.system(
        f'python3 -m demucs.separate -n htdemucs --two-stems=vocals "{args.audio}" -o "temp_outputs"'
    )

    if return_code != 0:
        print(
            "Source splitting failed, using original audio file. Use --no-stem argument to disable it."
        )
        vocal_target = args.audio
    else:
        temp_file_path= os.path.splitext(os.path.basename(args.audio))[0]
        vocal_target = f"temp_outputs/htdemucs/{temp_file_path}/vocals.wav"
else:
    vocal_target = args.audio
source_seperation_end_time = end_time = time.time()
print_time_usage(
  start_time = source_seperation_start_time,
  end_time = source_seperation_end_time,
  description= "Vocal Seperation from Audio"
)

# Load the Whisper ASR model and transcribe the audio
whisper_model = trace_time_usage(load_model, args.model_name)
whisper_results = trace_time_usage(whisper_model.transcribe, vocal_target, beam_size=None, verbose=False)

# Clear GPU memory
del whisper_model
torch.cuda.empty_cache()

# Load the Whisper alignment model and align words with timestamps
device = "cuda" if torch.cuda.is_available() else "cpu"
alignment_model, metadata = whisperx.load_align_model(
    language_code=whisper_results["language"], device=device
)
result_aligned = whisperx.align(
    whisper_results["segments"], alignment_model, metadata, vocal_target, device
)

# Clear GPU memory
del alignment_model
torch.cuda.empty_cache()

# Convert audio to mono for NeMo compatibility
signal, sample_rate = librosa.load(vocal_target, sr=None)
ROOT = os.getcwd()
temp_path = os.path.join(ROOT, "temp_outputs")
if not os.path.exists(temp_path):
    os.mkdir(temp_path)
os.chdir(temp_path)
soundfile.write("mono_file.wav", signal, sample_rate, "PCM_24")

# Initialize NeMo MSDD diarization model and perform diarization
config = create_config()

if device == "cpu":
    config.num_workers = 0

neural_diarizer_start_time = time.time()
msdd_model = NeuralDiarizer(cfg=config).to(device)
msdd_model.diarize()
neural_diarizer_end_time = time.time()
print_time_usage(
  start_time = neural_diarizer_start_time,
  end_time = neural_diarizer_end_time,
  description= "Neural diarizer processing"
)

# Clear GPU memory
del msdd_model
torch.cuda.empty_cache()

# Read speaker timestamps and labels from the output file
output_dir = "nemo_outputs"

speaker_ts = []
with open(f"{output_dir}/pred_rttms/mono_file.rttm", "r") as f:
    lines = f.readlines()
    for line in lines:
        line_list = line.split(" ")
        s = int(float(line_list[5]) * 1000)
        e = s + int(float(line_list[8]) * 1000)
        speaker_ts.append([s, e, int(line_list[11].split("_")[-1])])

# Map words to speakers using timestamps
wsm = get_words_speaker_mapping(result_aligned["word_segments"], speaker_ts, "start")

# Restore punctuation in the transcript if the language is supported
if whisper_results["language"] in punct_model_langs:
    # Load punctuation model
    punct_model = PunctuationModel(model="kredor/punctuate-all")

    # Get list of words from the word-speaker mapping
    words_list = list(map(lambda x: x["word"], wsm))

    # Predict punctuation for the words
    labled_words = punct_model.predict(words_list)

    # Add predicted punctuation to the words in the word-speaker mapping
    ending_puncts = ".?!"
    model_puncts = ".,;:!?"

    # Function to check if a word is an acronym
    is_acronym = lambda x: re.fullmatch(r"\b(?:[a-zA-Z]\.){2,}", x)

    for word_dict, labeled_tuple in zip(wsm, labled_words):
        word = word_dict["word"]
        if (
            word
            and labeled_tuple[1] in ending_puncts
            and (word[-1] not in model_puncts or is_acronym(word))
        ):
            word += labeled_tuple[1]
            if word.endswith(".."):
                word = word.rstrip(".")
            word_dict["word"] = word

    # Realign word-speaker mapping with punctuation
    wsm = get_realigned_ws_mapping_with_punctuation(wsm)
else:
    print(
        f'Punctuation restoration is not available for {whisper_results["language"]} language.'
    )

# Get sentence-speaker mapping from the word-speaker mapping
ssm = get_sentences_speaker_mapping(wsm, speaker_ts)

# Change back to the parent directory
os.chdir(ROOT)

# Write speaker-aware transcript to a text file
with open(f"{args.audio[:-4]}.txt", "w", encoding="utf-8-sig") as f:
    get_speaker_aware_transcript(ssm, f)

# Write speaker-aware subtitles to an SRT file
with open(f"{args.audio[:-4]}.srt", "w", encoding="utf-8-sig") as srt:
    write_srt(ssm, srt)

# Clean up temporary files and directories
cleanup(temp_path)