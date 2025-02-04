# -*- coding: utf-8 -*-
from zhipuai import ZhipuAI
import sys

if __name__ == '__main__':
    question = sys.argv[1]
    client = ZhipuAI(api_key="316b438ba6efe02778b874ed5d5f0a52.Yjj8ybeYhidJe8ja")  # Please fill in your own APIKey
    response = client.chat.completions.create(
        model="glm-4-flash",  # Please fill in the model name you want to call
        messages=[
            {"role": "system", "content": '''
            你是一位专业的程序员, 
            你有一位新来的同事向你请教编程问题,
            出于效率考虑, 你需要尽量简洁地回答,
            同时给出正确代码示例。
            注意, 你必须用中文回答问题.
                '''},
            {"role": "user", "content": question},
        ],
    )
    print(response.choices[0].message.content)