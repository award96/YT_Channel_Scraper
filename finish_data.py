"""Finish data-mining any channels with files in the 'UNFINISHED_PATH'.

For each file in the 'UNFINISHED_PATH' directory, using the video IDs
in the csv file, find the channel. Next, find all videos uploaded by that channel.
Then add any videos to the csv file that are older than the oldest video. Since 
the data is organized chronologically, this will be the last row. Once the channel has
been completed, move the csv file to the 'OUTPUT_PATH' directory.

Attributes:
    Imported from channel_scraper
"""



import requests
import json
import os
from channel_scraper import *


def finish_data(UNFINISHED_PATH):
    """For each file in the 'UNFINISHED_PATH' directory, open the file
    and use the 'last video ID' to make an API request. From the request get
    the channel ID, which is used to find every upload by the channel. Every
    upload after the 'last video ID' will then be appended to the csv file.
    Finally, the file will be moved to the 'OUTPUT_PATH' directory.

    Args:
        UNFINISHED_PATH (str): directory where the unfinished files are stored.

    Returns:
        None
    Output:
        csv files will be completed and moved to the OUTPUT_PATH directory.
    """

    file_list = get_file_list(UNFINISHED_PATH)
    print(f"\nfile_list:\n{file_list}")
    for file in file_list:
        print(f"\n\n\nOn file {file}")
        last_vid_id = get_last_vid_id(file)
        print(f"\nlast_vid_id = {last_vid_id}")
        channel_id = get_channel_id(last_vid_id)
        print(f"\nchannel_id = {channel_id}")
        channel_link = "https://youtube.com/user/" + channel_id
        if len(channel_id) == 24:
            if channel_id.startswith("U"):
                channel_link = "https://youtube.com/channel/" + channel_id
        print(f"\nchannel_link = {channel_link}")
        vid_list, channel_name, channel_id = find_channel_vids(channel_link,
                                                               True)
        print(f"\nfinished find_channel_vids, {len(vid_list)}"\
               " total videos found")
        new_vid_list = remove_finished_videos(vid_list,last_vid_id)
        print(f"\nfinished remove_finished_videos, {len(new_vid_list)}"\
               " videos left to mine")

        for finished_vid_list in datamine_channel(new_vid_list):
            channel_name_and_path = file.rsplit(".",1)[0]
            channel_name = channel_name_and_path.split(UNFINISHED_PATH,1)[1]
            csv_writer(finished_vid_list,channel_name,
                       UNFINISHED_PATH, channel_id)
        move_completed_csv(channel_name, OUTPUT_PATH, UNFINISHED_PATH)
        print(f"\ndone with {channel_name}")

def get_file_list(UNFINISHED_PATH):

    file_list = []
    for file in os.listdir(UNFINISHED_PATH):
        if file.endswith(".csv"):
            file_list.append(os.path.join(UNFINISHED_PATH, file))
    return file_list

def get_last_vid_id(filename):

    with open(filename,'r') as file:
        lines = file.read().splitlines()
        counter = 1
        last_vid_id = lines[-counter].split(",",1)[0]
        while len(last_vid_id) < 10: # in case of empty line
            counter += 1
            last_vid_id = lines[-counter].split(",",1)[0]
        return last_vid_id

def get_channel_id(vid_id):

    link = "https://www.googleapis.com/youtube/v3/videos?" \
            f"part=snippet&id={vid_id}&key={API_KEY}"
    YT_video_list_response = requests.get(link).json()
    channel_id = YT_video_list_response['items'][0]['snippet']['channelId']
    return channel_id

def remove_finished_videos(vid_list,last_vid_id):

    for i in range(len(vid_list)):
        vid_id = vid_list[i].get_vid_id()
        if vid_id == last_vid_id:
            print(f"\nfound last_vid_id = {last_vid_id}")
            return vid_list[i+1:]
    print("\nlast_vid_id never found, returning []")
    return [] # if you never find last_vid_id

if __name__ == "__main__":
    API_KEY = get_api_key()
    print("\n\nStarting channel_finisher.py")
    finish_data(UNFINISHED_PATH)
    print("\n\nAll files completed")