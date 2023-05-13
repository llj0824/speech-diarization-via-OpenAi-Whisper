import re
import pandas as pd
from datetime import datetime
from functools import reduce

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

## Section 1 - Speech Duration ##
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
print("\nSpeaker duration as % of total audio file:")
print(speaker_duration_percentage.round(2).astype(str) + " %")

print("Speaker aggregate duration (in seconds):")
print(speaker_duration.round(2).astype(str) + " seconds")



## Section 2 - Speech Rate ##
# Function to count words in a text
def word_count(text):
    return len(text.split())

# Apply the word_count function to the 'Text' column
df['WordCount'] = df['Text'].apply(word_count)

# Calculate the total number of words spoken by each speaker
speaker_wordcount = df.groupby('Speaker')['WordCount'].sum()

# Calculate the speech rate (words per minute) for each speaker
speaker_speech_rate = (speaker_wordcount / speaker_duration) * 60

print("\nSpeech rate (words per minute):")
print(speaker_speech_rate.round(2).astype(str) + " words per minute")

## Section 3 - Filler words ##
filler_words = [
    'um',
    'uh',
    'like',
    'you know',
    'so',
    'literally',
    'I mean',
    'well',
    'I think'
]

# Function to count the occurrences of filler words in a text
def count_filler_words(text):
    count = {}
    words = text.split()
    for word in words:
        if word.lower() in filler_words:
            count[word.lower()] = count.get(word.lower(), 0) + 1
    return count

# Function to merge two dictionaries
def merge_dicts(a, b):
    result = a.copy()
    for key, value in b.items():
        result[key] = result.get(key, 0) + value
    return result

# Apply the count_filler_words function to the 'Text' column
df['FillerWordCounts'] = df['Text'].apply(count_filler_words)

# Aggregate the filler word counts per speaker
speaker_filler_word_counts = df.groupby('Speaker')['FillerWordCounts'].apply(lambda x: reduce(merge_dicts, x))

# Convert the dictionary to a DataFrame
filler_word_counts_df = pd.DataFrame(list(speaker_filler_word_counts.items()), columns=['Speaker', 'Words'])

# Print the table
print("\nOccurrences of filler words per speaker:")
print(filler_word_counts_df)