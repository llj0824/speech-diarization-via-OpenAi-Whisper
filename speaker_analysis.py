import re
import pandas as pd
from datetime import datetime

# Ask the user for the input file path
file_path = input("Please enter the path to the .srt file: ")

# Initialize the list to store data
data = []

# Open and read the file
with open(file_path, 'r') as file:
    content = file.read()
    blocks = content.split('\n\n')

    # Loop through each block and parse the data
    for block in blocks:
        # Split the block into lines
        lines = block.split('\n')
        if len(lines) >= 3:
            # The first line is the index, second line is the time, and the remaining lines are the text
            index = lines[0]
            time = lines[1]
            text = ' '.join(lines[2:])

            # Use regex to find the speaker's name in the text
            match = re.match(r'(.*): (.*)', text)
            if match:
                speaker, text = match.groups()
            else:
                speaker = 'Unknown'

            # Append the data to the list
            data.append([index, time, speaker, text])

# Convert the list into a DataFrame
df = pd.DataFrame(data, columns=['Index', 'Time', 'Speaker', 'Text'])

## Speech Duration ##
# Function to calculate the duration in seconds from a time range string
def calculate_duration(time_range):
    start_time_str, end_time_str = time_range.split(' --> ')
    start_time = datetime.strptime(start_time_str, '%H:%M:%S,%f')
    end_time = datetime.strptime(end_time_str, '%H:%M:%S,%f')
    return (end_time - start_time).total_seconds()

# Apply the function to the 'Time' column
df['Duration'] = df['Time'].apply(calculate_duration)

# Group by speaker and sum the duration
speaker_duration = df.groupby('Speaker')['Duration'].sum()

# Calculate the total duration of the audio file
total_duration = df['Duration'].sum()

# Calculate the speaker_duration as % of total audio file
speaker_duration_percentage = (speaker_duration / total_duration) * 100

# Display the results
print("Speaker duration (in seconds):")
print(speaker_duration.round(2).astype(str) + " seconds")

print("\nSpeaker duration as % of total audio file:")
print(speaker_duration_percentage.round(2).astype(str) + " %")


## Speech Rate ##
# Function to count words in a text
def word_count(text):
    return len(text.split())

# Apply the word_count function to the 'Text' column
df['WordCount'] = df['Text'].apply(word_count)

# Calculate the total number of words spoken by each speaker
speaker_wordcount = df.groupby('Speaker')['WordCount'].sum()

# Calculate the speech rate (words per minute) for each speaker
speaker_speech_rate = (speaker_wordcount / speaker_duration) * 60

# Display the results
print("\nSpeaker word count:")
print(speaker_wordcount)

print("\nSpeech rate (words per minute):")
print(speaker_speech_rate.round(2) + " per minute")