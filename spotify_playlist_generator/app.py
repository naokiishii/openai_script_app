import datetime

from dotenv import dotenv_values
import pprint
import argparse
import json
import openai
import os
import spotipy


def main():
    config = dotenv_values(".env")
    os.environ["OPENAI_API_KEY"] = config["OPENAI_API_KEY"]
    parser = argparse.ArgumentParser(description="Simple command line song utility")
    parser.add_argument("-p", type=str, default="fun songs", help="The prompt to describe the playlist")
    parser.add_argument("-n", type=int, default=5, help="The number of songs to add to the playlist")

    args = parser.parse_args()
    prompt = args.p
    count = args.n
    playlist = get_playlist(config, prompt, count)
    add_songs_to_spotify(config, prompt, playlist)


def get_playlist(config, prompt, count=8):
    example_json = """
      [
          {"song": "Kisetsu wa Tsugitsugi Shindeiku", "artist": "EGO-WRAPPIN'"},
          {"song": "Sakura", "artist": "Ikimono Gakari"},
          {"song": "Hana wa Saku", "artist": "Various Artists"},
          {"song": "Yuki no Hana", "artist": "Mariah Carey"},
          {"song": "Kanashii Ue ni Risenai", "artist": "Miliyah Kato"},
          {"song": "Blue", "artist": "Misia"},
          {"song": "Kisetsu no Shumatsu", "artist": "Yojiro Noda"},
          {"song": "Sayonara Bysn", "artist": "Miyuki Nakajima"},
          {"song": "Fukutsu no Uta", "artist": "Yutaka Ozaki"},
          {"song": "Koi wa Mizuiro", "artist": "Aimer"}
      ]
      """
    messages = [
          {"role": "system", "content": """You are a helpful playlist generating assistant.
          You should generate a list of songs and their artists according to a text prompt
          You should return a JSON array, where each element follows this format: {"song": <song_title>, "artist": <artist_name>}"""},
          {"role": "user", "content": "Generate a playlist of 10 songs based on this prompt: super super sad J-POP songs"},
          {"role": "assistant", "content": example_json},
          {"role": "user", "content": f"Generate a playlist of {count} songs based on this prompt: {prompt}"},
    ]
    client = openai.OpenAI()
    res = client.chat.completions.create(
      messages=messages,
      model="gpt-4o-mini",
      max_tokens=400,
    )
    print(json.loads(res.choices[0].message.content))
    return json.loads(res.choices[0].message.content)


def add_songs_to_spotify(config, playlist_prompt, playlist):
    os.environ["OPENAI_API_KEY"] = config["OPENAI_API_KEY"]
    sp = spotipy.Spotify(
        auth_manager=spotipy.SpotifyOAuth(
            client_id=config["SPOTIFY_CLIENT_ID"],
            client_secret=config["SPOTIFY_CLIENT_SECRET"],
            redirect_uri="http://localhost:9999",
            scope="playlist-modify-private",
        )
    )

    current_user = sp.current_user()
    assert current_user is not None

    track_ids = []
    for item in playlist:
        artist, song = item["artist"], item["song"]
        advanced_query = f"artist:({artist}) track:({song}"
        basic_query = f"{song} {artist}"
        for query in [advanced_query, basic_query]:
            search_result = sp.search(q=query, type="track", limit=10)
            # pprint.pprint(search_result["tracks"]["items"][0]["id"])
            if not search_result["tracks"]["items"] or search_result["tracks"]["items"][0]["popularity"] < 20:
                continue
            else:
                result = search_result["tracks"]["items"][0]
                print(f"Found: {result['name']} - {result['id']}")
                track_ids.append(result["id"])
                break
        else:
            print(f"Queries {advanced_query} and {basic_query} returned no good results.")

    created_playlist = sp.user_playlist_create(
        current_user["id"],
        public=False,
        name=f"{playlist_prompt} - [{datetime.datetime.now().strftime('%c')}]",
    )

    sp.playlist_add_items(created_playlist["id"], track_ids)


if __name__ == "__main__":
    main()
