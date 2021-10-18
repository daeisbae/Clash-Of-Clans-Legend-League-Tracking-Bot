import coc  #type: ignore
import nest_asyncio  #type: ignore
import asyncio
from typing import List, Dict, Optional, Union


class PlayerStats:
    def __init__(self, ID: str, Password: str, filename: str) -> None:
        nest_asyncio.apply()
        self.__ID: str = ID
        self.__PW: str = Password
        self.PlayersTag: List[str] = []
        self.PrevPlayersFullInfo: Dict[str, Dict[str, Union[str, int]]] = {}
        self.client = coc.login(self.__ID, self.__PW)
        self.tags_collection_filename: str = filename

    def __del__(self) -> None:
        try:
            self.client.close()
            print("Client Closed")
        except Exception:
            print("Client close failed")

    async def GetUserTrophies(self) -> Dict[str, Dict[str, Union[str, int]]]:
        """
        User Data in self.PlayersTag
        Get user's trophies from the coc.client api
        
        return list of dict[playertag, dict[player name, tag, trophies]]
        why?: to find playertag within O(1)
        """
        tasks = list(
            map(
                lambda player: asyncio.create_task(
                    self.client.get_player(player)), self.PlayersTag))

        PlayersInfo = await asyncio.gather(*tasks)

        return dict(map(lambda player: \
            (player.tag, {'name': player.name, 'tag': player.tag, 'trophies': player.trophies})\
                ,PlayersInfo))

    def GetPlayerList(self) -> None:
        """
        Get target player tag from the given filename and store it in self.PlayersTag
        """
        with open(self.tags_collection_filename, 'r') as f:
            while True:
                tag = f.readline()
                if tag == '':
                    break
                tag = tag.replace('\n', '')
                self.PlayersTag.append(tag)

    def ComparePlayerData(self, NewPlayersInfo: Dict[str, Dict[str, Union[str, int]]])\
         -> Dict[str, Dict[str, Union[str, int]]]:
        """
        Compare trophies of NewPlayersInfo with self.PrevPlayersFullInfo
        if some of them are different, return the players in dict{playertag, playerinfo} format
        that have different trophy value 
        """

        def IsItSameTrophies(profile_1: Optional[Dict[str, Union[str, int]]],\
             profile_2: Optional[Dict[str, Union[str, int]]]) -> bool:

            if isinstance(profile_1, type(None)) or isinstance(
                    profile_2, type(None)):
                print(
                    f"Error!: profile_1: {profile_1}, profile_2: {profile_2}")
                return False
            return profile_1['trophies'] == profile_2[
                'trophies']  #type: ignore

        #If nothing is in the prev player info list
        #return every player info
        if len(self.PrevPlayersFullInfo.keys()) == 0:
            return NewPlayersInfo

        UpdateRequiredInfo: Dict[str, Dict[str, Union[str, int]]] = {}
        for tag in NewPlayersInfo.keys():
            try:
                if not IsItSameTrophies(NewPlayersInfo[tag],
                                        self.PrevPlayersFullInfo[tag]):
                    UpdateRequiredInfo.update({tag: NewPlayersInfo[tag]})
            except KeyError:
                print(f"TAG: {tag}, NOT FOUND, Please Check If Tag Exist!")
        return UpdateRequiredInfo

    def FindTrophyDifferenceAndUpdate(
        self, NewPlayersInfo: Dict[str, Dict[str, Union[str, int]]]
    ) -> Dict[str, Dict[str, Union[str, int]]]:
        """
        Get the difference in trophy and return the information
        """
        if len(self.PrevPlayersFullInfo.keys()) == 0:
            return {}

        def FindTrophyDifference(CurrInfo, PastInfo):
            if isinstance(CurrInfo, type(None)) or isinstance(
                    PastInfo, type(None)):
                print(f"Error!: CurrInfo: {CurrInfo}, PrevInfo: {PastInfo}")
                return 0
            return CurrInfo.get('trophies') - PastInfo.get('trophies')

        TrophyDifferenceCollection = {}
        for tag in NewPlayersInfo.keys():
            TrophyDifference = FindTrophyDifference(
                NewPlayersInfo.get(tag), self.PrevPlayersFullInfo.get(tag))
            TrophyDifferenceCollection[tag] = \
                {'trophies': TrophyDifference, 'name': NewPlayersInfo[tag].get('name'), 'tag': tag}

        return TrophyDifferenceCollection

    async def Run(self):
        """
        IMPORTANT: Call self.GetPlayerList() first before calling this function.
        1. Get data from self.PlayersTag then use GET method to fetch data from coc.api
        2. Compare CurrentReceivedData with PrevReceivedData to check if players trophies changed.
        3. If it is changed, Find the trophy difference and return this value
        """
        NewPlayersInfo = await self.GetUserTrophies()
        print("Get User Trophies")
        print(
            f"NewPlayersInfo = {NewPlayersInfo},\n\n self.PrevPlayerInfo = {self.PrevPlayersFullInfo}"
        )
        DifferenceDetectedPlayers = self.ComparePlayerData(NewPlayersInfo)
        print("Compare Player Data")
        TrophyDifference = self.FindTrophyDifferenceAndUpdate(
            DifferenceDetectedPlayers)
        print(f"Find Trophy Difference: {TrophyDifference}")

        self.PrevPlayersFullInfo = NewPlayersInfo
        return TrophyDifference
