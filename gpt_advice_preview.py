import openai
import os
import pandas as pd
import json
from datetime import datetime

def get_portfolio_csv(csv_path):
    df = pd.read_csv(csv_path)
    return df.to_string(index=False)

def get_latest_advice(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        advice_list = json.load(f)
    if not advice_list:
        return "No advice available."
    latest = max(advice_list, key=lambda x: x.get('timestamp', ''))
    return latest['advice']

def get_system_prompt(prompt_path, portfolio, recommendation):
    with open(prompt_path, 'r', encoding='utf-8') as f:
        prompt = f.read()
    prompt = prompt.replace('$portfolio$', portfolio)
    prompt = prompt.replace('$recommendation$', recommendation)
    return prompt

def get_gpt_response(prompt, openai_api_key):
    client = openai.OpenAI(api_key=openai_api_key)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": prompt}]
    )
    return response.choices[0].message.content

def main():
    csv_path = 'user_holdings_iammhk.csv'
    advice_path = 'global_advice.json'
    prompt_path = 'gpt_system_prompt.txt'
    openai_api_key = os.getenv('OPENAI_API_KEY')
    portfolio = get_portfolio_csv(csv_path)
    recommendation = get_latest_advice(advice_path)
    system_prompt = get_system_prompt(prompt_path, portfolio, recommendation)
    gpt_reply = get_gpt_response(system_prompt, openai_api_key)
    print(gpt_reply)

if __name__ == '__main__':
    main()
