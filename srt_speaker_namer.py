import re
import os

def main():
    # Prompt for the SRT file
    srt_file = input("Please enter the path to the SRT file: ")

    # Read the SRT file
    with open(srt_file, 'r', encoding='utf-8') as file:
        srt_data = file.read()

    # Find the number of unique speakers in the SRT file
    speaker_numbers = set(re.findall(r'Speaker (\d+):', srt_data))
    num_speakers = len(speaker_numbers)

    # Ask for confirmation
    print(f"Found {num_speakers} unique speakers.")
    confirm = input("Do you want to proceed? (yes/no) ")
    if confirm.lower() != 'yes':
        print("Aborted.")
        return

    # Prompt for speaker names
    speaker_names = {}
    for speaker_number in speaker_numbers:
        speaker_name = input(f"Please enter a name for Speaker {speaker_number}: ")
        speaker_names[speaker_number] = speaker_name

    # Replace speaker numbers with speaker names
    for speaker_number, speaker_name in speaker_names.items():
        srt_data = srt_data.replace(f"Speaker {speaker_number}:", speaker_name + ":")

    # Save new SRT file
    new_srt_file = os.path.splitext(srt_file)[0] + "_withNames.srt"
    with open(new_srt_file, 'w', encoding='utf-8') as file:
        file.write(srt_data)

    print(f"New SRT file saved as {new_srt_file}")


if __name__ == "__main__":
    main()
