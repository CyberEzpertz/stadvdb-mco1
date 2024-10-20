import pandas as pd
import math
import psycopg
from datetime import datetime

# Initialize the tables with granular data
text_languages = []
audio_languages = []
genres = []
developers = []
publishers = []
categories = []
tags = []
packages = []
sub_packages = []
movies = []
screenshots = []

# Initialize dictionaries for dimension groups to track unique entries
language_group = {}
genre_group = {}
developer_group = {}
publisher_group = {}
category_group = {}
tag_group = {}
support_group = {}
dim_date = {}

# Initialize a list for the FactGame rows
fact_game_rows = []


def parse_date(date):
    try:
        # Try the full format with day, month, and year
        return datetime.strptime(date, '%b %d, %Y')
    except ValueError:
        try:
            # Try the shortened format without day
            return datetime.strptime(date, '%b %Y')
        except ValueError:
            # If both fail, return None
            return None


def create_dimDate(date: datetime):
    quarter = math.ceil(date.month / 3)
    month = date.month
    year = date.year

    return {
        'date': date,
        'month': month,
        'year': year,
        'quarter': quarter
    }


def extract_data():
    # Extract the data from the JSON file
    filename = "games.json"
    data = pd.read_json(filename)
    data = data.T
    df = data

    # Clean the release date column
    df["release_date"] = data["release_date"].apply(parse_date)
    return df


def transform_data(df):
    for index, row in df.iterrows():
        # Prepare the FactGame row
        new_row = {
            "id": index,
            "name": row["name"],
            "about": row["about_the_game"],
            "detailedDesc": row["detailed_description"],
            "shortDesc": row["short_description"],
            "reviews": row["reviews"],
            "headerImg": row["header_image"],
            "website": row["website"],
            "supportURL": row["support_url"],
            "supportEmail": row["support_email"],
            "price": row["price"],
            "requiredAge": row["required_age"],
            "dlcCount": row["dlc_count"],
            "achievements": row["achievements"],
            "avePlaytimeForever": row["average_playtime_forever"],
            "avePlaytime2Weeks": row["average_playtime_2weeks"],
            "medPlaytimeForever": row["median_playtime_forever"],
            "medPlaytime2Weeks": row["median_playtime_2weeks"],
            "peakCCU": row["peak_ccu"],
            "metacriticScore": row["metacritic_score"],
            "metacriticURL": row["metacritic_url"],
            "notes": row["notes"],
            "scoreRank": row["score_rank"],
            "positiveReviews": row["positive"],
            "negativeReviews": row["negative"],
            "estimatedOwners": row["estimated_owners"],
            "reviewerCount": row["positive"] + row["negative"],
            "releaseDate": row["release_date"],
            # Placeholder for the foreign key IDs
            "genreGroupId": None,
            "tagGroupId": None,
            "languageGroupId": None,
            "developerGroupId": None,
            "publisherGroupId": None,
            "categoryGroupId": None,
            "dimSupportId": None,
        }

        # Handle the languages
        languages = (tuple(row["supported_languages"]),
                     tuple(row["full_audio_languages"]))
        if languages not in language_group:
            groupId = len(language_group) + 1
            language_group[languages] = groupId

            # Create new entries inside text languages and audio languages
            for textLang in languages[0]:
                data = {"language": textLang, "groupId": groupId}
                text_languages.append(data)
            for audioLang in languages[1]:
                data = {"language": audioLang, "groupId": groupId}
                audio_languages.append(data)

            new_row["languageGroupId"] = groupId
        else:
            new_row["languageGroupId"] = language_group[languages]

        # Handle Developers
        developer_tuple = tuple(row["developers"])
        if developer_tuple not in developer_group:
            groupId = len(developer_group) + 1
            developer_group[developer_tuple] = groupId

            for dev in developer_tuple:
                data = {"name": dev, "groupId": groupId}
                developers.append(data)

            new_row["developerGroupId"] = groupId
        else:
            new_row["developerGroupId"] = developer_group[developer_tuple]

        # Handle Publishers
        publisher_tuple = tuple(row["publishers"])
        if publisher_tuple not in publisher_group:
            groupId = len(publisher_group) + 1
            publisher_group[publisher_tuple] = groupId

            for pub in publisher_tuple:
                data = {"name": pub, "groupId": groupId}
                publishers.append(data)

            new_row["publisherGroupId"] = groupId
        else:
            new_row["publisherGroupId"] = publisher_group[publisher_tuple]

        # Handle Categories
        categories_tuple = tuple(row["categories"])
        if categories_tuple not in category_group:
            groupId = len(category_group) + 1
            category_group[categories_tuple] = groupId

            for cat in categories_tuple:
                data = {"name": cat, "groupId": groupId}
                categories.append(data)

            new_row["categoryGroupId"] = groupId
        else:
            new_row["categoryGroupId"] = category_group[categories_tuple]

        # Handle Genres
        genres_tuple = tuple(row["genres"])
        if genres_tuple not in genre_group:
            groupId = len(genre_group) + 1
            genre_group[genres_tuple] = groupId

            for gen in genres_tuple:
                data = {"genre": gen, "groupId": groupId}
                genres.append(data)

            new_row["genreGroupId"] = groupId
        else:
            new_row["genreGroupId"] = genre_group[genres_tuple]

        # Handle Tags
        if isinstance(row["tags"], dict):
            tags_tuple = tuple((k, v) for k, v in row["tags"].items())
            if tags_tuple not in tag_group:
                groupId = len(tag_group) + 1
                tag_group[tags_tuple] = groupId

                for tag in tags_tuple:
                    data = {"name": tag[0],
                            "groupId": groupId, "count": tag[1]}
                    tags.append(data)

                new_row["tagGroupId"] = groupId
            else:
                new_row["tagGroupId"] = tag_group[tags_tuple]
        else:
            if () not in tag_group:
                groupId = len(tag_group) + 1
                tag_group[()] = groupId
                new_row["tagGroupId"] = groupId
            else:
                new_row["tagGroupId"] = tag_group[()]

        # Handle the DimDate
        releaseDate = row["release_date"]
        if releaseDate not in dim_date:
            dim_date[releaseDate] = create_dimDate(releaseDate)

        # Handle Support
        support_tuple = (row["mac"], row["windows"], row["linux"])
        if support_tuple not in support_group:
            supportId = len(support_group) + 1
            data = {"supportId": supportId,
                    "macSupport": support_tuple[0], "windowsSupport": support_tuple[1], "linuxSupport": support_tuple[2]}
            support_group[support_tuple] = data

            new_row["dimSupportId"] = supportId
        else:
            new_row["dimSupportId"] = support_group[support_tuple]["supportId"]

        # Handle Packages
        for package in row["packages"]:
            data = {
                "id": len(packages) + 1,
                "title": package["title"],
                "description": package["description"],
                "gameId": index
            }
            packages.append(data)

            for sub in package["subs"]:
                subData = {
                    "text": sub["text"],
                    "description": sub["description"],
                    "price": sub["price"],
                    "packageId": len(packages)
                }
                sub_packages.append(subData)

        # Handle Movies & Screenshots
        for movie in row["movies"]:
            data = {
                "url": movie,
                "gameId": index
            }
            movies.append(data)

        for screenshot in row["screenshots"]:
            data = {
                "url": screenshot,
                "gameId": index
            }
            screenshots.append(data)

        # Store the FactGame row
        fact_game_rows.append(new_row)


