import random

none_reward_probability = 0.80
small_reward_probability = 0.15
large_reward_probability = 0.05


earnings_this_week = float(input("How much earnings did you have this week? "))

credit_cost = earnings_this_week/2
array_length = 50  # Change this to your desired array length

small_reward = credit_cost * 2
large_reward = credit_cost * 10

backtest_iterations = int(input("How many times do you want to backtest? "))

# credit_cost = 2.0
# array_length = 20  # Change this to your desired array length

# small_reward = 2.0
# large_reward = 10.0

# backtest_iterations = 100

def create_custom_array(length):
    array = [0] * int(length * none_reward_probability)
    array.extend([small_reward] * int(length * small_reward_probability))
    array.extend([large_reward] * int(length * large_reward_probability))
    random.shuffle(array)
    return array

def draw():
    custom_array = create_custom_array(array_length)
    print(custom_array)
    # Select a random position from the custom_array
    random_position = random.choice(custom_array)
    print("Selected reward:", random_position)
    return random_position

def backtest():
    total_profit = 0.0
    total_cost = 0.0

    for i in range(0, backtest_iterations):
        result = draw()

        if result == 0:
            total_profit += credit_cost
        else:
            total_cost += result
    
    print(f"The user have earned: {earnings_this_week} BUSD")
    print(f"The cost per credit is: {credit_cost} BUSD")
    print(f"The user purchased: {credit_cost * backtest_iterations} credits")

    print("Total Given:", total_cost)
    print("Total Earned:", total_profit)
    print("Net Company's profit:", total_profit - total_cost)


backtest()