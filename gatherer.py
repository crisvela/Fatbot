import asyncpraw
from asyncprawcore.exceptions import Forbidden
from asyncprawcore.exceptions import NotFound


class Gatherer:
    def __init__(self):
        self.reddit = None
        self.subreddit = None
        self.error_flag = False
        self.no_img_flag = False
        self.sub_name = ""
    
    async def get_sub_images(self, subreddit, num=50, invalid_ids=None):
        self.reddit = asyncpraw.Reddit(site_name="WardenBotScraper", user_agent="Warden User Agent")
        print(f"get_sub_images was called! Subreddit: {subreddit}! Num: {num}")
        if await self.sub_available(subreddit):
            print("Valid Sub!")
            self.subreddit = await self.reddit.subreddit(subreddit)
        else:
            self.subreddit = await self.reddit.random_subreddit(nsfw=False)
            self.error_flag = True
            print(f"Invalid Subreddit, Random One Assigned: {self.subreddit.display_name}!")
        self.sub_name = self.subreddit.display_name
        post = None
        if await self.subreddit.random() is not None:
            print("Getting random post!")
            for i in range(num):
                submission = await self.subreddit.random()
                if not test_post(submission):
                    pass
                else:
                    if invalid_ids:
                        if submission.id in invalid_ids:
                            pass
                        else:
                            print("Post appended!")
                            post = submission.url
                            break
                    else:
                        print("Post appended!")
                        post = submission.url
                        break
        else:
            async for submission in self.subreddit.hot(limit=num):
                if not test_post(submission):
                    pass
                else:
                    if invalid_ids:
                        if submission.id in invalid_ids:
                            print("Invalid id!")
                        else:
                            print("Post appended!")
                            post = submission.url
                            break
                    else:
                        print("Post appended!")
                        post = submission.url
                        break
        await self.reddit.close()
        if not post:
            self.no_img_flag = True
            return await self.get_sub_images(None)
        else:
            return post

    async def sub_available(self, subreddit):
        if subreddit:
            try:
                print("Checking availability!")
                subs = self.reddit.subreddits.search_by_name(subreddit, exact=True)
                print("Pass")
                async for sub in subs:
                    async for submission in sub.hot(limit=1):
                        pass
            except (Forbidden, NotFound):
                return False
            else:
                return True
        else:
            return False


def test_post(post):
    if post.stickied or post.is_video or post.over_18 or post.is_self:
        return False
    ext_list = [".jpg", ".jpeg", ".png"]
    try:
        image = post.url
        if not any(extension in image for extension in ext_list):
            raise AttributeError
    except AttributeError:
        return False
    return True
