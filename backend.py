import elasticsearch
import json
import requests
import csv
from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback

app = Flask(__name__)
CORS(app)

def es_create_index_if_not_exists(es, index):
    """Create the given ElasticSearch index and ignore error if it already exists"""
    try:
        es.indices.create(index)
    except elasticsearch.exceptions.RequestError as ex:
        if ex.error == 'resource_already_exists_exception':
            pass # Index already exists. Ignore.
        else: # Other exception - raise it
            raise exnodes

def insert_movies(filename):
  # open the CSV file and read the rows
  with open(filename, "r") as file:
    reader = csv.DictReader(file)
    for row in reader:
      # extract the movie data from the row
      movie = {
        "name": row["movie_title"],
        "actors": row["actor_1_name"],
        "genre": row["genres"],
        "release_date": row["title_year"]
      }

      # insert the movie into the Elasticsearch index
      es.index(index="movies", body=movie)

es = elasticsearch.Elasticsearch(["http://localhost:9200"])
es_create_index_if_not_exists(es,"movies")
# insert_movies("movie_metadata.csv")



def filter_movies(name, actors, genre, date):
  query = {
    "query": {
      "bool": {
        "must": []
      }
    }
  }
  headers={
    "Content-Type": "application/json"
  }

  if name:
    query["query"]["bool"]["must"].append({
      "match": {
        "name": name
      }
    })
  if actors:
    query["query"]["bool"]["must"].append({
      "match": {
        "actors": actors
      }
    })
  if genre:
    query["query"]["bool"]["must"].append({
      "match": {
        "genre": genre
      }
    })
  if date:
    query["query"]["bool"]["must"].append({
      "match": {
        "release_date": date
      }
    })



  res = es.search(index="movies", body=query, headers={
    "Content-Type": "application/json"
  })
  return res["hits"]["hits"]

def get_movie_poster(name):
  # make a GET request to the OMDb API to get the movie poster
  res = requests.get(
    "http://www.omdbapi.com/",
    params={
      "apikey": "74e22e02",
      "t": name,
      "i": "tt3896198"
    }
  )

  # extract the movie poster URL from the response
  try:
    print(res.json())
    poster_url = res.json()["Poster"]
  except Exception as e:
    error_message = traceback.format_exc()
    print(error_message)
    poster_url = ""

  return poster_url

@app.route("/search", methods=["GET"])
def search():
  # get the search query from the request query parameters
  name = request.args.get("name")
  actors = request.args.get("actors")
  genre = request.args.get("genre")
  date = request.args.get("date")

  print("in search")
  # filter the movies
  movies = filter_movies(name, actors, genre, date)

  # get the movie posters
  for movie in movies:
    movie["_source"]["poster_url"] = get_movie_poster(movie["_source"]["name"])

  return jsonify({
    "hits": {
      "hits": movies
    }
  })

@app.route("/poster", methods=["GET"])
def poster():
  # get the movie name from the request query parameters
  name = request.args.get("name")

  # get the movie poster URL
  poster_url = get_movie_poster(name)

  return poster_url

@app.route("/insert", methods=["POST"])
def insert():
  # get the movie data from the request body
  movie_data = request.json

  # insert the movie into Elasticsearch
  res = es.index(index="movies", body=movie_data)

  return jsonify({
    "result": "success",
    "id": res["_id"]
  })

if __name__ == "__main__":
  app.run(debug=True)
