"""Write a csv file for each YouTube channel in a text file.

channel_scraper opens a text file where each line is a YouTube channel link,
finds all the videos uploaded by that channel, and gathers data on each video.
It will write one csv file per channel, each row of the csv file is a video, 
ordered from newest to oldest.

File Writing:
    To prevent loss of data in the case that the module loses internet
    connection or the API key runs out of quota, this module will write
    a channel's data in the csv file every 'MAX_VIDEOS' number of videos,
    or when the channel is completely data-mined. 
    To highlight that an unfinished csv file does not contain every
    video by a channel, the module will write the csv file in the
    'UNFINISHED_PATH' until the channel is completed, 
    at which point it will move the file to he 'OUTPUT_PATH'.

    To complete an unfinished channel use the finish_data.py module.
    To update data use the update_data.py module.

Attributes:
    API_KEY_PATH (str): 
        The filepath for a .txt file where the first line is your API key. 

    CHANNEL_LINKS_TEXT_FILEPATH (str): 
        The filepath for a .txt file where each line is a link to 
        a YouTube channel.

    OUTPUT_PATH (str):
        The directory where the completed data should go. 
    
    UNFINISHED_PATH (str):
        The directory where the incomplete data should go.
    
    COMPLETED_LINKS_FILEPATH (str):
        The filepath to a .txt file which contains the links
        to all channels which have been partially or fully
        data-mined. This is necessary to prevent duplicate data.
    
    MAX_VIDEOS (int):
        The number of videos the module should datamine at a time before
        writing the data to a csv file. It should be noted that the module
        will always write the csv file when it completes a channel.
    
    RELEVANT_DATA (list of str):
        The data that json_parse() should look for. Metrics can be removed
        if they are not deemed relevant to write to the csv file. Removing a
        metric will not save API quota cost. 



"""


import csv
import json
import os
import requests
import sys

# variables
API_KEY_PATH = "api_key.txt"
CHANNEL_LINKS_TEXT_FILEPATH = "channel_links.txt"
OUTPUT_PATH = "data/"
UNFINISHED_PATH = "data/unfinished/"
COMPLETED_LINKS_FILEPATH = "completed_channel_links.txt"

MAX_VIDEOS = 500
RELEVANT_DATA = [  'viewCount', 'likeCount', 'dislikeCount', 'commentCount' ]


# main functions

def datamine_multiple_channels(CHANNEL_LINKS_TEXT_FILEPATH, 
                               OUTPUT_PATH, UNFINISHED_PATH):
    """ For each channel link in the CHANNEL_LINKS_TEXT_FILEPATH create
    a csv for that channel. Each row of the csv is a video by that channel, 
    columns contain basic information (id, title, date, thumbnail link)
    as well as the data included in RELEVANT_DATA. The rows are ordered from 
    newest to oldest video.

    Args:
        CHANNEL_LINKS_TEXT_FILEPATH (str): filepath to a .txt file where each
                                           line of the file is a link to a
                                           youtube channel.

        OUTPUT_PATH (str): the directory path where the finished data 
                           should be put.

        UNFINISHED_PATH (str): the directory path where the unfinished data
                               should be put. 
    Returns:
        None
    Output:
        writes a .csv file named after the channel name.
    """

    print("\ndatamine_multiple_channels is being called")
    channel_link_list = read_channel_link_file(CHANNEL_LINKS_TEXT_FILEPATH)
    counter = 0
    for channel in channel_link_list:
        counter += 1
        print(f"\n\n\nchannel link is {channel}, we are on channel {counter} "\
              f"of {len(channel_link_list)}")

        vid_list, channel_name, channel_id = find_channel_vids(channel) 
        # vid_list will be None if 
        # the channel appears in COMPLETED_LINKS_FILEPATH.                                                                
        if not vid_list:                                                
            remove_completed_channel(CHANNEL_LINKS_TEXT_FILEPATH)
            continue 

        for finished_vid_list in datamine_channel(vid_list):
            print(f"\nlen(vid_list) = {len(vid_list)}")
            csv_writer(finished_vid_list,channel_name,
                       UNFINISHED_PATH, channel_id)
        print(f"\ndone with {channel}")
        move_completed_csv(channel_name,OUTPUT_PATH,UNFINISHED_PATH)


