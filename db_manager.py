import aiosqlite


class Database:

    def __init__(self):
        self.ratings_path = "C:/Users/cvela/MyCodeFolder/PythonFolder/Bots/Fatbot/music_records.db"
        self.bank_path = "C:/Users/cvela/MyCodeFolder/PythonFolder/Bots/Fatbot/bank.db"
        self.tables = ["j_t", "d_t", "c_t"]
        self.keyed_tables = {477249470732697601: self.tables[0], 477270012592259082: self.tables[1],
                             387334819232874498: self.tables[2]}
        self.table_owners = {v: k for k, v in self.keyed_tables.items()}

    async def rate_song(self, title: str, score: int, critic: int):
        async with aiosqlite.connect(self.ratings_path) as db:
            rating = await self.get_rating(title, critic)
            if not rating:
                await db.execute(f"INSERT INTO {self.keyed_tables[critic]} (title,score) VALUES ('{title}', '{score}')")
            else:
                await db.execute(f"UPDATE {self.keyed_tables[critic]} SET score = {score} WHERE title = '{title}';")
            await db.commit()

    async def print_all_ratings(self):
        async with aiosqlite.connect(self.ratings_path) as db:
            for table in self.tables:
                async with db.execute(f"SELECT * from {table}") as songs:
                    async for row in songs:
                        print(row)
            await db.commit()

    async def get_rating(self, title: str, critic: int):
        rating = None
        async with aiosqlite.connect(self.ratings_path) as db:
            async with db.execute(f"SELECT * from {self.keyed_tables[critic]} WHERE title = '{title}'") as songs:
                async for song in songs:
                    print(song)
                    rating = song[1]
                    break
                if not rating:
                    print(f"{title} is not rated!")
            await db.commit()
        return rating

    async def get_critic_ratings(self, critic: int):
        ratings = []
        async with aiosqlite.connect(self.ratings_path) as db:
            async with db.execute(f"SELECT * from {self.keyed_tables[critic]}") as songs:
                async for song in songs:
                    score = [song[0], song[1]]
                    ratings.append(score)
            await db.commit()
        return ratings

    async def get_all_ratings(self, title: str):
        rating = []
        async with aiosqlite.connect(self.ratings_path) as db:
            for table in self.tables:
                async with db.execute(f"SELECT * from {table} WHERE title = '{title}'") as songs:
                    async for song in songs:
                        score = [self.table_owners[table], song[1]]
                        rating.append(score)
                        break
            if not rating:
                print(f"{title} is not rated!")
            await db.commit()
        return rating

    async def get_songs(self, score: int):
        songs = []
        async with aiosqlite.connect(self.ratings_path) as db:
            for table in self.tables:
                async with db.execute(f"SELECT * from {table} WHERE score = {score}") as entries:
                    async for entry in entries:
                        song = [self.table_owners[table], entry[0]]
                        songs.append(song)
            if not songs:
                print(f"No songs were rated: {score}!")
            await db.commit()
        return songs

    async def prune_songs(self, title: str, critic: int):
        async with aiosqlite.connect(self.ratings_path) as db:
            await db.execute(f"DELETE from {self.keyed_tables[critic]} WHERE title = '{title}'")
            await db.commit()

    async def create_music_tables(self):
        async with aiosqlite.connect(self.ratings_path) as db:
            for table in self.tables:
                await db.execute(f"""
                                CREATE TABLE {table} (
                                title TEXT   NOT NULL,
                                score INT    NOT NULL
                                );
                                """)
                await db.commit()
            print("Table created!")

    async def drop_music_tables(self):
        async with aiosqlite.connect(self.ratings_path) as db:
            for table in self.tables:
                await db.execute(f"DROP TABLE {table}")
                await db.commit()
            print("Table dropped!")