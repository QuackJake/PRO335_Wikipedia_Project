import xml.etree.ElementTree as xet 
import pandas as pd 

# Neo4j: parse xml data into .csv, then upload it from there
# 6 Degrees of Kevin bacon: List of celebrities, # of steps from kevin bacon, valid information about those steps.
# 
# Schema:
# Celebrity: actor_id, actor_name, movie_id, movie_title, release_year, role
# .csv will be loaded with cypher, and will be separated into 3 different types of nodes

cols = ["actor_id", "actor_name", "movie_id", "movie_title", "release_year", "role"] 
rows = [] 

xmlparse = xet.parse('sample.xml') 
root = xmlparse.getroot() 
for i in root: 
    name = i.find("name").text 
    phone = i.find("phone").text 
    email = i.find("email").text 
    date = i.find("date").text 
    country = i.find("country").text 
  
    rows.append({"name": name, 
                 "phone": phone, 
                 "email": email, 
                 "date": date, 
                 "country": country}) 
  
data_frame = pd.DataFrame(rows, columns=cols) 

data_frame.to_csv('output.csv') 