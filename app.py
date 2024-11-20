# Neo4j: parse xml data into .csv, then upload it from there
# 6 Degrees of Kevin bacon: List of celebrities, # of steps from kevin bacon, valid information about those steps.
# 
# Schema:
# Celebrity: actor_id, actor_name, movie_id, movie_title, release_year, role
# .csv will be loaded with cypher, and will be separated into 3 different types of nodes