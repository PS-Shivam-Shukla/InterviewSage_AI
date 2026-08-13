"""
Aptitude Question Bank & Selection Module (Phase 5.5).
Contains exactly 20 fixed, deterministic quantitative and logical reasoning questions.
Selects 5 randomized questions per fresher interview session without replacement.
"""

import random
from typing import List, Dict, Any

APTITUDE_20_BANK: List[Dict[str, Any]] = [
    {
        "id": "apt-1",
        "category": "Percentage",
        "question_text": "If a salary is increased by 20% and then decreased by 20%, what is the net percentage change in the salary?",
        "options": ["No change", "4% decrease", "4% increase", "2% decrease"],
        "correct_answer": "4% decrease",
        "competency_targeted": "Quantitative Reasoning",
        "difficulty": "EASY",
    },
    {
        "id": "apt-2",
        "category": "Profit & Loss",
        "question_text": "A trader buys a item for $80 and sells it for $100. What is the profit percentage?",
        "options": ["20%", "25%", "15%", "30%"],
        "correct_answer": "25%",
        "competency_targeted": "Quantitative Reasoning",
        "difficulty": "EASY",
    },
    {
        "id": "apt-3",
        "category": "Simple Interest",
        "question_text": "Calculate the simple interest on $1,000 at 5% per annum for 3 years.",
        "options": ["$150", "$100", "$200", "$125"],
        "correct_answer": "$150",
        "competency_targeted": "Quantitative Reasoning",
        "difficulty": "EASY",
    },
    {
        "id": "apt-4",
        "category": "Compound Interest",
        "question_text": "What is the compound interest on $2,000 at 10% per annum compounded annually for 2 years?",
        "options": ["$400", "$420", "$440", "$410"],
        "correct_answer": "$420",
        "competency_targeted": "Quantitative Reasoning",
        "difficulty": "MEDIUM",
    },
    {
        "id": "apt-5",
        "category": "Speed, Time & Distance",
        "question_text": "A car travels at 60 km/h for 2.5 hours. What is the total distance covered?",
        "options": ["120 km", "140 km", "150 km", "160 km"],
        "correct_answer": "150 km",
        "competency_targeted": "Problem Solving",
        "difficulty": "EASY",
    },
    {
        "id": "apt-6",
        "category": "Time & Work",
        "question_text": "If Alice can complete a task in 6 days and Bob in 12 days, how many days will they take working together?",
        "options": ["4 days", "6 days", "8 days", "3 days"],
        "correct_answer": "4 days",
        "competency_targeted": "Problem Solving",
        "difficulty": "MEDIUM",
    },
    {
        "id": "apt-7",
        "category": "Ratios & Proportions",
        "question_text": "If A:B = 2:3 and B:C = 4:5, what is the ratio A:C?",
        "options": ["8:15", "2:5", "6:15", "10:12"],
        "correct_answer": "8:15",
        "competency_targeted": "Logical Reasoning",
        "difficulty": "EASY",
    },
    {
        "id": "apt-8",
        "category": "Averages",
        "question_text": "The average of five numbers is 20. If one number is removed, the average becomes 18. What was the removed number?",
        "options": ["24", "28", "26", "30"],
        "correct_answer": "28",
        "competency_targeted": "Quantitative Reasoning",
        "difficulty": "MEDIUM",
    },
    {
        "id": "apt-9",
        "category": "Logical Reasoning",
        "question_text": "Complete the sequence: 2, 6, 12, 20, 30, ___?",
        "options": ["40", "42", "44", "38"],
        "correct_answer": "42",
        "competency_targeted": "Logical Reasoning",
        "difficulty": "EASY",
    },
    {
        "id": "apt-10",
        "category": "Logical Reasoning",
        "question_text": "If CAT is coded as 3120, how is DOG coded in the same pattern?",
        "options": ["4157", "4151", "4147", "3157"],
        "correct_answer": "4157",
        "competency_targeted": "Logical Reasoning",
        "difficulty": "EASY",
    },
    {
        "id": "apt-11",
        "category": "Percentage",
        "question_text": "30% of a number is 90. What is 50% of that same number?",
        "options": ["120", "150", "180", "200"],
        "correct_answer": "150",
        "competency_targeted": "Quantitative Reasoning",
        "difficulty": "EASY",
    },
    {
        "id": "apt-12",
        "category": "Time & Work",
        "question_text": "10 workers can build a wall in 8 days. How many workers are needed to build the same wall in 4 days?",
        "options": ["15", "20", "25", "16"],
        "correct_answer": "20",
        "competency_targeted": "Problem Solving",
        "difficulty": "EASY",
    },
    {
        "id": "apt-13",
        "category": "Speed, Time & Distance",
        "question_text": "A train 100 meters long passes a telegraph pole in 5 seconds. What is the speed of the train in km/h?",
        "options": ["72 km/h", "50 km/h", "60 km/h", "80 km/h"],
        "correct_answer": "72 km/h",
        "competency_targeted": "Problem Solving",
        "difficulty": "MEDIUM",
    },
    {
        "id": "apt-14",
        "category": "Profit & Loss",
        "question_text": "A watch sold for $270 results in a 10% loss. What was the original cost price?",
        "options": ["$300", "$290", "$310", "$280"],
        "correct_answer": "$300",
        "competency_targeted": "Quantitative Reasoning",
        "difficulty": "MEDIUM",
    },
    {
        "id": "apt-15",
        "category": "Ratios & Proportions",
        "question_text": "Divide $500 among A, B, and C in the ratio 2:3:5. How much does C receive?",
        "options": ["$150", "$250", "$200", "$300"],
        "correct_answer": "$250",
        "competency_targeted": "Quantitative Reasoning",
        "difficulty": "EASY",
    },
    {
        "id": "apt-16",
        "category": "Simple Interest",
        "question_text": "At what annual simple interest rate will a sum of money double itself in 10 years?",
        "options": ["5%", "10%", "8%", "12%"],
        "correct_answer": "10%",
        "competency_targeted": "Quantitative Reasoning",
        "difficulty": "EASY",
    },
    {
        "id": "apt-17",
        "category": "Probability",
        "question_text": "What is the probability of getting an even number when rolling a standard six-sided die?",
        "options": ["1/3", "1/2", "2/3", "1/6"],
        "correct_answer": "1/2",
        "competency_targeted": "Logical Reasoning",
        "difficulty": "EASY",
    },
    {
        "id": "apt-18",
        "category": "Logical Reasoning",
        "question_text": "If all Bloops are Razzies and all Razzies are Lazzies, are all Bloops definitely Lazzies?",
        "options": ["Yes", "No", "Cannot be determined", "Only on Tuesdays"],
        "correct_answer": "Yes",
        "competency_targeted": "Logical Reasoning",
        "difficulty": "EASY",
    },
    {
        "id": "apt-19",
        "category": "Averages",
        "question_text": "The mean of 4, 8, 12, 16, and X is 10. What is the value of X?",
        "options": ["8", "10", "12", "6"],
        "correct_answer": "10",
        "competency_targeted": "Quantitative Reasoning",
        "difficulty": "EASY",
    },
    {
        "id": "apt-20",
        "category": "Algebraic Reasoning",
        "question_text": "If 3x + 5 = 20, what is the value of 2x - 1?",
        "options": ["9", "10", "11", "8"],
        "correct_answer": "9",
        "competency_targeted": "Problem Solving",
        "difficulty": "EASY",
    },
]


def select_aptitude_questions(count: int = 5, session_seed: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Select `count` (default 5) randomized aptitude questions from the fixed 20-question bank.
    If session_seed is provided, the selection is deterministic for that specific session.
    """
    bank_copy = list(APTITUDE_20_BANK)
    if session_seed:
        rng = random.Random(session_seed)
        return rng.sample(bank_copy, min(count, len(bank_copy)))
    return random.sample(bank_copy, min(count, len(bank_copy)))