def insert_group_rows(cur, num, table_name):
    try:
        vals = [(x,) for x in range(1, num+1)]
        # query = f'INSERT INTO "{table_name}" VALUES (%s)'
        copy = f'COPY "{table_name}" FROM STDIN'
        print(f"[START] INSERT -> {table_name}.")

        with cur.copy(copy) as copy:
            for value in vals:
                copy.write_row(value)

        print(f"[SUCCESS] INSERT -> {table_name}.")
    except Exception as e:
        print(f"[ERROR] Skipped INSERT -> {table_name}.")
        print(f"[ERROR] Exception: {e}")


def insert_dict_array(cur, dictVals, table_name):
    try:
        print(f"[START] INSERT -> {table_name}.")
        keys = dictVals[0].keys()
        columns = [f'"{key}"' for key in keys]
        values = set(tuple(entry.values()) for entry in dictVals)
        copy = f'COPY "{table_name}" ({', '.join(columns)}) FROM STDIN'
        with cur.copy(copy) as copy:
            for value in values:
                copy.write_row(value)

        print(f"[SUCCESS] INSERT -> {table_name}.")
    except Exception as e:
        print(f"[ERROR] Skipped INSERT -> {table_name}.")
        print(f"[ERROR] Exception: {e}")


def insert_nested_dict(cur, dictVals, table_name):
    try:
        print(f"[START] INSERT -> {table_name}.")
        values = list(dictVals.values())
        keys = values[0].keys()
        columns = [f'"{key}"' for key in keys]
        placeholders = [f'%({key})s' for key in keys]
        query = f'''INSERT INTO "{table_name}" ({', '.join(columns)}) VALUES ({
            ", ".join(placeholders)})'''
        cur.executemany(query, values)

        print(f"[SUCCESS] INSERT -> {table_name}.")
    except Exception as e:
        print(f"[ERROR] Skipped INSERT -> {table_name}.")
        print(f"[ERROR] Exception: {e}")


def load_data():
    with psycopg.connect("postgresql://user:password@localhost:5001/postgres", autocommit=True) as conn:
        with conn.cursor() as cur:
            # Insert Groups
            insert_group_rows(cur, len(publisher_group), "DimPublisherGroup")
            insert_group_rows(cur, len(language_group), "DimLanguageGroup")
            insert_group_rows(cur, len(category_group), "DimCategoryGroup")
            insert_group_rows(cur, len(developer_group), "DimDeveloperGroup")
            insert_group_rows(cur, len(tag_group), "DimTagGroup")
            insert_group_rows(cur, len(genre_group), "DimGenreGroup")

            # Insert granular data
            insert_dict_array(cur, text_languages, "TextLanguage")
            insert_dict_array(cur, audio_languages, "AudioLanguage")
            insert_dict_array(cur, genres, "Genre")
            insert_dict_array(cur, developers, "Developer")
            insert_dict_array(cur, publishers, "Publisher")
            insert_dict_array(cur, categories, "Category")
            insert_dict_array(cur, tags, "Tag")

            # Insert nested dictionaries
            insert_nested_dict(cur, support_group, "DimSupport")
            insert_nested_dict(cur, dim_date, "DimDate")

            # Insert fact rows
            insert_dict_array(cur, fact_game_rows, "FactGame")

            # Insert many-to-one data
            insert_dict_array(cur, packages, "DimPackage")
            insert_dict_array(cur, movies, "DimMovie")
            insert_dict_array(cur, screenshots, "DimScreenshot")
            insert_dict_array(cur, sub_packages, "DimPackageSub")


def main():
    print("Extracting the data...")
    df = extract_data()
    print("Transforming the data...")
    transform_data(df)
    print("Loading the data...")
    load_data()


main()