def find_channel_vids(channel_link, 
                      called_from_finish_data = False):

    playlist_id, channel_id = request_channel_list_response(channel_link)
    # Appending to existing data should always be done with
    # finish_data.py , this block prevents duplicate data.
    if not called_from_finish_data:
        already_mined = prevent_duplicate_data(channel_id,  
                                               COMPLETED_LINKS_FILEPATH)
        if already_mined:
            return None, None, None

    video_items = [] # list of json data, each index is a video
    next_page_token = '&' # initiate with a "blank" next page token
    while next_page_token:
        new_video_items, next_page_token, channel_name = find_all_uploads(
                                                              playlist_id, 
                                                              next_page_token)
        video_items += new_video_items
        if len(video_items) % 500 == 0:
            print(f"\n{len(video_items)} videos found... looking for more")

    vid_list = [] # list of video objects initialized with basic information.
    for item in video_items:
        vid_id, title, date, thumbnail = json_parse(item,
                                                    playlist_items = True)
        vid_list.append(Video(vid_id,title,date,thumbnail))
    return vid_list, channel_name.replace(" ","_"), channel_id

def datamine_channel(vid_list):
    # Generator to take video objects with basic info and make
    # a 'statistics' request on them.
    finished_list = []
    counter = 0
    for vid in vid_list:

        counter += 1
        if counter%50 == 0:
            print(f"on video {counter} of {len(vid_list)}")
        # for each video gather statistics not present in playlist itemlist
        finished_list.append(datamine_video(vid)) 

        if len(finished_list) > MAX_VIDEOS: # prevent data loss
            print(f"\n{counter} videos mined, writing to csv file")
            yield finished_list
            finished_list = []
    print(f"\nAll {len(finished_list)} videos mined, writing to csv file")
    yield finished_list


# API request functions

def request_channel_list_response(channel_link):

    api_key = get_api_key()
    if "user" in channel_link:
        user_id = channel_link.split("user/",1)[-1]
        idTag = "forUsername=" + user_id
    else:
        channel_id = channel_link.split("channel/",1)[-1]
        idTag = "id=" + channel_id
    request_link = ("https://www.googleapis.com/youtube/v3/channels?" \
                    f"part=contentDetails&{idTag}&key={api_key}")

    yt_channel_list_response = requests.get(request_link).json()
    try:
        playlist_id = yt_channel_list_response['items'] \
                                              [0]['contentDetails'] \
                                              ['relatedPlaylists']['uploads']
    except (KeyError, IndexError):
        description = "Error getting playlist_id from" \
                      "yt_channel_list_response in function" \
                      "request_channel_list_response" \
                      f"\nThe API request link used was {request_link}"
        error_handler(yt_channel_list_response,api_key,description)

    channel_id = yt_channel_list_response['items'][0]['id']
    return playlist_id, channel_id

def find_all_uploads(playlist_id,next_page_token):

    api_key = get_api_key()
    request_link = ("https://www.googleapis.com/youtube/v3/" \
                    f"playlistItems?part=snippet&playlistId={playlist_id}&key"\
                    f"={api_key}&maxResults=50&pageToken={next_page_token}")

    yt_playlist_itemlist = requests.get(request_link).json()
    try:
        channel_name = yt_playlist_itemlist['items'][0] \
                                           ["snippet"]['channelTitle'] 
    except (KeyError, IndexError):
        description = "Error getting channel name from yt_playlist_itemlist"\
                      "in function find_all_uploads"\
                      f"\nThe API request link used was {request_link}"
        error_handler(yt_playlist_itemlist,api_key,description)

    try:
        next_page_token = yt_playlist_itemlist["nextPageToken"]
    except KeyError:
        # No nextPageToken means we have found all the uploads
        next_page_token = None 

    new_video_items = yt_playlist_itemlist['items'] 
    return new_video_items,next_page_token,channel_name

def datamine_video(video_object):

    api_key = get_api_key()
    vid_id = video_object.get_vid_id()
    api_link = "https://www.googleapis.com/youtube/v3/videos?"\
                f"part=statistics&id={vid_id}&key={api_key}"
    newRequest = requests.get(api_link)
    if newRequest.status_code == 429:
        print("status_code 429, too_many_requests")
        sys.exit()
    newData = json_parse(newRequest.json()) # RELEVANT_DATA
    video_object.add_data(newData)
    return video_object

# Classes

class Video(object):

    def __init__(
            self, vid_id,
            title, date,
            thumbnail):

        self.id = vid_id
        self.title = title
        self.date = date
        self.thumbnail = thumbnail
        self.data = []

    def get_vid_id(self):
        return self.id
    def add_data(self,data):
        self.data += data # RELEVANT_DATA

    def get_data(self):
        return [self.id, self.title, self.date, self.thumbnail] + self.data

# parsing functions

