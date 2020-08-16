# profile.py

import re
import sqlite3
import aiosqlite
import rollbot.profile.profile


class Profile():
    def __init__(self, db_name: str, table_suffix: str):
        self.db_name = db_name
        self.table = f'PROFILES{table_suffix}'
        self.create_db()

    def create_db(self):
        try:
            with sqlite3.connect(self.db_name) as db:
                db.execute(f'''CREATE TABLE {self.table}
                    (ID      INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                    OWNER    CHAR(50)                          ,
                    OWNER_ID INTEGER                           NOT NULL,
                    PROFILE  CHAR(50)                          NOT NULL,
                    LINK     CHAR(255)                         NOT NULL);''')
        except Exception as ex:
            return True


    async def add_profile(self, member: str, member_id: int, profile_name: str, profile_link: str):
        regex = re.compile(
            r'^https://discordapp.com/channels/\d{18}/\d{18}/\d{18}',
            re.IGNORECASE
        )

        if (re.match(regex, profile_link) is not None):
            # Do the save thing
            async with aiosqlite.connect(self.db_name) as db:
                exist_count = await db.execute(
                    f'SELECT LINK FROM {self.table} WHERE OWNER_ID = ? AND PROFILE = ?',
                    (member_id, profile_name)
                )
                row = await exist_count.fetchone()
                if (row == None):
                    cursor = await db.cursor()
                    await cursor.execute(
                        f"INSERT INTO {self.table} (PROFILE, LINK, OWNER, OWNER_ID) VALUES (?,?,?,?)",
                        (profile_name, profile_link, member, member_id)
                    )
                    await db.commit()
                    return f'** Added "{profile_name}" profile at "{profile_link}"'
            return f'** Couldn\'t add the profile "{profile_name}", you have already got that profile as {row[0]}'
        else:
            return f'** Couldn\'t add the profile "{profile_link}", it must be a Discord URL'

    async def get_profile(self, profile_name: str):
        async with aiosqlite.connect(self.db_name) as db:
            results = await db.execute(
                f'SELECT OWNER, LINK FROM {self.table} WHERE PROFILE = ?',
                (profile_name,)
            )
            to_return = []
            async for row in results:
                to_return.append(f'** {profile_name}({row[0]}): {row[1]}')
            if (len(to_return) == 0):
                return f'** Could not find a profile for {profile_name}'
            elif (len(to_return) == 1):
                return f'** {profile_name}: {row[1]}'
            else:
                return '\n'.join(to_return)

    async def del_profile(self, member_id: int, profile_name: str):
        async with aiosqlite.connect(self.db_name) as db:
            results = await db.execute(
                f'SELECT ID, OWNER_ID, OWNER, LINK FROM {self.table} WHERE PROFILE = ?',
                (profile_name,)
            )
            delete_count = 0
            process_count = 0
            owners = []
            async for row in results:
                process_count += 1
                if (row[1] == member_id):
                    cursor = await db.cursor()
                    await cursor.execute(
                        f"DELETE FROM {self.table} WHERE ID = ?",
                        (row[0],)
                    )
                    await db.commit()
                    delete_count += 1
                else:
                    owners.append(row[1])

            await results.close()
            if (process_count == 0):
                return f'** Could not find a profile for {profile_name}'
            elif (delete_count == 0):
                owners_string = ','.join(owners)
                return f'** You do not own {profile_name}({owners_string})'
            elif (process_count > 1):
                return f'** Deleted {profile_name}({row[2]})'
            else:
                return f'** Deleted {profile_name}'
