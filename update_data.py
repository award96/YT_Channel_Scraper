"""update all files in the 'OUTPUT_PATH' directory with new videos.

For each file in the 'OUTPUT_PATH' directory, open them and find up to 10 sample videos IDs
(in case one or more videos have been deleted). Use the video IDs to find the channel ID.
The first video ID which returns an API request will be the 'first video'. Any videos
uploaded before that 'first video' will be added to the top of the csv file.

Attributes:
    Imported from channel_scraper
"""


import requests
import json
import csv
import os
from finish_data import get_file_list
from channel_scraper import *

def update_all_data(OUTPUT_PATH):
    """For each file in the 'OUTPUT_PATH' directory, open the file
    and find the first video that has not been deleted. Use that 'first_vid_id'
    to make an API request to find the channel link. Make an API request to get
    all uploads by the channel, and only record up to the 'first_vid_id'. Add
    those new uploads to the top of the csv file in the same directory.

    Args:
        OUTPUT_PATH (str): The directory where the completed data should go.
    Returns:
        None
    Output:
        csv files will now be up to date.
    """

    print("\n\nstarting update_all_data")
    file_list = get_file_list(OUTPUT_PATH)
    for file in file_list:
        print(f"\nOn file {file}")
        vid_id_list = get_first_vid_id(file)
        channel_link, first_vid_id = get_channel_link(vid_id_list)
        new_vid_list = find_new_channel_vids(channel_link, first_vid_id)
        for finished_vid_list in datamine_channel(new_vid_list):
            print(f"\nlen(new_vid_list) = {len(new_vid_list)}")
            csv_updater(finished_vid_list,file)

def find_new_channel_vids(channel_link, first_vid_id):

    # Very similar functionality to find_channel_vids in channel_scraper.py
    playlist_id, channel_id = request_channel_list_response(channel_link)
    video_items = []
    next_page_token = '&'
    found = False
    while not found:
        new_video_items, next_page_token, channel_name = find_all_uploads(playlist_id, next_page_token)
        video_items += new_video_items
        found, video_items = check_vid_id(video_items, first_vid_id)

        if len(video_items)%500 == 0:
            print(f"\n{len(video_items)} new videos found... looking for more")

    print(f"\n{len(video_items)} new videos found")
    vid_list = []
    for item in video_items:
        vid_id, title, date, thumbnail = json_parse(item,playlist_items = True)
        vid_list.append(Video(vid_id,title,date,thumbnail))
    return vid_list

def check_vid_id(video_items, first_vid_id):

    for i in range(len(video_items)):
        vid_id = video_items[i]['snippet']['resourceId']['videoId']
        if vid_id == first_vid_id:
            return True, video_items[:i]
    return False, video_items


def get_channel_link(vid_id_list, counter = 0):

    api_link = "https://www.googleapis.com/youtube/v3/videos?part=snippet" \
               f"&id={vid_id_list[counter]}&key={API_KEY}"
    video_snippet_response = requests.get(api_link).json()
    try:
        channel_id = video_snippet_response['items'][0]['snippet']['channelId']
    except IndexError:
        print(f"\n\nIndexError\ncounter = {counter}")
        return get_channel_link(vid_id_list,counter = counter + 1)
    channel_link = "https://www.youtube.com/channel/" + channel_id
    return channel_link, vid_id_list[counter]

def get_first_vid_id(filename):

    with open(filename,'r') as file:
        header_line = file.readline()
        counter = 0
        vid_id_list = [] # necessary to have mulitple vid_id's
                         # in case the channel has deleted videos
        for line in file:
            vid_id_list.append(line.split(",",1)[0])
            if counter > 9:
                return vid_id_list
        return vid_id_list
        

def csv_updater(finished_vid_list, filepath):
    row_list = []

    with open(filepath,'r') as file:
        for line in file:
            row_list.append(line)
    temp_filepath = filepath.rsplit(".",1)[0] + "__temp.csv"

    with open(temp_filepath, 'w') as file:
        writer = csv.writer(file)
        file.write(row_list[0])
        for vid in finished_vid_list:
            vid_data = vid.get_data()
            writer.writerow(vid_data)
        file.writelines(row_list[1:])
    os.remove(filepath)
    os.rename(temp_filepath, filepath)



if __name__ == "__main__":
    API_KEY = get_api_key()
    update_all_data(OUTPUT_PATH)
    print(f"\n\nAll files in directory:  {OUTPUT_PATH}  updated")