def json_parse(json_text,playlist_items = False):

    if playlist_items:
        # the function is being called to parse a playlist items response
        vid_id = json_text['snippet']['resourceId']['videoId']
        title = json_text['snippet']['title']
        date = json_text['snippet']['publishedAt']
        try:
            thumbnail = json_text["snippet"]["thumbnails"]["default"]["url"]
        except KeyError:
            thumbnail = ""
        return vid_id, title, date, thumbnail

    # the function is being called to parse a video statistics response
    data = []
    try:
        stats = json_text["items"][0]['statistics']
    except KeyError:
        description = "Error retrieving stats from" \
                      "json_text in function json_parse"
        api_key = get_api_key()
        error_handler(json_text, api_key, description)
    for dataItem in RELEVANT_DATA:
        try:
            data.append(stats[dataItem])
        except KeyError:
            print(f"\nThe request did not retrieve {dataItem}, "\
                f"likely because {dataItem} was disabled for this video"\
                f"\n{dataItem} will be set to -1")
            data.append(-1)
    return data


# reading and writing file functions

def csv_writer(vid_list, channel_name,
               UNFINISHED_PATH, channel_id):

    filename = UNFINISHED_PATH + channel_name + ".csv"
    try:
        with open(filename, 'r') as test:
            file_exists = True
    except FileNotFoundError:
        file_exists = False
    with open(filename, 'a',newline = '') as file:
        writer = csv.writer(file)
        if not file_exists:
            print("creating new csv file") 
            update_completed_links(channel_id, COMPLETED_LINKS_FILEPATH)
            remove_completed_channel(CHANNEL_LINKS_TEXT_FILEPATH)
            header_line = [ "id", "title", "date", "thumbnail"] + RELEVANT_DATA
            writer.writerow( header_line )
        print(f"writing to {filename}")
        for vid in vid_list:
            vid_data = vid.get_data()
            writer.writerow(vid_data)

def move_completed_csv(channel_name, OUTPUT_PATH, UNFINISHED_PATH):

    with open(UNFINISHED_PATH + channel_name + ".csv","r") as fin:
        channels = fin.read().splitlines(True)
    with open(OUTPUT_PATH + channel_name + ".csv",'w') as fout:
        fout.writelines(channels)
    os.remove(UNFINISHED_PATH + channel_name + ".csv")

def read_channel_link_file(filepath):

    with open(filepath, "r") as file:
        channel_link_list = []
        channel_link_list += [line.rsplit("\n",1)[0] for line in file]
    return channel_link_list

def prevent_duplicate_data(channel_id, COMPLETED_LINKS_FILEPATH):

    with open(COMPLETED_LINKS_FILEPATH, 'r') as file:
        completed_channel_ids = []
        for line in file:
            new_id = line.rsplit("/",1)[1]
            completed_channel_ids.append(new_id.rsplit("\n",1)[0])
        if channel_id in completed_channel_ids:
            print("\n\nThis channel has already been partially" \
                f" or fully mined.\nThe channel id: {channel_id} appears in" \
                f" {COMPLETED_LINKS_FILEPATH}.\nIf the channel link in"   \
                f" {CHANNEL_LINKS_TEXT_FILEPATH} was given as a\n/user/ link"\
                f", the channel id: {channel_id} was found through an API request.")
            return True
        return False

def update_completed_links(channel_id, COMPLETED_LINKS_FILEPATH):
    
    with open(COMPLETED_LINKS_FILEPATH, "a") as file:
        file.write("https://www.youtube.com/channel/"+ channel_id + "\n")
            
def remove_completed_channel(CHANNEL_LINKS_TEXT_FILEPATH):

    with open(CHANNEL_LINKS_TEXT_FILEPATH,"r") as fin:
        channels = fin.read().splitlines(True)
    with open(CHANNEL_LINKS_TEXT_FILEPATH,'w') as fout:
        if len(channels) > 1:
            fout.writelines(channels[1:])
        else:
            fout.writelines([""])

def get_api_key():

    with open(API_KEY_PATH,'r') as file:
        api_key_raw = file.readline()
        if "\n" in api_key_raw:
            api_key = api_key_raw.replace("\n","")
        else:
            api_key = api_key_raw
        return api_key

# other functions

def error_handler(json_text, api_key, description):
    print(f"\n{description}")
    print(f"\nThe api_key used was {api_key}")
    print(f"\nThe problematic json_text is as follows\n{json_text}")


##########################################################

if __name__ == "__main__":

    api_key = get_api_key()
    datamine_multiple_channels(
        CHANNEL_LINKS_TEXT_FILEPATH,
        OUTPUT_PATH, UNFINISHED_PATH)