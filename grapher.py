import db_manager
import matplotlib.pyplot as plt
import numpy as np
import asyncio


class Analyzer:

    def __init__(self):
        self.database = db_manager.Database()

    async def graph(self, critic: int):

        x_measured = [i for i in range(0, 12)]
        y_measured = [0 for i in range(0, 12)]
        scores = await self.database.get_critic_ratings(critic)

        for title, score in scores:
            if 0 <= score <= 11: 
                y_measured[score] += 1
            elif score > 11:
                y_measured[11] += 1
            else:
                y_measured[0] += 1

        plt.title("Song Ratings")
        plt.bar(x_measured, y_measured, label="Scores")
        plt.yticks(np.arange(0, max(y_measured)+1, 1.0))
        plt.xticks(np.arange(min(x_measured), max(x_measured)+1, 1.0))
        plt.xlabel("Scores")
        plt.ylabel("Number of Songs")

        plt.savefig(f'{self.database.keyed_tables[critic]}.png')

        plt.clf()

        return f'{self.database.keyed_tables[critic]}.png'
