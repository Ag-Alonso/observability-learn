# Learn Python 3 - Magic 8-Ball

## The Magic 8-Ball

The Magic 8-Ball is a popular toy developed in the 1950s for fortune-telling or advice seeking.

Write a `magic8.py` Python program that can answer any “Yes” or “No” question with a different fortune each time it executes.

Magic 8-Ball, should I do this project?

We’ll be using the following 9 possible answers for our Magic 8-Ball:
- Yes - definitely
- It is decidedly so
- Without a doubt
- Reply hazy, try again
- Ask again later
- Better not tell you now
- My sources say no
- Outlook not so good
- Very doubtful

## Output Format
```python
[Name] asks: [Question]
Magic 8-Ball’s answer: [Answer]
```

### Example
```python
Joe asks: Is this real life?
Magic 8-Ball's answer: Better not tell you now
```

## Tasks
### Setting up
```python
name = "Joe"  # Name of the asker
question = "Will I win the lottery?"  # Yes or No question
answer = ""  # Empty string for now
```

### Generating a random number
```python
import random
random_number = random.randint(1, 9)
#print(random_number)  # Optional: verify randomness
```

### Control Flow
```python
if random_number == 1:
    answer = "Yes - definitely"
elif random_number == 2:
    answer = "It is decidedly so"
elif random_number == 3:
    answer = "Without a doubt"
elif random_number == 4:
    answer = "Reply hazy, try again"
elif random_number == 5:
    answer = "Ask again later"
elif random_number == 6:
    answer = "Better not tell you now"
elif random_number == 7:
    answer = "My sources say no"
elif random_number == 8:
    answer = "Outlook not so good"
elif random_number == 9:
    answer = "Very doubtful"
else:
    answer = "Error"
```

### Seeing the result
```python
if name == "":
    print(f"Question: {question}")
else:
    print(f"{name} asks: {question}")

print(f"Magic 8-Ball's answer: {answer}")
```

### Optional Challenges
- Add more possible answers and adjust the random number range and `elif` statements.
- Handle empty `name` by printing only the question.
- Handle empty `question` by informing the user.

Run your program multiple times to see different fortunes generated each time.

