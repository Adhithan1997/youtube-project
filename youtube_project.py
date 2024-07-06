# import the packages
from pprint import pprint
import pandas as pd
import pymongo
import pymysql
import re
import streamlit as st
from datetime import datetime
from streamlit_option_menu import option_menu

# connect youtube api
def api_connect():
  api_key='AIzaSyCXwL1yS826WOCBnrESw7oq0YmtnBsjjuE'
  api_service_name="youtube"
  api_version="v3"
  youtube=build(api_service_name,api_version,developerKey=api_key)
  return youtube

youtube=api_connect()
youtube

# connect mongodb
client = pymongo.MongoClient("mongodb+srv://adhi:adhithan@adhi.hcwg3kf.mongodb.net/?retryWrites=true&w=majority")

# connect mysql
connection = pymysql.connect(
host="localhost",
user="root",
password="adhi",
database="youtube_project"
)

# streamlit Title
st.title(":red[YOUTUBE]" ":blue[ DATA HARVESTING AND WAREHOUSING]") 

selected = option_menu(None, ["Home","collect data in mongodb", "Lode Data In SQL", 'Select the Query'], 
    menu_icon="cast", default_index=0, orientation="horizontal")

        
# Enter the channel Name (input)
channel_name = st.text_input("Enter the channel Name")
request = youtube.search().list(
        part="id,snippet",
        channelType="any",
        maxResults=1,
        q=channel_name,
   )

response=request.execute()

#get channel id
channel_id = response['items'][0]['snippet']['channelId']
print("Channel_id:", channel_id)

# get channel details
def channel_details(youtube,channel_id):
  datas=[]
  request=youtube.channels().list(
      part="snippet,contentDetails,statistics",
      id=channel_id
      
  )
  response=request.execute()

  for item in response['items']: 
    data={'channelName':item['snippet']['title'],
          'channelId':item['id'],
          'subscribers':item['statistics']['subscriberCount'],
          'views':item['statistics']['viewCount'],
          'totalVideos':item['statistics']['videoCount'],
          'playlistId':item['contentDetails']['relatedPlaylists']['uploads'],
          'channel_description':item['snippet']['description']
    }   
  datas.append(data)   
  return datas

#streamlit home code
if selected =="Home":
    step1 = st.button('Submit')
    if step1:
        youtube=api_connect()
        channel_info=channel_details(youtube,channel_id)
        st.write(channel_info)

# get playlist details
def playlist_details(youtube,channel_id):
      all_data=[]
      request = youtube.playlists().list(
                  part="snippet,contentDetails",
                  channelId=channel_id,
                  maxResults=50)
      response = request.execute()

      for item in response['items']: 
                  data={'PlaylistId':item['id'],
                        'Title':item['snippet']['title'],
                        'ChannelId':item['snippet']['channelId'],
                        'ChannelName':item['snippet']['channelTitle'],
                        'PublishedAt':item['snippet']['publishedAt'],
                        'VideoCount':item['contentDetails']['itemCount']}
                  all_data.append(data)
      return all_data

# get videos ids
def videos_ids(youtube,playlist_details):
    video_ids = []
    request = youtube.channels().list(
        id=channel_id, 
        part='contentDetails'
        )
    response=request.execute()
    playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    
    while True:
        request = youtube.playlistItems().list(
            playlistId=playlist_id, 
            part='snippet', 
            maxResults=50
            )
        response=request.execute()
        
        for i in range(len(response['items'])):
            video_ids.append(response['items'][i]['snippet']['resourceId']['videoId'])
        break
    return video_ids

video_ids=videos_ids(youtube,playlist_details)

