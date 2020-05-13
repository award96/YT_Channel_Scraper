# YouTube Channel Scraper

YouTube Channel Scraper uses the YouTube Data API to scrape relevant information on every youtube video for a channel. It is designed to take in a text file which lists YouTube channel links, and create a csv file for each channel. Each row of the csv file will be a singular video. 

A dataset created with this project can be found at: https://www.kaggle.com/andersward/youtube-video-statistics

## Prerequisites

### API key

A YouTube Data API key is necessary to make API requests. You can access the Google API dashboard [here](https://console.developers.google.com/apis/dashboard) and the YouTube Data API [here](https://developers.google.com/youtube/v3)

### Requests Module

The requests module is necessary to run the python script.

## Usage

First, write a text file where each line is a link to a YouTube channel (or use the given text file).


### channel_scraper.py
Generate data on each video for the channels linked in a text file
The Python script takes the following parameters:

OPTIONAL

* `API_KEY_PATH` the filepath for the text file where the first line is your API key, by default "api_key.txt
* `CHANNEL_LINKS_TEXT_FILEPATH` the filepath for the text file containing YouTube channel links, by default "channel_links.txt"
* `OUTPUT_PATH` the directory where the scraper should put completed data, by default "data/"
* `UNFINISHED_PATH` the directory where the scraper should put data before the scrape of the channel is complete. Data left in the unfinished_path will not have all of the videos by a channel, so it will be necessary to finish datamining that channel. By default "data/unfinished/"
* `MAX_VIDEOS` the maximum number of videos to datamine before writing the data in a csv. In the case of a lost internet connection or running out of quota for your API key, it is nice to mitigate the amount of lost data.
* `RELEVANT_DATA` the data (aside from id, title, date, and thumbnail url) that will be written in the csv file. Each API request includes all of the default data so it does not cost more quota to keep all of the default values. By default [ 'viewCount', 'likeCount', 'dislikeCount', 'commentCount' ]

channel_scraper will run until the API key has ran out of requests or all of the listed channel links have been datamined. Once it is complete, all of the channels that were completely mined will be in the OUTPUT_PATH directory, and all of the channels that were partially mined will be in the UNFINISHED_PATH directory. The data will be a csv file for each channel. The csv file will have a header. 

### finish_data.py
By importing functions from channel_scraper.py, continue where the data left off for each csv file in the `UNFINISHED_PATH` directory.

### update_data.py
By importing functions from channel_scraper.py, update all with the most recent videos for each csv file in the `OUTPUT_PATH` directory.


## License
This project is licensed under the GNU GPLv3 License - see the License.txt file for details