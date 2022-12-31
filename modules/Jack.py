# from .Whatsapp import *
class Jack:

    def get_positions(self, bets = 0, total_amount = 0.0):
        last_prize = int(bets)/100000
        
        prizes = []
        
        if int(bets) < 2:
            return prizes

        i = bets-1
        
        for i in range(bets) :
            prizes.append(0.0)

        ratio = 0.0
        money = float(total_amount)-float(total_amount)*0.2
        s = 0.0

        first_prize = 1.8 * money/bets+last_prize

        ratio = (first_prize-last_prize)/(bets-1)

        prizes[bets-1] = last_prize

        for i in range(len(prizes)-2, 0, -1):
            prizes[i] = prizes[i+1]+ratio    

        prizes[0] = first_prize

        # print(f"-----------------------------------------------------------------")
        # print(f"-----------------------------------------------------------------")
        # print(f"----------------------SLOT DISTRIBUTION--------------------------")
        # print(f"-----------------------------------------------------------------")
        # print(f"-----------------------------------------------------------------")

        # zeroing results
        for i in range(len(prizes)):
            if prizes[i] <= 0.01:
                prizes[i] = 0.00
            
            # print(f"Rank: {i+1} Reward(BUSD): {prizes[i]}")

        return prizes

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)