def convert_duration(duration):
            regex = r'PT(\d+H)?(\d+M)?(\d+S)?'
            match = re.match(regex,duration)
            if not match:
                    return '00:00:00'
            hours,minutes,seconds=match.groups()
            hours=int(hours[:-1])if hours else 0
            minutes=int(minutes[:-1])if minutes else 0
            seconds=int(seconds[:-1])if seconds else 0
            total_seconds=hours*3600+minutes*60+seconds
            return"{:02d}:{:02d}:{:02d}".format(int(total_seconds//3600),int((total_seconds%3600)//60),int(total_seconds%3600)%60)


# get video details
def video_details(youtube,video_ids):
    video_data= []
    for i in range(0, len(video_ids), 50):
        request = youtube.videos().list(
                    part="snippet,contentDetails,statistics",
                    id=video_ids,
                    maxResults=50
        )
        response= request.execute()
        for video in response['items']:
            video_details = dict(Channel_name = video['snippet']['channelTitle'],
                                Channel_id =video['snippet']['channelId'],
                                Video_id =video['id'],
                                Title = video['snippet']['title'],
                                Tags = ",".join(video['snippet'].get('tags',["notags"])),
                                Thumbnail = video['snippet']['thumbnails']['default']['url'],
                                Description = video['snippet']['description'],
                                Published_date = video['snippet']['publishedAt'],
                                Duration = convert_duration(video['contentDetails']['duration']),
                                Views = video['statistics']['viewCount'],
                                Likes = video['statistics'].get('likeCount'),
                                Comments = video['statistics'].get('commentCount'),
                                Favorite_count = video['statistics']['favoriteCount'],
                                Definition = video['contentDetails']['definition'],
                                Caption_status = video['contentDetails']['caption']
                                )
            video_data.append(video_details)
    return video_data

video_details(youtube,video_ids)

# get comments details
def comments_details(youtube,video_ids):
    all_comments = []
    for i in video_ids:
        try:   
            request = youtube.commentThreads().list(
                part="snippet,replies",
                maxResults=20,
                videoId= i
            )
            response = request.execute()
        
            for item in response['items']:
                data={'comment_id':item['snippet']['topLevelComment']['id'],
                    'comment_txt':item['snippet']['topLevelComment']['snippet']['textOriginal'],
                    'videoId':item['snippet']['topLevelComment']["snippet"]['videoId'],
                    'author_name':item['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                    'published_at':item['snippet']['topLevelComment']['snippet']['publishedAt'],
                }
                all_comments.append(data)
            
        except: 
            pass
        
    return all_comments

# all details stored in one function
def full_data(youtube,channel_id):

        c = channel_details(youtube,channel_id)
        p = playlist_details(youtube,channel_id)
        vi= videos_ids(youtube,c[0]['playlistId'])
        v = video_details(youtube,vi)
        cm = comments_details(youtube,vi)

        data = {'channel_details': c,
                'playlist_details': p,
                'video_details': v,
                'comments_details': cm}
        return data         

data=full_data(youtube,channel_id)

# insert full data in mangodb
#project_data = client["youtube"]

#coll=project_data["youtube_data"]

#coll.insert_one(data)

#streamlit insert mongodb code
if selected == 'collect data in mongodb':
    if st.button('Migrate Data to MongoDB'):
        db = client['youtube']
        coll = db['youtube_data']
        coll.insert_one(data)
        st.write(" Data insert completed")
    

#mysql connection
connection = pymysql.connect(
host="localhost",
user="root",
password="adhi",
database="youtube_project"
)
connect_data=connection.cursor()

def create_table():
    connection = pymysql.connect(
    host="localhost",
    user="root",
    password="adhi",
    database="youtube_project"
    )
    connect_data=connection.cursor()
    connect_data.execute("create table if not exists channel_details(\
                                            channel_name		varchar(255),\
                                            channel_id 			varchar(255) ,\
                                            subscription_count	varchar(255),\
                                            views		        varchar(255),\
                                            totalvideos         varchar(255),\
                                            playlist_id		    varchar(255) NOT NULL,\
                                            channel_description	text )")
    connection.commit()

    connect_data.execute("create table if not exists playlist_details(\
                                            playlist_id		 varchar(255),\
                                            Title            varchar(255),\
                                            channel_name	 varchar(255),\
                                            channel_id 		 varchar(255),\
                                            published_date	 varchar(255),\
                                            videosCount		 varchar(255))")
    connection.commit()

    connect_data.execute("create table if not exists video_details(\
                                            channel_name	 text,\
                                            channel_id       text,\
                                            video_id		 varchar(255),\
                                            Title            text,\
                                            tags			 text,\
                                            thumbnail		 text,\
                                            Description	     text,\
                                            published_date	 text,\
                                            Duration         time,\
                                            view_count		 text,\
                                            like_count		 text,\
                                            comment_count	 text,\
                                            favourite_count	 text,\
                                            Definition       text,\
                                            caption_status	 text)")
    connection.commit()

    connect_data.execute("create table if not exists comments_details(\
                                            comment_id			varchar(255),\
                                            comment_text		text,\
                                            video_id			varchar(255),\
                                            author_name			varchar(255),\
                                            published_at	    varchar(255) )")

    connection.commit()

#create_table()

def insert_query():
    query1 = '''INSERT INTO channel_details(channel_name,channel_id,subscription_count,views,totalVideos,playlist_id,channel_description) VALUES (%s, %s, %s,%s, %s, %s,%s);'''
    values1=tuple(data["channel_details"][0].values())
    connect_data.execute(query1,values1)
    connection.commit()

    for i in data['playlist_details']:
        values2=tuple(i.values())
        query2= '''INSERT INTO playlist_details( playlist_id,Title ,channel_name,channel_id ,published_date,videosCount) VALUES (%s, %s, %s,%s, %s, %s);'''
        
        connect_data.execute(query2,values2)

        connection.commit()   
        connection.rollback()

    for i in data["video_details"]:
        values3=tuple(i.values())
        query3= '''INSERT INTO video_details(channel_name,channel_id,video_id,Title,tags,thumbnail,Description,Published_date,Duration,view_count,like_count,comment_count,favourite_count,Definition,caption_status) VALUES (%s, %s,%s, %s,%s, %s, %s,%s, %s, %s,%s, %s, %s, %s, %s);'''
        
        connect_data.execute(query3,values3)
        connection.commit()   
        connection.rollback()

    for i in data["comments_details"]:
        values4=tuple(i.values())
        query4= '''INSERT INTO comments_details(comment_id,comment_text,video_id,author_name,published_at) VALUES (%s, %s,%s, %s,%s);'''
        
        connect_data.execute(query4,values4)
        connection.commit()   
        connection.rollback()

#insert_query()

# streamlit code
if selected == 'Lode Data In SQL':
    step3  = st.button('stor Data In SQL')
    if step3:
        create_table()
        insert_query()
        st.write("Data Migrated Successfuly to SQL,proceed with Select the Query option for analysis")


def qus1():
  connect_data.execute("""
                  SELECT channel_name,title\
                  FROM Video_details""")
  result1= connect_data.fetchall()
  return pd.DataFrame(result1, columns=['channel_name', 'video_name'])

def qus2():
  connect_data.execute( """
          SELECT Channel_Name, COUNT(*) AS Video_Count\
          FROM Video_details\
          GROUP BY Channel_Name\
          ORDER BY Video_Count DESC\
          LIMIT 1""")
  result2= connect_data.fetchall()
  return pd.DataFrame(result2, columns=['channel_name', 'total'])

def qus3():
  connect_data.execute("""SELECT channel_name AS Channel_Name, title AS Video_Title, view_count AS Views FROM video_details ORDER BY view_count DESC LIMIT 10""")
  result3= connect_data.fetchall()
  return pd.DataFrame(result3, columns=['channel_name', 'Video_Title', 'Views']) 

def qus4():
  connect_data.execute('select title , comment_count\
                         from video_details')
  result4= connect_data.fetchall()
  return pd.DataFrame(result4, columns=['video_name', 'comment_count'])

def qus5():
    connect_data.execute("""
           SELECT title, Channel_Name, MAX(like_count) AS Max_Likes\
           FROM Video_details\
           GROUP BY title, Channel_Name\
           ORDER BY Max_Likes DESC\
           """)
    result5= connect_data.fetchall()
    return pd.DataFrame(result5, columns=['video_name', 'channel_name', 'likes_count'])

def qus6():
  connect_data.execute('select title , like_count from video_details')
  result6= connect_data.fetchall()
  return pd.DataFrame(result6, columns=['video_name', 'like_count'])

def qus7():
  connect_data.execute('select channel_name,views from channel_details')
  result7= connect_data.fetchall()
  return pd.DataFrame(result7, columns=['channel_name', 'channel_views'])
  
def qus8():
    connect_data.execute("""SELECT DISTINCT channel_name
                          FROM Video_details
                          WHERE SUBSTRING(published_date, 1, 4) = '2024';""")
    result8= connect_data.fetchall()
    return pd.DataFrame(result8, columns=['channel_name'])

def qus9():
    connect_data.execute("SELECT channel_name, AVG(Duration) AS average FROM video_details GROUP BY channel_name ORDER BY channel_name DESC")
    result9= connect_data.fetchall()
    return pd.DataFrame(result9, columns=['channel_name', 'average'])

def qus10():
  connect_data.execute("""SELECT channel_name AS Channel_Name, title AS Video_name,comment_count AS Comments
                            FROM video_details
                            ORDER BY comment_count DESC
                            LIMIT 10""")
  result10 = connect_data.fetchall()
  return pd.DataFrame(result10,columns=['channel_name', 'video_name', 'comments_count'])


if selected =='Select the Query':
    step4 = st.subheader('Select the Query below')
    q1 = 'Q1-What are the names of all the videos and their corresponding channels?'
    q2 = 'Q2-Which channels have the most number of videos, and how many videos do they have?'
    q3 = 'Q3-What are the top 10 most viewed videos and their respective channels?'
    q4 = 'Q4-How many comments were made on each video with their corresponding video names?'
    q5 = 'Q5-Which videos have the highest number of likes with their corresponding channel names?'
    q6 = 'Q6-What is the total number of likes for each video with their corresponding video names?'
    q7 = 'Q7-What is the total number of views for each channel with their corresponding channel names?'
    q8 = 'Q8-What are the names of all the channels that have published videos in the 2023?'
    q9 = 'Q9-What is the average duration of all videos in each channel with corresponding channel names?'
    q10 = 'Q10-Which videos have the highest number of comments with their corresponding channel names?'

    query_option = st.selectbox('', ['Select One', q1, q2, q3, q4, q5, q6, q7, q8, q9, q10])
    if query_option == q1:
        st.dataframe(qus1())
    elif query_option == q2:
        st.dataframe(qus2())
    elif query_option == q3:
        st.dataframe(qus3())
    elif query_option == q4:
        st.dataframe(qus4())
    elif query_option == q5:
        st.dataframe(qus5())
    elif query_option == q6:
        st.dataframe(qus6())
    elif query_option == q7:
        st.dataframe(qus7())
    elif query_option == q8:
        st.dataframe(qus8())
    elif query_option == q9:
        st.dataframe(qus9())
    elif query_option == q10:
        st.dataframe(qus10())
        
      
